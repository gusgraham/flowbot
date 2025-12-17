"""
Interim Review Domain Models
Models for managing interim review workflow in FSM projects.
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class InterimStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    LOCKED = "locked"


class IssueType(str, Enum):
    ANOMALY = "anomaly"
    SUSPECT = "suspect"
    GAP = "gap"
    CALIBRATION = "calibration"
    OTHER = "other"


# ==========================================
# INTERIM
# ==========================================

class InterimBase(SQLModel):
    start_date: datetime
    end_date: datetime
    status: str = Field(default=InterimStatus.DRAFT)


class Interim(InterimBase, table=True):
    __tablename__ = "fsm_interim"
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="fsm_project.id", index=True)
    revision_of: Optional[int] = Field(default=None, foreign_key="fsm_interim.id")
    created_at: datetime = Field(default_factory=datetime.now)
    locked_at: Optional[datetime] = None
    
    # Relationships
    reviews: List["InterimReview"] = Relationship(
        back_populates="interim",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class InterimCreate(SQLModel):
    project_id: int
    start_date: datetime
    end_date: datetime


class InterimUpdate(SQLModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class InterimRead(InterimBase):
    id: int
    project_id: int
    revision_of: Optional[int] = None
    created_at: datetime
    locked_at: Optional[datetime] = None
    review_count: Optional[int] = None
    reviews_complete: Optional[int] = None


# ==========================================
# INTERIM REVIEW (per install)
# ==========================================

class InterimReviewBase(SQLModel):
    install_id: int = Field(foreign_key="fsm_install.id", index=True)
    install_type: str = "Flow Monitor"
    
    # Stage 1: Data Import
    data_coverage_pct: Optional[float] = None
    gaps_json: Optional[str] = None  # JSON array of gap periods
    data_import_acknowledged: bool = False
    data_import_notes: Optional[str] = None
    data_import_reviewer: Optional[str] = None
    data_import_reviewed_at: Optional[datetime] = None
    
    # Stage 2: Classification
    classification_complete: bool = False
    classification_comment: Optional[str] = None
    classification_reviewer: Optional[str] = None
    classification_reviewed_at: Optional[datetime] = None
    
    # Stage 3: Events
    events_complete: bool = False
    events_comment: Optional[str] = None
    events_reviewer: Optional[str] = None
    events_reviewed_at: Optional[datetime] = None
    
    # Stage 4: Processed Review
    review_complete: bool = False
    review_comment: Optional[str] = None
    review_reviewer: Optional[str] = None
    review_reviewed_at: Optional[datetime] = None


class InterimReview(InterimReviewBase, table=True):
    __tablename__ = "fsm_interimreview"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interim_id: int = Field(foreign_key="fsm_interim.id", index=True)
    
    # Relationships
    interim: Optional[Interim] = Relationship(back_populates="reviews")
    annotations: List["ReviewAnnotation"] = Relationship(
        back_populates="interim_review",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    classifications: List["DailyClassification"] = Relationship(
        back_populates="interim_review",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class InterimReviewCreate(SQLModel):
    interim_id: int
    install_id: int
    monitor_id: Optional[int] = None
    install_type: str = "Flow Monitor"


class InterimReviewRead(InterimReviewBase):
    id: int
    interim_id: int
    annotation_count: Optional[int] = None


class StageSignoff(SQLModel):
    """Schema for signing off a review stage"""
    comment: Optional[str] = None
    reviewer: str


# ==========================================
# REVIEW ANNOTATION
# ==========================================

class ReviewAnnotationBase(SQLModel):
    variable: str  # Depth, Velocity, Flow, Rain, Pump_State
    start_time: datetime
    end_time: datetime
    issue_type: str = Field(default=IssueType.OTHER)
    description: Optional[str] = None


class ReviewAnnotation(ReviewAnnotationBase, table=True):
    __tablename__ = "fsm_reviewannotation"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interim_review_id: int = Field(foreign_key="fsm_interimreview.id", index=True)
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationship
    interim_review: Optional[InterimReview] = Relationship(back_populates="annotations")


class ReviewAnnotationCreate(ReviewAnnotationBase):
    interim_review_id: int
    created_by: Optional[str] = None


class ReviewAnnotationRead(ReviewAnnotationBase):
    id: int
    interim_review_id: int
    created_by: Optional[str] = None
    created_at: datetime


# ==========================================
# DAILY CLASSIFICATION (ML output)
# ==========================================

class DailyClassificationBase(SQLModel):
    date: datetime
    ml_classification: Optional[str] = None  # Null for pump loggers (no ML model)
    ml_confidence: Optional[float] = None
    manual_classification: Optional[str] = None
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    override_at: Optional[datetime] = None


class DailyClassification(DailyClassificationBase, table=True):
    __tablename__ = "fsm_dailyclassification"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interim_review_id: int = Field(foreign_key="fsm_interimreview.id", index=True)
    
    # Relationship
    interim_review: Optional[InterimReview] = Relationship(back_populates="classifications")


class DailyClassificationCreate(DailyClassificationBase):
    interim_review_id: int


class DailyClassificationRead(DailyClassificationBase):
    id: int
    interim_review_id: int


class ClassificationOverride(SQLModel):
    """Schema for overriding a classification"""
    manual_classification: str
    override_reason: Optional[str] = None
    override_by: str
