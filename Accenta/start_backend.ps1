# Start Accenta Backend Server
# Usage: .\start_backend.ps1

$ErrorActionPreference = "Stop"

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "🚀 Starting Accenta Backend..." -ForegroundColor Green
Write-Host ""

# Check if venv exists
$venvPath = Join-Path $scriptDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
    pip install -r backend\requirements.txt
} else {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
    & "$venvPath\Scripts\Activate.ps1"
}

# Check if uvicorn is installed
try {
    uvicorn --version | Out-Null
} catch {
    Write-Host "Installing uvicorn..." -ForegroundColor Yellow
    pip install uvicorn
}

Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Set-Location backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

