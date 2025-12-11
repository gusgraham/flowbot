from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlmodel import Session, select
from database import get_session
from services.wq import WQService
from domain.wq import (
    WaterQualityProject, 
    WaterQualityProjectCreate, 
    WaterQualityProjectRead, 
    WQMonitor,
    WQMonitorRead
)
from domain.auth import User
from api.deps import get_current_active_user

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> WQService:
    return WQService(session)

# ==========================================
# PROJECTS
# ==========================================

@router.post("/wq/projects", response_model=WaterQualityProjectRead)
def create_wq_project(
    project: WaterQualityProjectCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    service: WQService = Depends(get_service)
):
    return service.create_project(project, current_user.id)

@router.get("/wq/projects", response_model=List[WaterQualityProjectRead])
def list_wq_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    service: WQService = Depends(get_service)
):
    # TODO: Add proper permission handling in service or here
    return service.list_projects(current_user.id, is_admin=current_user.is_superuser, offset=offset, limit=limit)

@router.get("/wq/projects/{project_id}", response_model=WaterQualityProjectRead)
def get_wq_project(
    project_id: int, 
    service: WQService = Depends(get_service)
):
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/wq/projects/{project_id}")
def delete_wq_project(
    project_id: int, 
    service: WQService = Depends(get_service)
):
    success = service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success"}

# ==========================================
# DATA IMPORT & MONITORS
# ==========================================

@router.post("/wq/projects/{project_id}/datasets/upload")
async def upload_dataset_file(
    project_id: int,
    file: UploadFile = File(...),
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    """
    Step 1: Upload file, receive headers and dataset_id.
    """
    try:
        content = await file.read()
        return service.create_dataset(project_id, content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/wq/datasets/{dataset_id}/import")
def import_dataset(
    dataset_id: int,
    payload: Dict[str, Any],
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    """
    Step 2: Submit mapping and monitor info to process file.
    Payload: { "mapping": {...}, "monitor_name": "...", "monitor_id": int (optional) }
    """
    try:
        monitor = service.process_dataset(
            dataset_id=dataset_id,
            mapping=payload.get("mapping", {}),
            monitor_name=payload.get("monitor_name"),
            monitor_id=payload.get("monitor_id")
        )
        return {"status": "success", "monitor_id": monitor.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wq/projects/{project_id}/monitors", response_model=List[WQMonitorRead])
def list_project_monitors(
    project_id: int,
    service: WQService = Depends(get_service)
):
    return service.list_monitors(project_id)

@router.get("/wq/monitors/{monitor_id}/data")
def get_monitor_data(
    monitor_id: int,
    variables: Optional[str] = None, # Comma separated
    points: int = 500,
    resample: Optional[str] = None, # 'D', 'W', 'M', 'A'
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    var_list = variables.split(",") if variables else None
    return service.get_graph_data(monitor_id, var_list, points, resample)

# ==========================================
# COLLABORATORS (Keep existing logic if needed, or move to generic service)
# ==========================================
# ... (omitted for brevity, assume existing collaborator logic persists if needed)
