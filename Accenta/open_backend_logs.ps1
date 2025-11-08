# PowerShell script to open backend logs in a new window
# Usage: .\open_backend_logs.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendLogPath = Join-Path $scriptDir "backend\logs\backend.log"

Write-Host "Opening backend logs window..." -ForegroundColor Green
Write-Host "Log file: $backendLogPath" -ForegroundColor Gray

# Check if log file exists
if (Test-Path $backendLogPath) {
    # Open a new PowerShell window that tails the log file
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\backend'; Write-Host 'Backend Logs - Press Ctrl+C to stop' -ForegroundColor Cyan; Write-Host 'Log file: $backendLogPath' -ForegroundColor Gray; Write-Host ''; Get-Content '$backendLogPath' -Wait -Tail 50"
} else {
    # If log file doesn't exist, open a window in the backend directory
    Write-Host "Log file not found yet. Opening backend directory..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\backend'; Write-Host 'Backend Directory' -ForegroundColor Cyan; Write-Host 'Log file will be created at: logs\backend.log' -ForegroundColor Gray; Write-Host 'To view logs, run: Get-Content logs\backend.log -Wait -Tail 50' -ForegroundColor Yellow; Write-Host ''"
}

