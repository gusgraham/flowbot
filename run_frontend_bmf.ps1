$ErrorActionPreference = "Stop"

# Navigate to frontend and run simple web server
Set-Location "$PSScriptRoot\frontend"
Write-Host "Starting Frontend..." -ForegroundColor Cyan
npm run dev -- --port 5173 --host
