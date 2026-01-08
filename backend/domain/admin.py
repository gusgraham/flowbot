"""
Admin Domain Models - Cost Tracking & Billing
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from domain.auth import User


# ==========================================
# COST CENTRE
# ==========================================

class CostCentreBase(SQLModel):
    name: str = Field(index=True)
    code: str = Field(index=True, unique=True)  # e.g., "ENG-001"
    is_overhead: bool = False  # If true, costs are distributed pro-rata to other centres


class CostCentre(CostCentreBase, table=True):
    __tablename__ = "admin_cost_centre"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationship to users
    users: List["User"] = Relationship(back_populates="cost_centre")


class CostCentreCreate(CostCentreBase):
    pass


class CostCentreRead(CostCentreBase):
    id: int
    created_at: datetime


class CostCentreUpdate(SQLModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_overhead: Optional[bool] = None


# ==========================================
# MODULE WEIGHT (for usage tracking)
# ==========================================

class ModuleWeightBase(SQLModel):
    module: str = Field(index=True, unique=True)  # FSM, FSA, WQ, VER, SSD
    weight: float = 1.0
    description: Optional[str] = None


class ModuleWeight(ModuleWeightBase, table=True):
    __tablename__ = "admin_module_weight"
    
    id: Optional[int] = Field(default=None, primary_key=True)


class ModuleWeightRead(ModuleWeightBase):
    id: int


class ModuleWeightUpdate(SQLModel):
    weight: Optional[float] = None
    description: Optional[str] = None


# ==========================================
# USAGE LOG
# ==========================================

class UsageLog(SQLModel, table=True):
    __tablename__ = "admin_usage_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="auth_user.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    module: str = Field(index=True)  # FSM, FSA, WQ, VER, SSD
    weight: float = 1.0  # Captured at log time


# ==========================================
# STORAGE SNAPSHOT
# ==========================================

class StorageSnapshot(SQLModel, table=True):
    __tablename__ = "admin_storage_snapshot"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="auth_user.id", index=True)  # Project owner
    project_id: int = Field(index=True)  # Generic FK (can be any module's project)
    module: str = Field(index=True)  # FSM, FSA, WQ, VER, SSD
    snapshot_date: date = Field(index=True)
    size_bytes: int = 0


# ==========================================
# BUDGET CONFIG
# ==========================================

class BudgetConfigBase(SQLModel):
    effective_date: date
    hosting_budget: float  # Monthly £
    development_budget: float  # Monthly £
    storage_weight_pct: int = 30  # % of allocation based on storage
    notes: Optional[str] = None


class BudgetConfig(BudgetConfigBase, table=True):
    __tablename__ = "admin_budget_config"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class BudgetConfigCreate(BudgetConfigBase):
    pass


class BudgetConfigRead(BudgetConfigBase):
    id: int
    created_at: datetime


class BudgetConfigUpdate(SQLModel):
    effective_date: Optional[date] = None
    hosting_budget: Optional[float] = None
    development_budget: Optional[float] = None
    storage_weight_pct: Optional[int] = None
    notes: Optional[str] = None


# ==========================================
# MONTHLY INVOICE
# ==========================================

class MonthlyInvoice(SQLModel, table=True):
    __tablename__ = "admin_monthly_invoice"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cost_centre_id: int = Field(foreign_key="admin_cost_centre.id", index=True)
    year_month: str = Field(index=True)  # "2026-01"
    total_budget: float  # Total FlowBot budget that month
    share_pct: float  # This centre's % share
    utilization_cost: float
    storage_cost: float
    total_cost: float
    details_json: Optional[str] = None  # JSON breakdown by user/module
    generated_at: datetime = Field(default_factory=datetime.now)


class MonthlyInvoiceRead(SQLModel):
    id: int
    cost_centre_id: int
    year_month: str
    total_budget: float
    share_pct: float
    utilization_cost: float
    storage_cost: float
    total_cost: float
    details_json: Optional[str]
    generated_at: datetime

