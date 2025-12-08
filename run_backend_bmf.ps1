$ErrorActionPreference = "Stop"

# Activate root virtual environment
$VenvPath = "$PSScriptRoot\.venv\Scripts\Activate.ps1"
if (Test-Path $VenvPath) {
    Write-Host "Activating virtual environment at $VenvPath" -ForegroundColor Green
    . $VenvPath
}
else {
    Write-Error "Virtual environment not found at $VenvPath"
}

# Navigate to backend and run uvicorn
Set-Location "$PSScriptRoot\backend"
Write-Host "Starting Uvicorn..." -ForegroundColor Cyan
uvicorn main:app --reload --port 8001
