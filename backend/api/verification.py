from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select, or_, col
from database import get_session
from services.verification import VerificationService
from domain.verification import VerificationProject, VerificationProjectCreate, VerificationProjectRead, VerificationProjectCollaborator
from domain.auth import User
from api.deps import get_current_active_user

router = APIRouter()

# Verification Projects
@router.post("/verification/projects", response_model=VerificationProjectRead)
def create_verification_project(
    project: VerificationProjectCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_project = VerificationProject.model_validate(project)
    db_project.owner_id = current_user.id
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@router.get("/verification/projects", response_model=List[VerificationProjectRead])
def list_verification_projects(
    offset: int = 0, 
    limit: int = 100, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_superuser or current_user.role == 'Admin':
        projects = session.exec(select(VerificationProject).offset(offset).limit(limit)).all()
    else:
        # Include owned projects OR collaborative projects
        collab_subquery = select(VerificationProjectCollaborator.project_id).where(
            VerificationProjectCollaborator.user_id == current_user.id
        )
        projects = session.exec(
            select(VerificationProject).where(
                or_(
                    VerificationProject.owner_id == current_user.id,
                    col(VerificationProject.id).in_(collab_subquery)
                )
            ).offset(offset).limit(limit)
        ).all()
    return projects

@router.get("/verification/projects/{project_id}", response_model=VerificationProjectRead)
def get_verification_project(
    project_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
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

# ==========================================
# COLLABORATORS
# ==========================================

@router.get("/verification/projects/{project_id}/collaborators")
def list_collaborators(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all collaborators for a project."""
    project = session.get(VerificationProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    statement = select(User).join(VerificationProjectCollaborator).where(
        VerificationProjectCollaborator.project_id == project_id
    )
    return session.exec(statement).all()

@router.post("/verification/projects/{project_id}/collaborators")
def add_collaborator(
    project_id: int,
    username: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Add a collaborator to a project."""
    project = session.get(VerificationProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can add collaborators")
    
    user_to_add = session.exec(select(User).where(User.username == username)).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = session.exec(select(VerificationProjectCollaborator).where(
        VerificationProjectCollaborator.project_id == project_id,
        VerificationProjectCollaborator.user_id == user_to_add.id
    )).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a collaborator")
    
    link = VerificationProjectCollaborator(project_id=project_id, user_id=user_to_add.id)
    session.add(link)
    session.commit()
    
    return user_to_add

@router.delete("/verification/projects/{project_id}/collaborators/{user_id}")
def remove_collaborator(
    project_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a collaborator from a project."""
    project = session.get(VerificationProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not (current_user.is_superuser or current_user.role == 'Admin' or project.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Only the owner can remove collaborators")
    
    link = session.exec(select(VerificationProjectCollaborator).where(
        VerificationProjectCollaborator.project_id == project_id,
        VerificationProjectCollaborator.user_id == user_id
    )).first()
    
    if link:
        session.delete(link)
        session.commit()
    
    return {"message": "Collaborator removed"}

