param(
    [string]$MySqlExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    [string]$DefaultsFile = "C:\secure\mysql-backup.cnf",
    [string]$Database = "your_database",
    [Alias("RootBackupDirectory")]
    [string]$BackupRoot = $env:MYSQL_BACKUP_ROOT,
    [ValidateSet("daily", "weekly", "monthly", "yearly", "all")]
    [string]$Rotation = "daily",
    [string]$BackupZip = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = "D:\MySQLBackups"
}

function Get-NewestZip([string]$Root, [string]$SelectedRotation) {
    $searchDirs = @()

    if ($SelectedRotation -eq "all") {
        $searchDirs = @(
            (Join-Path $Root "daily"),
            (Join-Path $Root "weekly"),
            (Join-Path $Root "monthly"),
            (Join-Path $Root "yearly")
        )
    } else {
        $searchDirs = @((Join-Path $Root $SelectedRotation))
    }

    $existingDirs = $searchDirs | Where-Object { Test-Path -Path $_ }
    if (-not $existingDirs) {
        throw "No backup directories found under $Root for rotation '$SelectedRotation'."
    }

    $newest = Get-ChildItem -Path $existingDirs -Filter "*.zip" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $newest) {
        throw "No backup zip files found for rotation '$SelectedRotation'."
    }

    return $newest.FullName
}

if ([string]::IsNullOrWhiteSpace($BackupZip)) {
    $BackupZip = Get-NewestZip -Root $BackupRoot -SelectedRotation $Rotation
}

if (-not (Test-Path -Path $BackupZip)) {
    throw "Backup zip not found: $BackupZip"
}

$extractDir = Join-Path $env:TEMP ("mysql_restore_" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $extractDir | Out-Null

try {
    Expand-Archive -Path $BackupZip -DestinationPath $extractDir -Force
    $sqlFile = Get-ChildItem -Path $extractDir -Filter "*.sql" -File | Select-Object -First 1

    if (-not $sqlFile) {
        throw "No .sql file found in archive: $BackupZip"
    }

    $cmd = '"' + $MySqlExe + '" --defaults-extra-file="' + $DefaultsFile + '" "' + $Database + '" < "' + $sqlFile.FullName + '"'
    cmd.exe /c $cmd | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "mysql restore failed with exit code $LASTEXITCODE"
    }

    Write-Host "Restore complete from: $BackupZip"
} finally {
    if (Test-Path -Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
}
