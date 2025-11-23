from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlmodel import Session
from database import get_session
from domain.qa import NoteRead, NoteCreate, AttachmentRead, AttachmentCreate
from services.qa import QAService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> QAService:
    return QAService(session)

# Notes
@router.post("/projects/{project_id}/notes", response_model=NoteRead)
def create_note(project_id: int, note: NoteCreate, service: QAService = Depends(get_service)):
    note.project_id = project_id
    return service.create_note(note)

@router.get("/projects/{project_id}/notes", response_model=List[NoteRead])
def list_notes(project_id: int, service: QAService = Depends(get_service)):
    return service.list_notes(project_id)

# Attachments
@router.post("/projects/{project_id}/attachments", response_model=AttachmentRead)
async def create_attachment(
    project_id: int, 
    file: UploadFile = File(...),
    service: QAService = Depends(get_service)
):
    content = await file.read()
    attachment_in = AttachmentCreate(
        filename=file.filename,
        file_path="",  # Will be set by service
        user_id=1,  # TODO: Get from auth context
        project_id=project_id
    )
    return service.create_attachment(attachment_in, content)

@router.get("/projects/{project_id}/attachments", response_model=List[AttachmentRead])
def list_attachments(project_id: int, service: QAService = Depends(get_service)):
    return service.list_attachments(project_id)
