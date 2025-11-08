# Open a PowerShell window for backend operations
# Usage: .\open_backend_window.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"

Write-Host "Opening backend PowerShell window..." -ForegroundColor Green

# Open a new PowerShell window in the backend directory
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; Write-Host '=== BACKEND POWERSHELL ===' -ForegroundColor Cyan; Write-Host 'Directory: $backendDir' -ForegroundColor Gray; Write-Host ''; Write-Host 'Useful commands:' -ForegroundColor Yellow; Write-Host '  - View logs: Get-Content logs\backend.log -Wait -Tail 50' -ForegroundColor White; Write-Host '  - View last 100 lines: Get-Content logs\backend.log -Tail 100' -ForegroundColor White; Write-Host '  - Start backend: ..\start_backend.ps1' -ForegroundColor White; Write-Host ''; if (Test-Path 'logs\backend.log') { Write-Host 'Last 20 lines of log:' -ForegroundColor Green; Write-Host ''; Get-Content 'logs\backend.log' -Tail 20 } else { Write-Host 'Log file not found yet.' -ForegroundColor Yellow }; Write-Host ''; Write-Host 'Ready for commands...' -ForegroundColor Green"

