from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# Forward references
class Monitor(SQLModel, table=False):
    pass

class ProjectBase(SQLModel):
    job_number: str = Field(index=True)
    job_name: str
    client: str
    client_job_ref: Optional[str] = None
    survey_start_date: Optional[datetime] = None
    survey_end_date: Optional[datetime] = None
    survey_complete: bool = False

class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    sites: List["Site"] = Relationship(back_populates="project")
    installs: List["Install"] = Relationship(back_populates="project")
    # Monitors are usually global assets, but FSM Project has a list of "available" monitors?
    # Or maybe monitors are just linked via Installs. 
    # In legacy code, fsmProject has dict_fsm_monitors.
    # We'll assume Monitors are independent assets but can be associated with a project context if needed.

class SiteBase(SQLModel):
    site_id: str = Field(index=True) # User facing ID e.g. "MH123"
    site_type: str = "Flow Monitor" # Network Asset or Location
    address: Optional[str] = None
    mh_ref: Optional[str] = None
    w3w: Optional[str] = None
    easting: float = 0.0
    northing: float = 0.0

class Site(SiteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    
    project: Optional[Project] = Relationship(back_populates="sites")
    installs: List["Install"] = Relationship(back_populates="site")

class InstallBase(SQLModel):
    install_id: str = Field(index=True)
    install_type: str = "Flow Monitor"
    client_ref: Optional[str] = None
    install_date: Optional[datetime] = None
    remove_date: Optional[datetime] = None
    
    # FM Specific
    fm_pipe_letter: str = "A"
    fm_pipe_shape: str = "Circular"
    fm_pipe_height_mm: int = 225
    fm_pipe_width_mm: int = 225
    fm_pipe_depth_to_invert_mm: int = 0
    fm_sensor_offset_mm: int = 0
    
    # RG Specific
    rg_position: str = "Ground"

class Install(InstallBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    site_id: Optional[int] = Field(default=None, foreign_key="site.id")
    monitor_id: Optional[int] = Field(default=None, foreign_key="monitor.id")
    
    project: Optional[Project] = Relationship(back_populates="installs")
    site: Optional[Site] = Relationship(back_populates="installs")
    monitor: Optional["Monitor"] = Relationship(back_populates="installs")
