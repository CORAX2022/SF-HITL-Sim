# 用 NetLogo 7.0.4 的 headless API 跑 BehaviorSpace 实验。
#
# 为什么不直接用 netlogo-headless.bat：
#   该 .bat 用 FOR %%a IN (%*) 逐词展开参数，遇到含空格的路径
#   （如 F:\城规工作室\CJ 李昊\...）会被拆成多个词，导致
#   "找不到或无法加载主类"。这里直接调用 org.nlogo.headless.Main，
#   由 PowerShell 正确引用每个参数，绕开该缺陷。
#
# 另注意：.bat 优先使用 JAVA_HOME/PATH 上的 java，
# 而本机 PATH 上是 Java 8，NetLogo 7 需要 Java 17+，
# 故这里强制使用 NetLogo 自带的 runtime\bin\java.exe。

param(
  [Parameter(Mandatory = $true)][string]$Model,
  [string]$Experiment = "",
  [string]$Table = "",
  [string]$Spreadsheet = "",
  [string]$Command = "",
  [string]$NetLogoHome = "D:\NetLogo"
)

$ErrorActionPreference = "Stop"

$java = Join-Path $NetLogoHome "runtime\bin\java.exe"
if (-not (Test-Path $java)) {
  throw "未找到 NetLogo 自带 Java: $java"
}

$jar = Get-ChildItem (Join-Path $NetLogoHome "app") -Filter "netlogo-*.jar" |
       Where-Object { $_.Name -notmatch "3d|console" } |
       Select-Object -First 1
if (-not $jar) { throw "未找到 netlogo jar（$NetLogoHome\app）" }

# -Dfile.encoding=UTF-8 保证中文路径与中文注释正常
$jvmOpts = @(
  "-XX:MaxRAMPercentage=50"
  "-Dfile.encoding=UTF-8"
  "-Dnetlogo.docs.dir=$NetLogoHome"
  "-Dnetlogo.models.dir=$NetLogoHome\models"
  "-Dnetlogo.extensions.dir=$NetLogoHome\extensions"
  "--add-exports=java.base/java.lang=ALL-UNNAMED"
  "--add-exports=java.desktop/sun.awt=ALL-UNNAMED"
  "--add-exports=java.desktop/sun.java2d=ALL-UNNAMED"
)

# 输出目录必须存在
if ($Table) {
  $tableDir = Split-Path -Parent $Table
  if ($tableDir -and -not (Test-Path $tableDir)) {
    New-Item -ItemType Directory -Path $tableDir -Force | Out-Null
  }
  if (Test-Path $Table) { Remove-Item $Table -Force }
}

# 三选一：--command（跑一条命令）/ --experiment（跑 BehaviorSpace 实验）
$nlArgs = @("--model", $Model)
if ($Command) {
  $nlArgs += @("--command", $Command)
} else {
  if (-not $Experiment) { throw "需要 -Experiment 或 -Command 之一" }
  $nlArgs += @("--experiment", $Experiment)
  if ($Table) { $nlArgs += @("--table", $Table) }
  if ($Spreadsheet) { $nlArgs += @("--spreadsheet", $Spreadsheet) }
}

$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $java @jvmOpts -classpath $jar.FullName org.nlogo.headless.Main @nlArgs
$code = $LASTEXITCODE
$sw.Stop()

Write-Host ("[run-nlogo] exit={0} elapsed={1:N1}s -> {2}" -f $code, $sw.Elapsed.TotalSeconds, $Table)
if (Test-Path $Table) {
  Write-Host ("[run-nlogo] 输出 {0:N0} bytes" -f (Get-Item $Table).Length)
}
exit $code
