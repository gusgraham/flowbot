"""
Verification Module Domain Models

This module contains all SQLModel definitions for the verification workflow,
including events, trace sets, monitor traces, verification runs, and metrics.
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON
from sqlalchemy import Column, Integer, ForeignKey
from enum import Enum


# ============================================
# ENUMS
# ============================================

class EventType(str, Enum):
    STORM = "STORM"
    DWF = "DWF"


class RunStatus(str, Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"
    SUPERSEDED = "SUPERSEDED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    MARGINAL = "MARGINAL"
    NOT_VERIFIED = "NOT_VERIFIED"
    PENDING = "PENDING"


class ScoreBand(str, Enum):
    OK = "OK"
    FAIR = "FAIR"
    NO = "NO"
    NA = "NA"


class SeriesType(str, Enum):
    OBS_FLOW = "obs_flow"
    PRED_FLOW = "pred_flow"
    OBS_DEPTH = "obs_depth"
    PRED_DEPTH = "pred_depth"
    OBS_VELOCITY = "obs_velocity"
    PRED_VELOCITY = "pred_velocity"


# ============================================
# VERIFICATION EVENT
# ============================================

class VerificationEventBase(SQLModel):
    name: str = Field(index=True)
    event_type: str = Field(default="STORM")  # STORM or DWF
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class VerificationEvent(VerificationEventBase, table=True):
    __tablename__ = "verificationevent"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="verificationproject.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    trace_sets: List["TraceSet"] = Relationship(back_populates="event")


class VerificationEventCreate(SQLModel):
    name: str
    event_type: str = "STORM"
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class VerificationEventRead(VerificationEventCreate):
    id: int
    project_id: int
    created_at: datetime


# ============================================
# VERIFICATION FLOW MONITOR
# ============================================

class VerificationFlowMonitorBase(SQLModel):
    name: str = Field(index=True)
    icm_node_reference: Optional[str] = None
    is_critical: bool = Field(default=False)
    is_surcharged: bool = Field(default=False)


class VerificationFlowMonitor(VerificationFlowMonitorBase, table=True):
    __tablename__ = "verificationflowmonitor"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="verificationproject.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    monitor_traces: List["MonitorTraceVersion"] = Relationship(back_populates="monitor")


class VerificationFlowMonitorCreate(SQLModel):
    name: str
    icm_node_reference: Optional[str] = None
    is_critical: bool = False
    is_surcharged: bool = False


class VerificationFlowMonitorRead(VerificationFlowMonitorCreate):
    id: int
    project_id: int
    created_at: datetime


class VerificationFlowMonitorUpdate(SQLModel):
    name: Optional[str] = None
    icm_node_reference: Optional[str] = None
    is_critical: Optional[bool] = None
    is_surcharged: Optional[bool] = None


# ============================================
# TRACE SET (represents one ICM export file import)
# ============================================

class TraceSetBase(SQLModel):
    name: str = Field(index=True)  # e.g., "ICM Run v3" or filename
    source_file: Optional[str] = None


class TraceSet(TraceSetBase, table=True):
    __tablename__ = "traceset"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="verificationevent.id", index=True)
    imported_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    event: Optional[VerificationEvent] = Relationship(back_populates="trace_sets")
    monitor_traces: List["MonitorTraceVersion"] = Relationship(back_populates="trace_set")


class TraceSetCreate(SQLModel):
    name: str
    source_file: Optional[str] = None


class TraceSetRead(TraceSetCreate):
    id: int
    event_id: int
    imported_at: datetime


# ============================================
# MONITOR TRACE VERSION (one monitor's data from one trace set)
# ============================================

class MonitorTraceVersionBase(SQLModel):
    timestep_minutes: int = Field(default=2)
    upstream_end: bool = Field(default=False)
    obs_location_name: Optional[str] = None
    pred_location_name: Optional[str] = None


class MonitorTraceVersion(MonitorTraceVersionBase, table=True):
    __tablename__ = "monitortraceversion"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    trace_set_id: int = Field(foreign_key="traceset.id", index=True)
    monitor_id: int = Field(foreign_key="verificationflowmonitor.id", index=True)
    
    # Relationships
    trace_set: Optional[TraceSet] = Relationship(back_populates="monitor_traces")
    monitor: Optional[VerificationFlowMonitor] = Relationship(back_populates="monitor_traces")
    time_series: List["VerificationTimeSeries"] = Relationship(back_populates="monitor_trace")
    runs: List["VerificationRun"] = Relationship(back_populates="monitor_trace")


class MonitorTraceVersionRead(MonitorTraceVersionBase):
    id: int
    trace_set_id: int
    monitor_id: int


# ============================================
# VERIFICATION TIME SERIES (parquet storage reference)
# ============================================

class VerificationTimeSeriesBase(SQLModel):
    series_type: str  # obs_flow, pred_flow, obs_depth, pred_depth, etc.
    parquet_path: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    record_count: Optional[int] = None


class VerificationTimeSeries(VerificationTimeSeriesBase, table=True):
    __tablename__ = "verificationtimeseries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_trace_id: int = Field(foreign_key="monitortraceversion.id", index=True)
    
    # Relationships
    monitor_trace: Optional[MonitorTraceVersion] = Relationship(back_populates="time_series")


class VerificationTimeSeriesRead(VerificationTimeSeriesBase):
    id: int
    monitor_trace_id: int


# ============================================
# TOLERANCE SET (configurable thresholds)
# ============================================

class ToleranceSetBase(SQLModel):
    name: str = Field(index=True)
    event_type: str = Field(default="STORM")  # STORM or DWF
    for_critical: bool = Field(default=False)
    for_surcharged: bool = Field(default=False)
    
    # Depth tolerances
    depth_time_tolerance_hrs: float = Field(default=0.5)
    depth_peak_tolerance_pct: float = Field(default=10.0)
    depth_peak_tolerance_abs_m: float = Field(default=0.1)
    depth_peak_surcharged_upper_m: float = Field(default=0.5)  # +0.5m for surcharged
    depth_peak_surcharged_lower_m: float = Field(default=0.1)  # -0.1m for surcharged
    
    # Flow tolerances
    flow_nse_threshold: float = Field(default=0.5)
    flow_time_tolerance_hrs: float = Field(default=0.5)
    flow_peak_tolerance_upper_pct: float = Field(default=25.0)  # +25% for general
    flow_peak_tolerance_lower_pct: float = Field(default=15.0)  # -15% for general
    flow_volume_tolerance_upper_pct: float = Field(default=20.0)
    flow_volume_tolerance_lower_pct: float = Field(default=10.0)


class ToleranceSet(ToleranceSetBase, table=True):
    __tablename__ = "toleranceset"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="verificationproject.id", index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class ToleranceSetCreate(SQLModel):
    name: str
    event_type: str = "STORM"
    for_critical: bool = False
    for_surcharged: bool = False
    depth_time_tolerance_hrs: float = 0.5
    depth_peak_tolerance_pct: float = 10.0
    depth_peak_tolerance_abs_m: float = 0.1
    depth_peak_surcharged_upper_m: float = 0.5
    depth_peak_surcharged_lower_m: float = 0.1
    flow_nse_threshold: float = 0.5
    flow_time_tolerance_hrs: float = 0.5
    flow_peak_tolerance_upper_pct: float = 25.0
    flow_peak_tolerance_lower_pct: float = 15.0
    flow_volume_tolerance_upper_pct: float = 20.0
    flow_volume_tolerance_lower_pct: float = 10.0


class ToleranceSetRead(ToleranceSetCreate):
    id: int
    project_id: int
    created_at: datetime


class ToleranceSetUpdate(SQLModel):
    name: Optional[str] = None
    depth_time_tolerance_hrs: Optional[float] = None
    depth_peak_tolerance_pct: Optional[float] = None
    depth_peak_tolerance_abs_m: Optional[float] = None
    flow_nse_threshold: Optional[float] = None
    flow_time_tolerance_hrs: Optional[float] = None
    flow_peak_tolerance_upper_pct: Optional[float] = None
    flow_peak_tolerance_lower_pct: Optional[float] = None
    flow_volume_tolerance_upper_pct: Optional[float] = None
    flow_volume_tolerance_lower_pct: Optional[float] = None


# ============================================
# VERIFICATION RUN
# ============================================

class VerificationRunBase(SQLModel):
    status: str = Field(default="DRAFT")  # DRAFT, FINAL, SUPERSEDED
    is_final_for_monitor_event: bool = Field(default=False)
    
    # Aggregate scores
    overall_flow_score: Optional[float] = None
    overall_depth_score: Optional[float] = None
    overall_status: Optional[str] = None  # VERIFIED, MARGINAL, NOT_VERIFIED, PENDING
    
    # Display metrics (not for scoring)
    nse: Optional[float] = None
    kge: Optional[float] = None  # Kling-Gupta Efficiency
    cv_obs: Optional[float] = None  # Coefficient of Variation
    
    # Analysis Settings (Persisted)
    analysis_settings: Optional[dict] = Field(default=None, sa_type=JSON)


class VerificationRun(VerificationRunBase, table=True):
    __tablename__ = "verificationrun"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    monitor_trace_id: int = Field(foreign_key="monitortraceversion.id", index=True)
    tolerance_set_id: Optional[int] = Field(default=None, foreign_key="toleranceset.id")
    created_at: datetime = Field(default_factory=datetime.now)
    finalized_at: Optional[datetime] = None
    
    # Relationships
    monitor_trace: Optional[MonitorTraceVersion] = Relationship(back_populates="runs")
    metrics: List["VerificationMetric"] = Relationship(back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    adjustments: List["ManualAdjustment"] = Relationship(back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class VerificationRunCreate(SQLModel):
    tolerance_set_id: Optional[int] = None


class VerificationRunRead(VerificationRunBase):
    id: int
    monitor_trace_id: int
    tolerance_set_id: Optional[int]
    created_at: datetime
    finalized_at: Optional[datetime]


class VerificationRunUpdate(SQLModel):
    status: Optional[str] = None
    is_final_for_monitor_event: Optional[bool] = None


# ============================================
# VERIFICATION METRIC
# ============================================

class VerificationMetricBase(SQLModel):
    parameter: str  # FLOW, DEPTH, VOLUME, SHAPE
    metric_name: str  # nse, peak_time_diff_hrs, peak_diff_pct, volume_diff_pct
    value: float
    score_band: Optional[str] = None  # OK, FAIR, NO, NA
    score_points: Optional[int] = None


class VerificationMetric(VerificationMetricBase, table=True):
    __tablename__ = "verificationmetric"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(sa_column=Column(Integer, ForeignKey("verificationrun.id", ondelete="CASCADE"), index=True))
    
    # Relationships
    run: Optional[VerificationRun] = Relationship(back_populates="metrics")


class VerificationMetricRead(VerificationMetricBase):
    id: int
    run_id: int


# ============================================
# MANUAL ADJUSTMENT
# ============================================

class ManualAdjustmentBase(SQLModel):
    adjustment_type: str  # peak_override, exclusion
    parameter: str  # FLOW, DEPTH
    details: Optional[dict] = Field(default=None, sa_type=JSON)
    reason: Optional[str] = None


class ManualAdjustment(ManualAdjustmentBase, table=True):
    __tablename__ = "manualadjustment"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(sa_column=Column(Integer, ForeignKey("verificationrun.id", ondelete="CASCADE"), index=True))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    run: Optional[VerificationRun] = Relationship(back_populates="adjustments")


class ManualAdjustmentCreate(SQLModel):
    adjustment_type: str
    parameter: str
    details: Optional[dict] = None
    reason: Optional[str] = None


class ManualAdjustmentRead(ManualAdjustmentBase):
    id: int
    run_id: int
    created_at: datetime
