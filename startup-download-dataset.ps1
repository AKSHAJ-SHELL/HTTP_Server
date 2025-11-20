# Startup wrapper for S3 dataset download
# This script runs on system boot to download the dataset once
# It logs to a file and runs silently in the background

$ErrorActionPreference = "SilentlyContinue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Log file location
$logDir = Join-Path $scriptPath "logs"
$logFile = Join-Path $logDir "s3-download-$(Get-Date -Format 'yyyy-MM-dd').log"

# Create logs directory if it doesn't exist
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Function to write to log file
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logFile -Value $logMessage
}

# Wait for network to be ready (30 seconds delay)
Write-Log "Startup download script started. Waiting for network..."
Start-Sleep -Seconds 30

# Check if dataset already exists
$outputDir = Join-Path $scriptPath "s3_dataset"
$datasetExists = (Test-Path $outputDir) -and (Get-ChildItem -Path $outputDir -Recurse -File -ErrorAction SilentlyContinue).Count -gt 0

if ($datasetExists) {
    Write-Log "Dataset already exists. Skipping download." "INFO"
    exit 0
}

Write-Log "Starting dataset download..." "INFO"

# Run the download script and capture output
try {
    $downloadScript = Join-Path $scriptPath "download-s3-dataset.ps1"
    
    # Run script and redirect output to log
    $output = & powershell.exe -ExecutionPolicy Bypass -File $downloadScript -OutputDir $outputDir 2>&1
    
    # Write output to log
    foreach ($line in $output) {
        Write-Log $line "DOWNLOAD"
    }
    
    # Check if download was successful
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Dataset download completed successfully" "SUCCESS"
    } else {
        Write-Log "Dataset download failed with exit code: $LASTEXITCODE" "ERROR"
    }
} catch {
    Write-Log "Error running download script: $($_.Exception.Message)" "ERROR"
    exit 1
}

