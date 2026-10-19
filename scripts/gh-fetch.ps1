<#
.SYNOPSIS
  Fetch a GitHub repository as a zip archive through the gh-proxy.com mirror.

.DESCRIPTION
  github.com and api.github.com are DNS-blackholed to 127.0.0.1 on this machine
  (resolver-level, not the hosts file). Direct git clone therefore fails, and
  git-over-proxy also fails because the mirror demands credentials.
  Working path: GitHub REST API and codeload archives proxied through
  https://gh-proxy.com/https://<target>.

  Downloads the default-branch archive, verifies zip integrity, extracts it to a
  staging directory, and records provenance (repo, stars, default branch, license)
  into a manifest JSON line.

.PARAMETER Repo
  owner/name, e.g. mesa/mesa

.PARAMETER DestDir
  Directory that will contain the extracted repository tree.

.PARAMETER Force
  Re-download even if the destination already exists.

.EXAMPLE
  ./gh-fetch.ps1 -Repo mesa/mesa -DestDir "F:\proj\deploy\repos"
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Repo,
  [Parameter(Mandatory = $true)][string]$DestDir,
  [string]$Proxy = "https://gh-proxy.com",
  [switch]$Force,
  [int]$TimeoutSec = 600
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step($msg) { Write-Host "[gh-fetch] $msg" }

if ($Repo -notmatch '^[^/]+/[^/]+$') { throw "Repo must be 'owner/name', got '$Repo'" }

$owner, $name = $Repo.Split('/', 2)
$targetDir = Join-Path $DestDir "$name"
$manifestPath = Join-Path $DestDir "manifest.jsonl"

if ((Test-Path (Join-Path $targetDir ".fetch-ok")) -and -not $Force) {
  Write-Step "SKIP $Repo (already fetched at $targetDir)"
  exit 0
}

New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
$work = Join-Path ([System.IO.Path]::GetTempPath()) ("ghfetch_" + [guid]::NewGuid().ToString("N").Substring(0, 12))
New-Item -ItemType Directory -Force -Path $work | Out-Null

try {
  # ---- 1. Metadata (also validates that the repo exists) -------------------
  $apiUrl = "$Proxy/https://api.github.com/repos/$Repo"
  Write-Step "metadata: $apiUrl"
  $metaRaw = curl.exe -sL --max-time 60 $apiUrl
  if (-not $metaRaw) { throw "empty metadata response for $Repo" }
  $meta = $metaRaw | ConvertFrom-Json
  if ($meta.message) { throw "GitHub API error for ${Repo}: $($meta.message)" }

  $branch = $meta.default_branch
  if (-not $branch) { $branch = "main" }
  Write-Step ("{0}  stars={1}  lang={2}  branch={3}" -f $meta.full_name, $meta.stargazers_count, $meta.language, $branch)

  # ---- 2. Archive download -------------------------------------------------
  $zipPath = Join-Path $work "$name.zip"
  $zipUrl = "$Proxy/https://github.com/$Repo/archive/refs/heads/$branch.zip"
  Write-Step "archive: $zipUrl"
  $code = curl.exe -sL --max-time $TimeoutSec -o $zipPath -w "%{http_code}" $zipUrl
  if ($code -ne "200") { throw "archive download failed (HTTP $code) for $zipUrl" }
  $zipLen = (Get-Item $zipPath).Length
  if ($zipLen -lt 512) { throw "archive suspiciously small ($zipLen bytes) for $Repo" }
  Write-Step ("downloaded {0:N1} MB" -f ($zipLen / 1MB))

  # ---- 3. Integrity check --------------------------------------------------
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  try {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
  } catch { throw "corrupt zip for ${Repo}: $($_.Exception.Message)" }

  $entryCount = $zip.Entries.Count
  $sha = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash
  $zip.Dispose()
  Write-Step "zip OK: $entryCount entries, sha256=$($sha.Substring(0,16))..."

  # ---- 4. Extract ----------------------------------------------------------
  $stage = Join-Path $work "stage"
  Expand-Archive -Path $zipPath -DestinationPath $stage -Force
  # GitHub archives wrap everything in one top-level folder
  $inner = Get-ChildItem -Path $stage -Directory | Select-Object -First 1
  if (-not $inner) { throw "archive for $Repo contained no top-level directory" }

  if (Test-Path $targetDir) { Remove-Item $targetDir -Recurse -Force }
  Move-Item -Path $inner.FullName -Destination $targetDir
  Set-Content -Path (Join-Path $targetDir ".fetch-ok") -Value $sha -NoNewline

  # ---- 5. Provenance manifest ---------------------------------------------
  $record = [ordered]@{
    repo           = $meta.full_name
    stars          = $meta.stargazers_count
    language       = $meta.language
    default_branch = $branch
    license        = if ($meta.license) { $meta.license.spdx_id } else { $null }
    archived       = $meta.archived
    pushed_at      = $meta.pushed_at
    html_url       = $meta.html_url
    description    = $meta.description
    zip_sha256     = $sha
    zip_entries    = $entryCount
    fetched_at     = (Get-Date).ToString("o")
    local_path     = $targetDir
  }
  ($record | ConvertTo-Json -Compress) | Add-Content -Path $manifestPath -Encoding UTF8

  Write-Step "OK $Repo -> $targetDir"
}
finally {
  if (Test-Path $work) { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
}
