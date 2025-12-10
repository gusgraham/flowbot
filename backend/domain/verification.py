from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class VerificationProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class VerificationProjectCollaborator(SQLModel, table=True):
    """Link table for Verification project collaborators (many-to-many)"""
    project_id: int = Field(foreign_key="verificationproject.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

class VerificationProject(VerificationProjectBase, table=True):
    __tablename__ = "verificationproject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Collaborators (Many-to-Many)
    collaborators: List["User"] = Relationship(link_model=VerificationProjectCollaborator)

class VerificationProjectCreate(SQLModel):
    name: str
    job_number: str
    client: str
    model_name: Optional[str] = None
    description: Optional[str] = None

class VerificationProjectRead(VerificationProjectCreate):
    id: int
    owner_id: Optional[int]
    created_at: datetime
