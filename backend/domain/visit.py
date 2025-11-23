from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class VisitBase(SQLModel):
    install_id: int = Field(foreign_key="install.id")
    visit_date: datetime
    crew_lead: str
    silt_level_mm: Optional[int] = 0
    battery_voltage: Optional[float] = None
    notes: Optional[str] = None
    photos_json: Optional[str] = None # JSON list of filenames

class Visit(VisitBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    install: Optional["Install"] = Relationship(back_populates="visits")

class VisitCreate(VisitBase):
    pass

class VisitRead(VisitBase):
    id: int
