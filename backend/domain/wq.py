from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class WaterQualityProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    campaign_date: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class WQProjectCollaborator(SQLModel, table=True):
    """Link table for Water Quality project collaborators (many-to-many)"""
    project_id: int = Field(foreign_key="waterqualityproject.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

class WaterQualityProject(WaterQualityProjectBase, table=True):
    __tablename__ = "waterqualityproject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # Collaborators (Many-to-Many)
    collaborators: List["User"] = Relationship(link_model=WQProjectCollaborator)

class WaterQualityProjectCreate(SQLModel):
    name: str
    job_number: str
    client: str
    campaign_date: Optional[datetime] = None
    description: Optional[str] = None

class WaterQualityProjectRead(WaterQualityProjectCreate):
    id: int
    owner_id: Optional[int]
    created_at: datetime
