# Lane R: fetch GitHub repo search results (direct API), cache raw JSON to disk.
param(
  [Parameter(Mandatory=$true)][string]$Tag,
  [Parameter(Mandatory=$true)][string]$Q,
  [string]$Sort = "stars",
  [string]$Order = "desc",
  [int]$PerPage = 100,
  [string]$Base = "https://api.github.com"
)
$out = Join-Path $PSScriptRoot "$Tag.json"
if (Test-Path $out) { Write-Output "$Tag CACHED"; exit 0 }
$h = @{ "User-Agent" = "lane-r-research"; "Accept" = "application/vnd.github+json" }
$enc = [uri]::EscapeDataString($Q)
$url = "$Base/search/repositories?q=$enc&sort=$Sort&order=$Order&per_page=$PerPage"
$ok = $false
foreach ($try in 1..4) {
  try {
    $r = Invoke-RestMethod -Uri $url -Headers $h -TimeoutSec 90
    $r | ConvertTo-Json -Depth 8 | Set-Content -Path $out -Encoding UTF8
    Write-Output "$Tag OK total=$($r.total_count) got=$($r.items.Count)"
    $ok = $true
    break
  } catch {
    $msg = $_.Exception.Message
    Write-Output "$Tag TRY$try ERR $msg"
    if ($msg -match "403|429|rate limit") { Start-Sleep -Seconds 20 } else { Start-Sleep -Seconds 5 }
  }
}
if (-not $ok) { Write-Output "$Tag FAILED"; exit 1 }
