# AWS CLI Installation for Windows

## Quick Install (Recommended)

### Option 1: MSI Installer
1. Download the AWS CLI MSI installer:
   - **64-bit Windows**: https://awscli.amazonaws.com/AWSCLIV2.msi
   - The installer auto-detects your system architecture

2. Run the downloaded `.msi` file

3. Follow the installation wizard (default settings are fine)

4. **Restart your PowerShell/Command Prompt** after installation

5. Verify installation:
   ```powershell
   aws --version
   ```
   You should see: `aws-cli/2.x.x Python/3.x.x ...`

### Option 2: Using pip (if you have Python installed)
```powershell
pip install awscli
```

## Using the Download Script

1. Open PowerShell in the project directory

2. Run the script:
   ```powershell
   .\download-s3-dataset.ps1
   ```

3. To specify a custom output directory:
   ```powershell
   .\download-s3-dataset.ps1 -OutputDir "C:\MyDataset"
   ```

## Troubleshooting

**"aws is not recognized" error:**
- Restart your PowerShell/Command Prompt
- Check if AWS CLI is in your PATH: `$env:PATH`
- Reinstall AWS CLI if needed

**Download is slow:**
- This is normal for large datasets
- The script will resume if interrupted (run it again)
- Consider downloading specific prefixes instead of the entire bucket

**Permission errors:**
- Run PowerShell as Administrator if needed
- Check that the output directory is writable

## Auto-Start on Boot (Download Once)

The dataset can be configured to download automatically once when your system boots.

### Setup Auto-Download

1. **Run the setup script:**
   ```powershell
   .\setup-auto-download-task.ps1
   ```

2. **The script will:**
   - Create a Windows Task Scheduler task
   - Configure it to run on system startup (with 2 minute delay for network)
   - Run the download script automatically
   - Skip download if dataset already exists

3. **On next boot:**
   - The task will run automatically
   - Dataset will download to `./s3_dataset/`
   - Progress will be logged to `./logs/s3-download-YYYY-MM-DD.log`

### Manual Testing

Test the scheduled task without rebooting:
```powershell
Start-ScheduledTask -TaskName "S3DatasetDownloadOnBoot"
```

Check the log file:
```powershell
Get-Content .\logs\s3-download-*.log -Tail 20
```

### Disable Auto-Download

To remove the auto-download task:
```powershell
.\setup-auto-download-task.ps1 -Remove
```

Or manually via Task Scheduler:
1. Open Task Scheduler
2. Find task: `S3DatasetDownloadOnBoot`
3. Right-click → Delete

### How It Works

1. **On System Boot:**
   - Windows Task Scheduler triggers the task
   - Waits 2 minutes for network to be ready
   - Runs `startup-download-dataset.ps1`

2. **Startup Script:**
   - Checks if dataset already exists
   - If exists, skips download (runs only once)
   - If not, runs `download-s3-dataset.ps1`
   - Logs all output to log file

3. **Download Script:**
   - Downloads entire S3 bucket
   - Creates flag file when complete
   - Skips on subsequent runs (unless `-Force` is used)

### Troubleshooting Auto-Start

**Task doesn't run on boot:**
- Check Task Scheduler: `taskschd.msc`
- Verify task is enabled
- Check task history for errors
- Ensure network is available (task requires network)

**Download doesn't start:**
- Check log file: `.\logs\s3-download-*.log`
- Verify AWS CLI is installed
- Check network connectivity
- Run script manually to test: `.\startup-download-dataset.ps1`

**Task runs but download fails:**
- Check AWS CLI installation
- Verify S3 bucket is accessible
- Check disk space
- Review log file for specific errors

**Want to re-download:**
- Delete the dataset folder: `Remove-Item -Recurse -Force .\s3_dataset`
- Or use force flag: `.\download-s3-dataset.ps1 -Force`

