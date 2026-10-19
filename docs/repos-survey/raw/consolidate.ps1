# Lane R: consolidate raw search JSON -> candidate pool (stars>100, active in last 3y)
$rawDir = $PSScriptRoot
$cut = [datetime]::Parse("2023-10-14T00:00:00Z").ToUniversalTime()
$all = @{}
Get-ChildItem $rawDir -Filter "*.json" | ForEach-Object {
  try { $j = Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return }
  if (-not $j.items) { return }
  foreach ($it in $j.items) {
    if (-not $it.full_name) { continue }
    $key = $it.full_name
    if ($all.ContainsKey($key)) {
      if ($it.stargazers_count -gt $all[$key].stars) { $all[$key].stars = $it.stargazers_count }
      $all[$key].queries += $_.BaseName
    } else {
      $all[$key] = [pscustomobject]@{
        full_name = $it.full_name
        url = $it.html_url
        stars = $it.stargazers_count
        language = $it.language
        license_spdx = $(if ($it.license) { $it.license.spdx_id } else { $null })
        license_name = $(if ($it.license) { $it.license.name } else { $null })
        default_branch = $it.default_branch
        created_at = $it.created_at
        pushed_at = $it.pushed_at
        topics = @($it.topics)
        description = $it.description
        archived = $it.archived
        forks = $it.forks_count
        queries = @($_.BaseName)
      }
    }
  }
}
$list = $all.Values | Sort-Object -Property stars -Descending
$active = $list | Where-Object { $_.pushed_at -and ([datetime]::Parse($_.pushed_at).ToUniversalTime() -ge $cut) }
$ge100 = $active | Where-Object { $_.stars -gt 100 }
Write-Output "unique_total=$($list.Count) active3y=$($active.Count) stars_gt100_and_active=$($ge100.Count)"
$ge100 | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $rawDir "_candidates.json") -Encoding UTF8
$ge100 | Select-Object full_name, stars, language, pushed_at, created_at, archived, license_spdx, description |
  Export-Csv (Join-Path $rawDir "_candidates.csv") -NoTypeInformation -Encoding UTF8
Write-Output "written _candidates.json / _candidates.csv"
