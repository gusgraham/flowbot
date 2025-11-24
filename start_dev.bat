@echo off
echo Starting FlowBot Hub Development Environment...

:: Start Backend
start "FlowBot Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn main:app --reload --port 8001"

:: Start Frontend
start "FlowBot Frontend" cmd /k "cd frontend && npm run dev"

echo Servers are starting in new windows...
