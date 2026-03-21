param(
    [string]$MySqlDumpExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
    [string]$DefaultsFile = "C:\secure\mysql-backup.cnf",
    [string]$Database = "your_database",
    [Alias("RootBackupDirectory")]
    [string]$BackupRoot = $env:MYSQL_BACKUP_ROOT,
    [int]$KeepDaily = 14,
    [int]$KeepWeekly = 8,
    [int]$KeepMonthly = 24,
    [int]$KeepYearly = 10
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = "D:\MySQLBackups"
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path -Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Trim-Rotation([string]$Path, [int]$Keep) {
    if (-not (Test-Path -Path $Path)) {
        return
    }

    $files = Get-ChildItem -Path $Path -File | Sort-Object LastWriteTime -Descending
    $files | Select-Object -Skip $Keep | Remove-Item -Force
}

$dailyPath = Join-Path $BackupRoot "daily"
$weeklyPath = Join-Path $BackupRoot "weekly"
$monthlyPath = Join-Path $BackupRoot "monthly"
$yearlyPath = Join-Path $BackupRoot "yearly"

Ensure-Dir $dailyPath
Ensure-Dir $weeklyPath
Ensure-Dir $monthlyPath
Ensure-Dir $yearlyPath

$now = Get-Date
$stamp = $now.ToString("yyyy-MM-dd_HHmmss")
$sqlFile = Join-Path $env:TEMP "$Database-$stamp.sql"
$zipName = "$Database-$stamp.zip"
$dailyZip = Join-Path $dailyPath $zipName

& $MySqlDumpExe "--defaults-extra-file=$DefaultsFile" "--single-transaction" "--routines" "--triggers" "--events" $Database "--result-file=$sqlFile"
if ($LASTEXITCODE -ne 0) {
    throw "mysqldump failed with exit code $LASTEXITCODE"
}

Compress-Archive -Path $sqlFile -DestinationPath $dailyZip -CompressionLevel Optimal -Force
Remove-Item -Path $sqlFile -Force

if ($now.DayOfWeek -eq [System.DayOfWeek]::Sunday) {
    Copy-Item -Path $dailyZip -Destination (Join-Path $weeklyPath $zipName) -Force
}

if ($now.Day -eq 1) {
    Copy-Item -Path $dailyZip -Destination (Join-Path $monthlyPath $zipName) -Force
}

if ($now.Month -eq 1 -and $now.Day -eq 1) {
    Copy-Item -Path $dailyZip -Destination (Join-Path $yearlyPath $zipName) -Force
}

Trim-Rotation -Path $dailyPath -Keep $KeepDaily
Trim-Rotation -Path $weeklyPath -Keep $KeepWeekly
Trim-Rotation -Path $monthlyPath -Keep $KeepMonthly
Trim-Rotation -Path $yearlyPath -Keep $KeepYearly

Write-Host "Backup complete: $dailyZip"
