from typing import List
from sqlmodel import Session
from domain.qa import Note, NoteCreate, Attachment, AttachmentCreate
from repositories.qa import NoteRepository, AttachmentRepository
from infra.storage import StorageService

class QAService:
    def __init__(self, session: Session):
        self.session = session
        self.note_repo = NoteRepository(session)
        self.attachment_repo = AttachmentRepository(session)
        self.storage_service = StorageService()
    
    # Notes
    def create_note(self, note_in: NoteCreate) -> Note:
        note = Note.from_orm(note_in)
        return self.note_repo.create(note)
    
    def list_notes(self, project_id: int) -> List[Note]:
        return self.note_repo.list_by_project(project_id)
    
    # Attachments
    def create_attachment(self, attachment_in: AttachmentCreate, file_content: bytes = None) -> Attachment:
        # Save file if content provided
        if file_content:
            file_path = self.storage_service.save_file(
                file_content, 
                attachment_in.filename, 
                subfolder="attachments"
            )
            attachment_in.file_path = file_path
        
        attachment = Attachment.from_orm(attachment_in)
        return self.attachment_repo.create(attachment)
    
    def list_attachments(self, project_id: int) -> List[Attachment]:
        return self.attachment_repo.list_by_project(project_id)
