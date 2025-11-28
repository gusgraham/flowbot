from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# Forward references
if False:
    from .project import Install

class RawData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    install_id: int = Field(foreign_key="install.id", unique=True)
    
    # File config
    rainfall_file_pattern: Optional[str] = None
    depth_file_pattern: Optional[str] = None
    velocity_file_pattern: Optional[str] = None
    
    # Calibration (stored as JSON)
    silt_levels_json: Optional[str] = None # List of {date, value}
    depth_corrections_json: Optional[str] = None # List of {date, offset}
    velocity_corrections_json: Optional[str] = None
    
    # Overrides
    pipe_shape_override: Optional[str] = None
    
    install: Optional["Install"] = Relationship(back_populates="raw_data")

class ProcessedData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    install_id: int = Field(foreign_key="install.id")
    
    # Time range
    start_time: datetime
    end_time: datetime
    
    # Storage
    file_path: str # Path to Parquet/Arrow file containing Flow, Depth, Velocity, Rain columns
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    install: Optional["Install"] = Relationship(back_populates="processed_data")

class Interim(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    
    start_date: datetime
    end_date: datetime
    
    # Status flags
    data_import_complete: bool = False
    site_inspection_review_complete: bool = False
    data_classification_complete: bool = False
    report_complete: bool = False
    
    summary_text: Optional[str] = None
    
    reviews: List["InterimReview"] = Relationship(back_populates="interim")
    project: Optional["Project"] = Relationship(back_populates="interims")

class InterimReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interim_id: int = Field(foreign_key="interim.id")
    install_id: int = Field(foreign_key="install.id")
    
    # Data Coverage
    data_covered: bool = False
    ignore_missing: bool = False
    reason_missing: Optional[str] = None
    
    # QA Checks
    anomalies_found: bool = False
    comments: Optional[str] = None
    
    interim: Optional[Interim] = Relationship(back_populates="reviews")
    install: Optional["Install"] = Relationship()
