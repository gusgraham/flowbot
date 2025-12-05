from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from database import get_session
from services.ingestion import IngestionService
from domain.auth import User
from api.deps import get_current_active_user

router = APIRouter()

def get_ingestion_service(session: Session = Depends(get_session)) -> IngestionService:
    return IngestionService(session)

@router.post("/projects/{project_id}/ingest")
def trigger_ingestion(
    project_id: int, 
    background_tasks: BackgroundTasks,
    service: IngestionService = Depends(get_ingestion_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger bulk raw data ingestion for a project.
    Runs as a background task.
    """
    # Access control could be refined (check project owner), but basic auth is here.
    
    background_tasks.add_task(service.ingest_project, project_id)
    return {"message": "Ingestion started", "status": "processing"}
