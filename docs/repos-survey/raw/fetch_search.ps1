# Lane R: fetch GitHub repo search results through proxy, cache raw JSON to disk.
param(
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][string]$Q,
  [string]$Sort = "stars",
  [string]$Order = "desc",
  [int]$PerPage = 100
)
$ErrorActionPreference = "Stop"
$rawDir = Join-Path $PSScriptRoot ""
$out = Join-Path $rawDir "$Tag.json"
if (Test-Path $out) { Write-Output "$Tag CACHED"; exit 0 }
$h = @{ "User-Agent" = "lane-r-research"; "Accept" = "application/vnd.github+json" }
$enc = [uri]::EscapeDataString($Q)
$url = "https://gh-proxy.com/https://api.github.com/search/repositories?q=$enc&sort=$Sort&order=$Order&per_page=$PerPage"
$ok = $false
foreach ($try in 1..3) {
  try {
    $r = Invoke-RestMethod -Uri $url -Headers $h -TimeoutSec 90
    $r | ConvertTo-Json -Depth 8 | Set-Content -Path $out -Encoding UTF8
    Write-Output "$Tag OK total=$($r.total_count) got=$($r.items.Count)"
    $ok = $true
    break
  } catch {
    Write-Output "$Tag TRY$try ERR $($_.Exception.Message)"
    Start-Sleep -Seconds 5
  }
}
if (-not $ok) { Write-Output "$Tag FAILED" ; exit 1 }
