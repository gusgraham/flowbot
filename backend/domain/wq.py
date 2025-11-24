from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class WaterQualityProjectBase(SQLModel):
    name: str = Field(index=True)
    client: str
    job_number: str = Field(index=True)
    campaign_date: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class WaterQualityProject(WaterQualityProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Future: Relationships to WQ samples, lab results

class WaterQualityProjectCreate(WaterQualityProjectBase):
    pass

class WaterQualityProjectRead(WaterQualityProjectBase):
    id: int
