# Download entire S3 bucket dataset
# Usage: .\download-s3-dataset.ps1 [output_directory] [-Force]

param(
    [string]$OutputDir = "./s3_dataset",
    [switch]$Force
)

$BucketName = "rgb-ir-dataset"
$Region = "us-east-2"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "S3 Dataset Download Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Bucket: s3://$BucketName"
Write-Host "Region: $Region"
Write-Host "Output Directory: $OutputDir"
Write-Host "==========================================" -ForegroundColor Cyan

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not found"
    }
    Write-Host "Found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: AWS CLI is not installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install AWS CLI:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://awscli.amazonaws.com/AWSCLIV2.msi" -ForegroundColor Yellow
    Write-Host "2. Or install via pip: pip install awscli" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Check if dataset already exists
$flagFile = Join-Path $OutputDir ".download_complete"
$datasetExists = (Test-Path $OutputDir) -and (Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue).Count -gt 0

if ($datasetExists -and -not $Force) {
    Write-Host "Dataset already exists in: $OutputDir" -ForegroundColor Yellow
    Write-Host "Skipping download. Use -Force to re-download." -ForegroundColor Yellow
    Write-Host ""
    
    # Show existing dataset info
    $fileCount = (Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue).Count
    $totalSize = (Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "Existing files: $fileCount" -ForegroundColor Cyan
    Write-Host "Total size: $([math]::Round($totalSize, 2)) GB" -ForegroundColor Cyan
    exit 0
}

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "Created output directory: $OutputDir" -ForegroundColor Green
}

Write-Host "Starting download..." -ForegroundColor Yellow
Write-Host "This may take a while depending on the dataset size..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel" -ForegroundColor Gray
Write-Host ""

# Download entire bucket
# --no-sign-request: Use for public buckets (no AWS credentials needed)
# --region: Specify the region
# sync: Syncs files (only downloads new/changed files on subsequent runs)
try {
    aws s3 sync "s3://$BucketName/" "$OutputDir/" `
        --no-sign-request `
        --region $Region `
        --exclude "*.DS_Store" `
        --exclude "*.git*" `
        --exclude "Thumbs.db"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host "Download complete!" -ForegroundColor Green
        Write-Host "Files saved to: $OutputDir" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
        
        # Count downloaded files
        $fileCount = (Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue).Count
        $totalSize = (Get-ChildItem -Path $OutputDir -Recurse -File -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum).Sum / 1GB
        
        Write-Host "Total files downloaded: $fileCount" -ForegroundColor Green
        Write-Host "Total size: $([math]::Round($totalSize, 2)) GB" -ForegroundColor Green
        
        # Create flag file to mark download as complete
        $flagFile = Join-Path $OutputDir ".download_complete"
        Set-Content -Path $flagFile -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        Write-Host "Download flag created: $flagFile" -ForegroundColor Gray
    } else {
        Write-Host "Error: Download failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

