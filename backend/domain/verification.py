from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class VerificationProjectBase(SQLModel):
    name: str = Field(index=True)
    client: str
    job_number: str = Field(index=True)
    model_name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class VerificationProject(VerificationProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Future: Relationships to verification runs, model results

class VerificationProjectCreate(VerificationProjectBase):
    pass

class VerificationProjectRead(VerificationProjectBase):
    id: int
