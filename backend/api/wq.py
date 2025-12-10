from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select, or_, col
from database import get_session
from services.wq import WQService
from domain.wq import WaterQualityProject, WaterQualityProjectCreate, WaterQualityProjectRead, WQProjectCollaborator
from domain.auth import User
from api.deps import get_current_active_user

router = APIRouter()

# Water Quality Projects
@router.post("/wq/projects", response_model=WaterQualityProjectRead)
def create_wq_project(
    project: WaterQualityProjectCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_project = WaterQualityProject.model_validate(project)
    db_project.owner_id = current_user.id
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/wq/projects", response_model=List[WaterQualityProjectRead])
def list_wq_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_superuser or current_user.role == 'Admin':
        projects = session.exec(select(WaterQualityProject).offset(offset).limit(limit)).all()
    else:
        # Include owned projects OR collaborative projects
        collab_subquery = select(WQProjectCollaborator.project_id).where(
            WQProjectCollaborator.user_id == current_user.id
        )
        projects = session.exec(
            select(WaterQualityProject).where(
                or_(
                    WaterQualityProject.owner_id == current_user.id,
                    col(WaterQualityProject.id).in_(collab_subquery)
                )
            ).offset(offset).limit(limit)
        ).all()
    return projects

@router.get("/wq/projects/{project_id}", response_model=WaterQualityProjectRead)
def get_wq_project(
    project_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
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

# ==========================================
# COLLABORATORS
# ==========================================

@router.get("/wq/projects/{project_id}/collaborators")
def list_collaborators(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all collaborators for a project."""
    project = session.get(WaterQualityProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    statement = select(User).join(WQProjectCollaborator).where(
        WQProjectCollaborator.project_id == project_id
    )
    return session.exec(statement).all()

@router.post("/wq/projects/{project_id}/collaborators")
def add_collaborator(
    project_id: int,
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a collaborator to a project."""
    project = session.get(WaterQualityProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can add collaborators")
    
    user_to_add = session.exec(select(User).where(User.username == username)).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = session.exec(select(WQProjectCollaborator).where(
        WQProjectCollaborator.project_id == project_id,
        WQProjectCollaborator.user_id == user_to_add.id
    )).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    link = WQProjectCollaborator(project_id=project_id, user_id=user_to_add.id)
    session.add(link)
    session.commit()
    
    return user_to_add

@router.delete("/wq/projects/{project_id}/collaborators/{user_id}")
def remove_collaborator(
    project_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a collaborator from a project."""
    project = session.get(WaterQualityProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")
    
    link = session.exec(select(WQProjectCollaborator).where(
        WQProjectCollaborator.project_id == project_id,
        WQProjectCollaborator.user_id == user_id
    )).first()
    
    if link:
        session.delete(link)
        session.commit()
    
    return {"message": "Collaborator removed"}

