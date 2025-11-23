# Image Server Startup Script
# This script ensures Docker containers are running on system startup

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting Image Server..." -ForegroundColor Green

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Docker is not installed or not in PATH" -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Docker is not installed or not accessible" -ForegroundColor Red
    exit 1
}

# Check if Docker daemon is running
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Yellow
        Write-Host "Attempting to start Docker Desktop..." -ForegroundColor Yellow
        
        # Try to start Docker Desktop (if installed in default location)
        $dockerDesktopPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerDesktopPath) {
            Start-Process $dockerDesktopPath
            Write-Host "Waiting for Docker Desktop to start (30 seconds)..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30
            
            # Check again
            docker ps > $null 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Error: Docker Desktop did not start in time. Please start it manually." -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "Error: Docker Desktop not found. Please start Docker Desktop manually." -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "Docker daemon is running" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Could not connect to Docker daemon" -ForegroundColor Red
    exit 1
}

# Start the containers
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
try {
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Image Server started successfully!" -ForegroundColor Green
        Write-Host "Server is available at: http://localhost:8000" -ForegroundColor Green
        Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
        
        # Show container status
        Write-Host "`nContainer Status:" -ForegroundColor Cyan
        docker-compose ps
    } else {
        Write-Host "Error: Failed to start containers" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Failed to start containers - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

