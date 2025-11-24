Set-Location "$PSScriptRoot\backend"
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found in .venv\Scripts\Activate.ps1" -ForegroundColor Red
}
uvicorn main:app --reload --port 8001
