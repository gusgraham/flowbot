from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
from database import get_session
from domain.visit import VisitRead, VisitCreate
from services.install import InstallService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> InstallService:
    return InstallService(session)

# Visits
@router.post("/installs/{install_id}/visits", response_model=VisitRead)
def create_visit(install_id: int, visit: VisitCreate, service: InstallService = Depends(get_service)):
    # Ensure install_id in path matches body? Or override?
    visit.install_id = install_id
    return service.create_visit(visit)

@router.get("/installs/{install_id}/visits", response_model=List[VisitRead])
def list_visits(install_id: int, service: InstallService = Depends(get_service)):
    return service.list_visits(install_id)

# Ingestion
@router.post("/installs/{install_id}/upload")
async def upload_data(install_id: int, file: UploadFile = File(...), service: InstallService = Depends(get_service)):
    content = await file.read()
    service.upload_data(install_id, content, file.filename)
    return {"message": "File uploaded successfully", "filename": file.filename}
