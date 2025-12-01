from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class AnalysisProjectBase(SQLModel):
    name: str = Field(index=True)
    client: str
    job_number: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class AnalysisProject(AnalysisProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Future: Relationships to imported datasets or analysis results

class AnalysisProjectCreate(AnalysisProjectBase):
    pass

class AnalysisProjectRead(AnalysisProjectBase):
    id: int

class AnalysisDatasetBase(SQLModel):
    project_id: int = Field(foreign_key="analysisproject.id")
    name: str
    variable: str  # 'Rainfall', 'Flow', 'Depth', 'Velocity'
    file_path: str
    status: str = Field(default="processing")  # 'processing', 'ready', 'error'
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata_json: str = Field(default="{}", sa_column_kwargs={"name": "metadata"}) # Store extra info like units, gauge name

class AnalysisDataset(AnalysisDatasetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
class AnalysisDatasetRead(AnalysisDatasetBase):
    id: int
    status: str
    error_message: Optional[str]
    metadata_json: str

class AnalysisTimeSeriesBase(SQLModel):
    dataset_id: int = Field(foreign_key="analysisdataset.id", index=True)
    timestamp: datetime = Field(index=True)
    value: Optional[float] = None # rainfall (mm/hr) or generic value
    flow: Optional[float] = None # L/s
    depth: Optional[float] = None # mm
    velocity: Optional[float] = None # m/s

class AnalysisTimeSeries(AnalysisTimeSeriesBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class AnalysisTimeSeriesRead(AnalysisTimeSeriesBase):
    id: int
