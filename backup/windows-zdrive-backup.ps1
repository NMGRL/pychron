param(
    [string]$SourceRoot = "",
    [string]$DestinationRoot = "Z:\Pychron_backup",
    [string[]]$Folders = @("setupfiles", "scripts", "data", ".appdata", "experiments", "preferences", "queue_conditionals")
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $SourceRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}

if (-not (Test-Path -Path $DestinationRoot)) {
    New-Item -ItemType Directory -Path $DestinationRoot | Out-Null
}

foreach ($folder in $Folders) {
    $src = Join-Path $SourceRoot $folder
    if (-not (Test-Path -Path $src)) {
        Write-Host "Skipping missing folder: $src"
        continue
    }

    $dst = Join-Path $DestinationRoot $folder
    if (-not (Test-Path -Path $dst)) {
        New-Item -ItemType Directory -Path $dst | Out-Null
    }

    robocopy $src $dst /E /COPY:DAT /DCOPY:DAT /R:2 /W:5
    if ($LASTEXITCODE -ge 8) {
        throw "Robocopy failed for $src (exit code $LASTEXITCODE)"
    }
}

Write-Host "Backup complete to: $DestinationRoot"
