from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select
from database import get_session
from services.verification import VerificationService
from domain.verification import VerificationProject, VerificationProjectCreate, VerificationProjectRead

router = APIRouter()

# Verification Projects
@router.post("/verification/projects", response_model=VerificationProjectRead)
def create_verification_project(
    project: VerificationProjectCreate, 
    session: Session = Depends(get_session)
):
    db_project = VerificationProject.from_orm(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/verification/projects", response_model=List[VerificationProjectRead])
def list_verification_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session)
):
    projects = session.exec(select(VerificationProject).offset(offset).limit(limit)).all()
    return projects

@router.get("/verification/projects/{project_id}", response_model=VerificationProjectRead)
def get_verification_project(
    project_id: int, 
    session: Session = Depends(get_session)
):
    project = session.get(VerificationProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Verification Project not found")
    return project

def get_service(session: Session = Depends(get_session)) -> VerificationService:
    return VerificationService(session)

@router.post("/verification/{monitor_id}/upload-model")
async def upload_model_results(
    monitor_id: int,
    file: UploadFile = File(...),
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    try:
        content = await file.read()
        created_ts = service.import_model_results(monitor_id, content, file.filename)
        return {
            "monitor_id": monitor_id,
            "message": "Model results imported successfully",
            "created_records": len(created_ts)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verification/{monitor_id}/compare")
def get_comparison_data(
    monitor_id: int,
    start_date: str = None,
    end_date: str = None,
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    return service.get_comparison_data(monitor_id, start_date, end_date)

@router.get("/verification/{monitor_id}/scores")
def calculate_scores(
    monitor_id: int,
    start_date: str = None,
    end_date: str = None,
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    return service.calculate_scores(monitor_id, start_date, end_date)
