"""
Flow Survey Management (FSM) Domain Models
All models related to Flow Survey management are consolidated here.
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# ==========================================
# FSM PROJECT
# ==========================================

class FsmProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    client_job_ref: Optional[str] = None
    description: Optional[str] = None
    survey_start_date: Optional[datetime] = None
    survey_end_date: Optional[datetime] = None
    survey_complete: bool = False
    default_download_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ProjectCollaborator(SQLModel, table=True):
    __tablename__ = "fsm_projectcollaborator"
    project_id: int = Field(foreign_key="fsm_project.id", primary_key=True)
    user_id: int = Field(foreign_key="auth_user.id", primary_key=True)
    # can_edit: bool = True # Future extension

class FsmProject(FsmProjectBase, table=True):
    __tablename__ = "fsm_project"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="auth_user.id")
    last_ingestion_date: Optional[datetime] = None
    
    # Relationships with cascade delete
    sites: List["Site"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    installs: List["Install"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    monitors: List["Monitor"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    # Collaborators (Many-to-Many via ProjectCollaborator)
    # We import User from domain.auth but to avoid circular import at top level, usage in List["User"] is string.
    # However, SQLModel needs the class available in the registry. 
    # Usually we can do: use `from domain.auth import User` inside methods or avoid explicit type if string used?
    # Actually Link models need to be defined.
    collaborators: List["User"] = Relationship(link_model=ProjectCollaborator)

class FsmProjectCreate(SQLModel):
    name: str
    job_number: str
    client: str
    client_job_ref: Optional[str] = None
    description: Optional[str] = None
    survey_start_date: Optional[datetime] = None
    survey_end_date: Optional[datetime] = None
    default_download_path: Optional[str] = None

class FsmProjectUpdate(SQLModel):
    name: Optional[str] = None
    job_number: Optional[str] = None
    client: Optional[str] = None
    client_job_ref: Optional[str] = None
    description: Optional[str] = None
    survey_start_date: Optional[datetime] = None
    survey_end_date: Optional[datetime] = None
    survey_complete: Optional[bool] = None
    default_download_path: Optional[str] = None

class FsmProjectRead(FsmProjectBase):
    id: int
    owner_id: Optional[int]
    last_ingestion_date: Optional[datetime] = None

# ==========================================
# MONITOR
# ==========================================

class MonitorBase(SQLModel):
    monitor_asset_id: str = Field(index=True, unique=True)
    monitor_type: str = "Flow Monitor"
    monitor_sub_type: str = "Detec"
    pmac_id: Optional[str] = None

class Monitor(MonitorBase, table=True):
    __tablename__ = "fsm_monitor"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="fsm_project.id")
    
    project: Optional[FsmProject] = Relationship(back_populates="monitors")
    installs: List["Install"] = Relationship(back_populates="monitor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    timeseries: List["TimeSeries"] = Relationship(back_populates="monitor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class MonitorCreate(MonitorBase):
    project_id: int

class MonitorRead(MonitorBase):
    id: int

# ==========================================
# SITE
# ==========================================

class SiteBase(SQLModel):
    site_id: str = Field(index=True)
    site_type: str = "Flow Monitor"
    address: Optional[str] = None
    mh_ref: Optional[str] = None
    w3w: Optional[str] = None
    easting: float = 0.0
    northing: float = 0.0

class Site(SiteBase, table=True):
    __tablename__ = "fsm_site"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = Field(default=None, foreign_key="fsm_project.id")
    
    project: Optional[FsmProject] = Relationship(back_populates="sites")
    installs: List["Install"] = Relationship(back_populates="site", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class SiteCreate(SiteBase):
    project_id: Optional[int] = None

class SiteRead(SiteBase):
    id: int

# ==========================================
# INSTALL
# ==========================================

class InstallBase(SQLModel):
    install_id: str = Field(index=True)
    install_type: str = "Flow Monitor"
    client_ref: Optional[str] = None
    install_date: Optional[datetime] = None
    removal_date: Optional[datetime] = Field(default=None, sa_column_kwargs={"name": "remove_date"})
    
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
    __tablename__ = "fsm_install"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    project_id: Optional[int] = Field(default=None, foreign_key="fsm_project.id")
    site_id: Optional[int] = Field(default=None, foreign_key="fsm_site.id")
    monitor_id: Optional[int] = Field(default=None, foreign_key="fsm_monitor.id")
    
    project: Optional[FsmProject] = Relationship(back_populates="installs")
    site: Optional[Site] = Relationship(back_populates="installs")
    monitor: Optional[Monitor] = Relationship(back_populates="installs")
    visits: List["Visit"] = Relationship(back_populates="install", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    timeseries: List["TimeSeries"] = Relationship(back_populates="install", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    raw_data_settings: Optional["RawDataSettings"] = Relationship(back_populates="install", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class InstallCreate(InstallBase):
    project_id: int
    site_id: int
    monitor_id: int

class InstallRead(InstallBase):
    id: int
    project_id: int
    site_id: int
    monitor_id: int
    last_data_ingested: Optional[datetime] = None
    last_data_processed: Optional[datetime] = None

# ==========================================
# VISIT
# ==========================================

class VisitBase(SQLModel):
    install_id: int = Field(foreign_key="fsm_install.id")
    visit_date: datetime
    crew_lead: str
    silt_level_mm: Optional[int] = 0
    battery_voltage: Optional[float] = None
    notes: Optional[str] = None
    photos_json: Optional[str] = None

class Visit(VisitBase, table=True):
    __tablename__ = "fsm_visit"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    install: Optional[Install] = Relationship(back_populates="visits")

class VisitCreate(VisitBase):
    pass

class VisitRead(VisitBase):
    id: int

# ==========================================
# RAW DATA SETTINGS
# ==========================================

class RawDataSettingsBase(SQLModel):
    install_id: int = Field(foreign_key="fsm_install.id", unique=True)
    
    # File ingestion paths
    file_path: Optional[str] = None
    rainfall_file_format: Optional[str] = None
    depth_file_format: Optional[str] = None
    velocity_file_format: Optional[str] = None
    battery_file_format: Optional[str] = None
    pumplogger_file_format: Optional[str] = None
    
    # Rain Gauge calibration
    rg_tb_depth: Optional[float] = None  # Tipping bucket depth (mm)
    rg_timing_corr: Optional[str] = None  # JSON: [{datetime, offset, comment}]
    
    # Flow Monitor calibration - Pipe shape
    pipe_shape: Optional[str] = None  # ARCH, CIRC, CNET, EGG, EGG2, OVAL, RECT, UTOP, USER
    pipe_width: Optional[int] = None
    pipe_height: Optional[int] = None
    pipe_shape_intervals: Optional[int] = None
    pipe_shape_def: Optional[str] = None  # JSON: [{width, height}]
    
    # Flow Monitor calibration - Corrections
    dep_corr: Optional[str] = None  # JSON: [{datetime, depth_corr, invert_offset, comment}]
    vel_corr: Optional[str] = None  # JSON: [{datetime, velocity_factor, comment}]
    dv_timing_corr: Optional[str] = None  # JSON: [{datetime, time_offset, comment}]
    silt_levels: Optional[str] = None  # JSON: [{datetime, silt_depth, comment}]
    
    # Pump Logger calibration
    pl_timing_corr: Optional[str] = None  # JSON: [{datetime, offset, comment}]
    pl_added_onoffs: Optional[str] = None  # JSON: [{datetime, state, comment}]

class RawDataSettings(RawDataSettingsBase, table=True):
    __tablename__ = "fsm_rawdatasettings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    install: Optional[Install] = Relationship(back_populates="raw_data_settings")

class RawDataSettingsCreate(RawDataSettingsBase):
    pass

class RawDataSettingsUpdate(SQLModel):
    file_path: Optional[str] = None
    rainfall_file_format: Optional[str] = None
    depth_file_format: Optional[str] = None
    velocity_file_format: Optional[str] = None
    battery_file_format: Optional[str] = None
    pumplogger_file_format: Optional[str] = None
    rg_tb_depth: Optional[float] = None
    rg_timing_corr: Optional[str] = None
    pipe_shape: Optional[str] = None
    pipe_width: Optional[int] = None
    pipe_height: Optional[int] = None
    pipe_shape_intervals: Optional[int] = None
    pipe_shape_def: Optional[str] = None
    dep_corr: Optional[str] = None
    vel_corr: Optional[str] = None
    dv_timing_corr: Optional[str] = None
    silt_levels: Optional[str] = None
    pl_timing_corr: Optional[str] = None
    pl_added_onoffs: Optional[str] = None

class RawDataSettingsRead(RawDataSettingsBase):
    id: int

# ==========================================
# TIME SERIES & EVENTS
# ==========================================

class TimeSeriesBase(SQLModel):
    install_id: Optional[int] = Field(default=None, foreign_key="fsm_install.id")
    monitor_id: Optional[int] = Field(default=None, foreign_key="fsm_monitor.id")
    variable: str  # Flow, Depth, Velocity, Rain
    data_type: str  # Raw, Processed, Model
    start_time: datetime
    end_time: datetime
    interval_minutes: int
    filename: Optional[str] = None
    unit: Optional[str] = Field(default=None)

class TimeSeries(TimeSeriesBase, table=True):
    __tablename__ = "fsm_timeseries"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    monitor: Optional[Monitor] = Relationship(back_populates="timeseries")
    install: Optional[Install] = Relationship(back_populates="timeseries")

# NOTE: Event table removed - FsmEvent is the canonical event table
# class EventBase(SQLModel):
#     install_id: int = Field(foreign_key="fsm_install.id")
#     event_type: str  # Storm, DryDay, DW
#     start_time: datetime
#     end_time: datetime
#     label: Optional[str] = None
#
# class Event(EventBase, table=True):
#     __tablename__ = "fsm_event"
#     id: Optional[int] = Field(default=None, primary_key=True)

# ==========================================
# QA - NOTES & ATTACHMENTS
# ==========================================

class NoteBase(SQLModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int
    project_id: Optional[int] = None
    site_id: Optional[int] = None
    monitor_id: Optional[int] = None
    install_id: Optional[int] = None

class Note(NoteBase, table=True):
    __tablename__ = "fsm_note"
    id: Optional[int] = Field(default=None, primary_key=True)

class NoteCreate(NoteBase):
    pass

class NoteRead(NoteBase):
    id: int

class AttachmentBase(SQLModel):
    filename: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int
    note_id: Optional[int] = None
    project_id: Optional[int] = None
    site_id: Optional[int] = None
    monitor_id: Optional[int] = None
    install_id: Optional[int] = None

class Attachment(AttachmentBase, table=True):
    __tablename__ = "fsm_attachment"
    id: Optional[int] = Field(default=None, primary_key=True)

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentRead(AttachmentBase):
    id: int

# ==========================================
# FSM EVENT (Project-level rainfall events)
# ==========================================

class FsmEventBase(SQLModel):
    start_time: datetime
    end_time: datetime
    event_type: str = "Storm"  # Storm, No Event, Dry Day
    total_rainfall_mm: Optional[float] = None
    max_intensity_mm_hr: Optional[float] = None
    preceding_dry_hours: Optional[float] = None
    
    # Review fields
    reviewed: bool = False
    review_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class FsmEvent(FsmEventBase, table=True):
    __tablename__ = "fsm_event"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="fsm_project.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class FsmEventCreate(SQLModel):
    project_id: int
    start_time: datetime
    end_time: datetime
    event_type: str = "Storm"
    total_rainfall_mm: Optional[float] = None
    max_intensity_mm_hr: Optional[float] = None
    preceding_dry_hours: Optional[float] = None


class FsmEventUpdate(SQLModel):
    event_type: Optional[str] = None
    reviewed: Optional[bool] = None
    review_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class FsmEventRead(FsmEventBase):
    id: int
    project_id: int
    created_at: datetime
