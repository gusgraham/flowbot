from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
# Forward references
if False:
    from .monitor import Monitor
    from .project import Install

class TimeSeriesBase(SQLModel):
    install_id: Optional[int] = Field(default=None, foreign_key="install.id")
    monitor_id: Optional[int] = Field(default=None, foreign_key="monitor.id")
    variable: str # Flow, Depth, Velocity, Rain
    data_type: str # Raw, Processed, Model
    start_time: datetime
    end_time: datetime
    interval_minutes: int
    filename: Optional[str] = None # Path to parquet/csv file
    
class TimeSeries(TimeSeriesBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    monitor: Optional["Monitor"] = Relationship()
    install: Optional["Install"] = Relationship()

class EventBase(SQLModel):
    install_id: int = Field(foreign_key="install.id")
    event_type: str # Storm, DryDay, DW
    start_time: datetime
    end_time: datetime
    label: Optional[str] = None
    
class Event(EventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
