from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Forward reference
from .project import Install

class MonitorBase(SQLModel):
    monitor_asset_id: str = Field(index=True, unique=True)
    monitor_type: str = "Flow Monitor"
    monitor_sub_type: str = "Detec"
    pmac_id: Optional[str] = None
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")

class Monitor(MonitorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project: Optional["Project"] = Relationship(back_populates="monitors")
    installs: List["Install"] = Relationship(back_populates="monitor")
    timeseries: List["TimeSeries"] = Relationship(back_populates="monitor")

class MonitorCreate(MonitorBase):
    pass

class MonitorRead(MonitorBase):
    id: int

