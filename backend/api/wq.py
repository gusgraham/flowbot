from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from database import get_session
from services.wq import WQService
from domain.wq import WaterQualityProject, WaterQualityProjectCreate, WaterQualityProjectRead

router = APIRouter()

# Water Quality Projects
@router.post("/wq/projects", response_model=WaterQualityProjectRead)
def create_wq_project(
    project: WaterQualityProjectCreate, 
    session: Session = Depends(get_session)
):
    db_project = WaterQualityProject.from_orm(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/wq/projects", response_model=List[WaterQualityProjectRead])
def list_wq_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    projects = session.exec(select(WaterQualityProject).offset(offset).limit(limit)).all()
    return projects

@router.get("/wq/projects/{project_id}", response_model=WaterQualityProjectRead)
def get_wq_project(
    project_id: int, 
    session: Session = Depends(get_session)
):
    project = session.get(WaterQualityProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Water Quality Project not found")
    return project

def get_service(session: Session = Depends(get_session)) -> WQService:
    return WQService(session)

@router.post("/wq/{monitor_id}/upload")
async def upload_wq_data(
    monitor_id: int,
    file: UploadFile = File(...),
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    try:
        content = await file.read()
        created_ts = service.import_wq_data(monitor_id, content, file.filename)
        return {
            "monitor_id": monitor_id,
            "message": "WQ data imported successfully",
            "created_records": len(created_ts),
            "variables": [ts.variable for ts in created_ts]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wq/{monitor_id}/data")
def get_wq_data(
    monitor_id: int,
    service: WQService = Depends(get_service)
) -> List[Dict[str, Any]]:
    return service.get_wq_timeseries(monitor_id)

@router.get("/wq/{monitor_id}/correlation")
def correlate_wq_flow(
    monitor_id: int,
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    return service.correlate_wq_flow(monitor_id)
