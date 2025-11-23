from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlmodel import Session
from database import get_session
from services.dashboard import DashboardService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> DashboardService:
    return DashboardService(session)

@router.get("/projects/{project_id}/monitor-status")
def get_monitor_status(project_id: int, service: DashboardService = Depends(get_service)):
    return service.get_monitor_status(project_id)

@router.get("/monitors/{monitor_id}/history")
def get_monitor_history(monitor_id: int, service: DashboardService = Depends(get_service)):
    return service.get_monitor_history(monitor_id)

@router.get("/projects/{project_id}/data-summary")
def get_data_summary(project_id: int, service: DashboardService = Depends(get_service)):
    return service.get_data_summary(project_id)

@router.get("/projects/{project_id}/issues")
def get_issues(project_id: int, service: DashboardService = Depends(get_service)):
    return service.get_issues(project_id)
