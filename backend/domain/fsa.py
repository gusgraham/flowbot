from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# ==========================================
# FSA PROJECT
# ==========================================

class FsaProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class FsaProjectCollaborator(SQLModel, table=True):
    """Link table for FSA project collaborators (many-to-many)"""
    project_id: int = Field(foreign_key="fsaproject.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

class FsaProject(FsaProjectBase, table=True):
    __tablename__ = "fsaproject"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    datasets: List["FsaDataset"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    events: List["SurveyEvent"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    collaborators: List["User"] = Relationship(link_model=FsaProjectCollaborator)

class FsaProjectCreate(SQLModel):
    name: str
    job_number: str
    client: str
    description: Optional[str] = None

class FsaProjectRead(FsaProjectCreate):
    id: int
    owner_id: Optional[int]
    created_at: datetime

# ==========================================
# FSA DATASET
# ==========================================

class FsaDatasetBase(SQLModel):
    project_id: int = Field(foreign_key="fsaproject.id")
    name: str
    variable: str  # 'Rainfall', 'Flow', 'Depth', 'Velocity', 'Flow/Depth'
    source: str = "Uploaded"  # e.g. "Uploaded", "Manual Entry"
    file_path: Optional[str] = None  # Path to uploaded file
    status: str = Field(default="processing")  # 'processing', 'ready', 'error'
    error_message: Optional[str] = None
    imported_at: datetime = Field(default_factory=datetime.now)
    metadata_json: str = Field(default="{}")  # Store extra info like units, gauge name

class FsaDataset(FsaDatasetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project: Optional[FsaProject] = Relationship(back_populates="datasets")
    flow_monitors: List["FlowMonitor"] = Relationship(back_populates="dataset", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    rain_gauges: List["RainGauge"] = Relationship(back_populates="dataset", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    timeseries: List["FsaTimeSeries"] = Relationship(back_populates="dataset", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class FsaDatasetCreate(FsaDatasetBase):
    pass

class FsaDatasetRead(FsaDatasetBase):
    id: int
    status: str
    error_message: Optional[str]
    metadata_json: str
    imported_at: datetime

# ==========================================
# FLOW MONITOR
# ==========================================

class FlowMonitorBase(SQLModel):
    dataset_id: int = Field(foreign_key="fsadataset.id")
    name: str
    timestep_minutes: float
    flow_units: str = "l/s"
    depth_units: str = "mm"
    velocity_units: str = "m/s"
    
    # Location
    x: Optional[float] = None
    y: Optional[float] = None

class FlowMonitor(FlowMonitorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    dataset: Optional[FsaDataset] = Relationship(back_populates="flow_monitors")
    
    # 1:1 Relationships (simulated via foreign keys or just embedded if simple)
    # For now, we'll keep them on the main table or separate if complex.
    # Let's separate Model and Stats for cleanliness as per the ERD.
    
    stats: Optional["FlowMonitorStats"] = Relationship(back_populates="monitor", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"})
    model: Optional["FlowMonitorModel"] = Relationship(back_populates="monitor", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"})

class FlowMonitorCreate(FlowMonitorBase):
    pass

class FlowMonitorRead(FlowMonitorBase):
    id: int

# ==========================================
# FLOW MONITOR DETAILS (Stats & Model)
# ==========================================

class FlowMonitorStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_id: int = Field(foreign_key="flowmonitor.id", unique=True)
    
    min_flow: Optional[float] = None
    max_flow: Optional[float] = None
    total_volume: Optional[float] = None
    min_depth: Optional[float] = None
    max_depth: Optional[float] = None
    min_velocity: Optional[float] = None
    max_velocity: Optional[float] = None
    
    monitor: Optional[FlowMonitor] = Relationship(back_populates="stats")

class FlowMonitorModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_id: int = Field(foreign_key="flowmonitor.id", unique=True)
    
    has_model_data: bool = False
    pipe_ref: Optional[str] = None
    model_rg: Optional[str] = None
    pipe_length: Optional[float] = None
    pipe_shape: Optional[str] = None
    pipe_dia: Optional[float] = None
    pipe_height: Optional[float] = None
    pipe_roughness: Optional[float] = None
    us_invert: Optional[float] = None
    ds_invert: Optional[float] = None
    system_type: Optional[str] = None # Combined, Foul, Surface
    
    monitor: Optional[FlowMonitor] = Relationship(back_populates="model")

# ==========================================
# RAIN GAUGE
# ==========================================

class RainGaugeBase(SQLModel):
    dataset_id: int = Field(foreign_key="fsadataset.id")
    name: str
    timestep_minutes: float
    
    # Location
    x: Optional[float] = None
    y: Optional[float] = None

class RainGauge(RainGaugeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    dataset: Optional[FsaDataset] = Relationship(back_populates="rain_gauges")
    stats: Optional["RainGaugeStats"] = Relationship(back_populates="rain_gauge", sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"})

class RainGaugeStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rain_gauge_id: int = Field(foreign_key="raingauge.id", unique=True)
    
    min_intensity: Optional[float] = None
    max_intensity: Optional[float] = None
    total_depth: Optional[float] = None
    return_period: Optional[float] = None
    
    rain_gauge: Optional[RainGauge] = Relationship(back_populates="stats")

# ==========================================
# SURVEY EVENTS
# ==========================================

class SurveyEventBase(SQLModel):
    project_id: int = Field(foreign_key="fsaproject.id")
    event_type: str # Storm, DryDay
    start_time: datetime
    end_time: datetime
    name: Optional[str] = None

class SurveyEvent(SurveyEventBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project: Optional[FsaProject] = Relationship(back_populates="events")

class SurveyEventCreate(SurveyEventBase):
    pass

class SurveyEventRead(SurveyEventBase):
    id: int

# ==========================================
# TIMESERIES DATA
# ==========================================

class FsaTimeSeriesBase(SQLModel):
    dataset_id: int = Field(foreign_key="fsadataset.id", index=True)
    timestamp: datetime = Field(index=True)
    value: Optional[float] = None  # rainfall (mm/hr) or generic value
    flow: Optional[float] = None  # L/s
    depth: Optional[float] = None  # mm
    velocity: Optional[float] = None  # m/s

class FsaTimeSeries(FsaTimeSeriesBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    dataset: Optional[FsaDataset] = Relationship(back_populates="timeseries")

class FsaTimeSeriesRead(FsaTimeSeriesBase):
    id: int
