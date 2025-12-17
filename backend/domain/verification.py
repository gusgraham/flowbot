from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# Import extended verification models
from domain.verification_models import (
    VerificationEvent, VerificationEventCreate, VerificationEventRead,
    VerificationFlowMonitor, VerificationFlowMonitorCreate, VerificationFlowMonitorRead, VerificationFlowMonitorUpdate,
    TraceSet, TraceSetCreate, TraceSetRead,
    MonitorTraceVersion, MonitorTraceVersionRead,
    VerificationTimeSeries, VerificationTimeSeriesRead,
    ToleranceSet, ToleranceSetCreate, ToleranceSetRead, ToleranceSetUpdate,
    VerificationRun, VerificationRunCreate, VerificationRunRead, VerificationRunUpdate,
    VerificationMetric, VerificationMetricRead,
    ManualAdjustment, ManualAdjustmentCreate, ManualAdjustmentRead,
    VerificationFullPeriodImport, VerificationFullPeriodImportCreate, VerificationFullPeriodImportRead, VerificationFullPeriodImportUpdate,
    VerificationFullPeriodMonitor, VerificationFullPeriodMonitorRead, VerificationDWFProfile,
    VerificationDryDay, VerificationDryDayRead, VerificationDryDayUpdate,
    EventType, RunStatus, VerificationStatus, ScoreBand, SeriesType
)

class VerificationProjectBase(SQLModel):
    name: str = Field(index=True)
    job_number: str = Field(index=True)
    client: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class VerificationProjectCollaborator(SQLModel, table=True):
    __tablename__ = "ver_projectcollaborator"
    """Link table for Verification project collaborators (many-to-many)"""
    project_id: int = Field(foreign_key="ver_project.id", primary_key=True)
    user_id: int = Field(foreign_key="auth_user.id", primary_key=True)

class VerificationProject(VerificationProjectBase, table=True):
    __tablename__ = "ver_project"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="auth_user.id")
    
    # Collaborators (Many-to-Many)
    collaborators: List["User"] = Relationship(link_model=VerificationProjectCollaborator)
    
    # Child relationships
    events: List["VerificationEvent"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[VerificationEvent.project_id]"}
    )
    monitors: List["VerificationFlowMonitor"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[VerificationFlowMonitor.project_id]"}
    )
    tolerance_sets: List["ToleranceSet"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ToleranceSet.project_id]"}
    )

class VerificationProjectCreate(SQLModel):
    name: str
    job_number: str
    client: str
    model_name: Optional[str] = None
    description: Optional[str] = None

class VerificationProjectRead(VerificationProjectCreate):
    id: int
    owner_id: Optional[int]
    created_at: datetime
