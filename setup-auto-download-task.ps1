# Setup Windows Task Scheduler to run dataset download on boot
# This script creates a scheduled task that runs the download script on system startup

param(
    [switch]$Remove  # Use this flag to remove the task instead of creating it
)

$ErrorActionPreference = "Stop"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "Error: Administrator Privileges Required" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "This script requires Administrator privileges to create scheduled tasks." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator:" -ForegroundColor Cyan
    Write-Host "1. Right-click PowerShell in Start Menu" -ForegroundColor White
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "3. Navigate to this directory:" -ForegroundColor White
    Write-Host "   cd `"$PWD`"" -ForegroundColor Gray
    Write-Host "4. Run the script again:" -ForegroundColor White
    Write-Host "   .\setup-auto-download-task.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupScript = Join-Path $scriptPath "startup-download-dataset.ps1"
$taskName = "S3DatasetDownloadOnBoot"

if ($Remove) {
    Write-Host "Removing scheduled task: $taskName" -ForegroundColor Yellow
    
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "Task removed successfully!" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -like "*cannot be found*") {
            Write-Host "Task does not exist. Nothing to remove." -ForegroundColor Yellow
        } else {
            Write-Host "Error removing task: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    exit 0
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setting up Auto-Download Task" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if startup script exists
if (-not (Test-Path $startupScript)) {
    Write-Host "Error: Startup script not found: $startupScript" -ForegroundColor Red
    exit 1
}

Write-Host "Startup script: $startupScript" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "Old task removed successfully." -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not remove existing task: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Attempting to continue anyway..." -ForegroundColor Yellow
        Write-Host ""
    }
}

# Create the action (what to run)
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startupScript`""

# Create the trigger (when to run - on system startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Set delay to ensure network is ready (2 minutes after boot)
$trigger.Delay = "PT2M"

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
    -RestartCount 0

# Create the principal (run as current user)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Downloads S3 dataset once on system boot" | Out-Null
    
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Name: $taskName" -ForegroundColor Cyan
    Write-Host "Trigger: At system startup (with 2 minute delay)" -ForegroundColor Cyan
    Write-Host "Script: $startupScript" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The dataset will download automatically on next boot." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To remove this task, run:" -ForegroundColor Gray
    Write-Host "  .\setup-auto-download-task.ps1 -Remove" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test the task manually:" -ForegroundColor Gray
    Write-Host "  Start-ScheduledTask -TaskName `"$taskName`"" -ForegroundColor Gray
    
} catch {
    Write-Host "Error creating task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to run PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}

