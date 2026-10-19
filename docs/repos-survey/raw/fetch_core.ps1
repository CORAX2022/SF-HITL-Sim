# Lane R: verify specific repos via core API (no cloning), cache each to raw/core/
param([string]$ListFile)
$ErrorActionPreference = "Continue"
$dir = Join-Path $PSScriptRoot "core"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$h = @{ "User-Agent" = "lane-r-research"; "Accept" = "application/vnd.github+json" }
$names = Get-Content $ListFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" -and -not $_.StartsWith("#") }
$out = @()
foreach ($n in $names) {
  $n = $n.Trim()
  $safe = $n -replace "[/\\]", "__"
  $f = Join-Path $dir "$safe.json"
  if (-not (Test-Path $f)) {
    $url = "https://gh-proxy.com/https://api.github.com/repos/$n"
    try {
      $r = Invoke-RestMethod -Uri $url -Headers $h -TimeoutSec 60
      $r | ConvertTo-Json -Depth 6 | Set-Content -Path $f -Encoding UTF8
      Start-Sleep -Milliseconds 250
    } catch {
      Set-Content -Path $f -Value "{`"__error`":`"$($_.Exception.Message -replace '"','')`"}" -Encoding UTF8
    }
  }
  try { $j = Get-Content $f -Raw -Encoding UTF8 | ConvertFrom-Json } catch { continue }
  if ($j.__error) { Write-Output "MISS $n" ; continue }
  $lic = if ($j.license) { $j.license.spdx_id } else { "null" }
  Write-Output ("OK   {0} | {1} | {2} | {3} | {4} | {5}" -f $j.full_name, $j.stargazers_count, $j.language, $lic, $j.pushed_at, $j.created_at)
}
