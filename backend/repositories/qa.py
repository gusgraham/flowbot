from typing import List
from sqlmodel import Session, select
from domain.qa import Note, Attachment
from repositories.base import BaseRepository

class NoteRepository(BaseRepository[Note]):
    def __init__(self, session: Session):
        super().__init__(session, Note)
    
    def list_by_project(self, project_id: int) -> List[Note]:
        statement = select(Note).where(Note.project_id == project_id)
        return self.session.exec(statement).all()

class AttachmentRepository(BaseRepository[Attachment]):
    def __init__(self, session: Session):
        super().__init__(session, Attachment)
    
    def list_by_project(self, project_id: int) -> List[Attachment]:
        statement = select(Attachment).where(Attachment.project_id == project_id)
        return self.session.exec(statement).all()
