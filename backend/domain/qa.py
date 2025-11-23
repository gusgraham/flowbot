from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class NoteBase(SQLModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int
    # Polymorphic association? Or just optional FKs?
    project_id: Optional[int] = None
    site_id: Optional[int] = None
    monitor_id: Optional[int] = None
    install_id: Optional[int] = None

class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class NoteCreate(NoteBase):
    pass

class NoteRead(NoteBase):
    id: int

class AttachmentBase(SQLModel):
    filename: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int
    note_id: Optional[int] = None # Attach to note?
    # Or direct attachment to entities
    project_id: Optional[int] = None
    site_id: Optional[int] = None
    monitor_id: Optional[int] = None
    install_id: Optional[int] = None

class Attachment(AttachmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentRead(AttachmentBase):
    id: int
