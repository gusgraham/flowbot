from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class WaterQualityProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    campaign_date: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class WQProjectCollaborator(SQLModel, table=True):
    __tablename__ = "wq_projectcollaborator"
    """Link table for Water Quality project collaborators (many-to-many)"""
    project_id: int = Field(foreign_key="wq_project.id", primary_key=True)
    user_id: int = Field(foreign_key="auth_user.id", primary_key=True)

class WaterQualityProject(WaterQualityProjectBase, table=True):
    __tablename__ = "wq_project"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="auth_user.id")
    
    # Relationships
    collaborators: List["User"] = Relationship(link_model=WQProjectCollaborator)
    datasets: List["WaterQualityDataset"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    monitors: List["WQMonitor"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

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

# ==========================================
# WQ DATASET
# ==========================================

class WaterQualityDatasetBase(SQLModel):
    name: str
    project_id: int = Field(foreign_key="wq_project.id")
    file_path: str
    original_filename: str
    upload_date: datetime = Field(default_factory=datetime.now)
    status: str = "pending" # pending, processed, error
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))

class WaterQualityDataset(WaterQualityDatasetBase, table=True):
    __tablename__ = "wq_dataset"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project: Optional[WaterQualityProject] = Relationship(back_populates="datasets")
    timeseries: List["WQTimeSeries"] = Relationship(back_populates="dataset", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class WaterQualityDatasetCreate(SQLModel):
    project_id: int
    name: str = "New Upload"

class WaterQualityDatasetRead(WaterQualityDatasetBase):
    id: int

# ==========================================
# WQ MONITOR
# ==========================================

class WQMonitorBase(SQLModel):
    project_id: int = Field(foreign_key="wq_project.id")
    name: str
    description: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None

class WQMonitor(WQMonitorBase, table=True):
    __tablename__ = "wq_monitor"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project: Optional[WaterQualityProject] = Relationship(back_populates="monitors")
    timeseries: List["WQTimeSeries"] = Relationship(back_populates="monitor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class WQMonitorCreate(WQMonitorBase):
    pass

class WQMonitorRead(WQMonitorBase):
    id: int

# ==========================================
# WQ TIME SERIES
# ==========================================

class WQTimeSeriesBase(SQLModel):
    monitor_id: int = Field(foreign_key="wq_monitor.id")
    dataset_id: int = Field(foreign_key="wq_dataset.id")
    variable: str # pH, DO, Temp, etc.
    unit: Optional[str] = None
    start_time: datetime
    end_time: datetime
    filename: str # Parquet file path

class WQTimeSeries(WQTimeSeriesBase, table=True):
    __tablename__ = "wq_timeseries"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    monitor: Optional[WQMonitor] = Relationship(back_populates="timeseries")
    dataset: Optional[WaterQualityDataset] = Relationship(back_populates="timeseries")

class WQTimeSeriesRead(WQTimeSeriesBase):
    id: int
