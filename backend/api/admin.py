"""
Admin API Routes - Cost Tracking & Billing
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from domain.admin import (
    CostCentre, CostCentreCreate, CostCentreRead, CostCentreUpdate,
    ModuleWeight, ModuleWeightRead, ModuleWeightUpdate,
    BudgetConfig, BudgetConfigCreate, BudgetConfigRead, BudgetConfigUpdate,
    MonthlyInvoice, MonthlyInvoiceRead,
)
from domain.auth import User, UserRead
from api.deps import get_current_active_superuser

router = APIRouter()


# ==========================================
# COST CENTRES
# ==========================================

@router.get("/cost-centres", response_model=List[CostCentreRead])
def list_cost_centres(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """List all cost centres."""
    return session.exec(select(CostCentre)).all()


@router.get("/cost-centres/{cost_centre_id}", response_model=CostCentreRead)
def get_cost_centre(
    cost_centre_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get a specific cost centre."""
    cost_centre = session.get(CostCentre, cost_centre_id)
    if not cost_centre:
        raise HTTPException(status_code=404, detail="Cost centre not found")
    return cost_centre


@router.post("/cost-centres", response_model=CostCentreRead)
def create_cost_centre(
    data: CostCentreCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Create a new cost centre."""
    # Check for duplicate code
    existing = session.exec(select(CostCentre).where(CostCentre.code == data.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cost centre code already exists")
    
    cost_centre = CostCentre(**data.model_dump())
    session.add(cost_centre)
    session.commit()
    session.refresh(cost_centre)
    return cost_centre


@router.put("/cost-centres/{cost_centre_id}", response_model=CostCentreRead)
def update_cost_centre(
    cost_centre_id: int,
    data: CostCentreUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Update a cost centre."""
    cost_centre = session.get(CostCentre, cost_centre_id)
    if not cost_centre:
        raise HTTPException(status_code=404, detail="Cost centre not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cost_centre, key, value)
    
    session.add(cost_centre)
    session.commit()
    session.refresh(cost_centre)
    return cost_centre


@router.delete("/cost-centres/{cost_centre_id}")
def delete_cost_centre(
    cost_centre_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Delete a cost centre."""
    cost_centre = session.get(CostCentre, cost_centre_id)
    if not cost_centre:
        raise HTTPException(status_code=404, detail="Cost centre not found")
    
    # Check if any users are assigned
    users = session.exec(select(User).where(User.cost_centre_id == cost_centre_id)).all()
    if users:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete: {len(users)} user(s) are assigned to this cost centre"
        )
    
    session.delete(cost_centre)
    session.commit()
    return {"status": "success", "message": "Cost centre deleted"}


@router.get("/cost-centres/{cost_centre_id}/users", response_model=List[UserRead])
def get_cost_centre_users(
    cost_centre_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get all users assigned to a cost centre."""
    cost_centre = session.get(CostCentre, cost_centre_id)
    if not cost_centre:
        raise HTTPException(status_code=404, detail="Cost centre not found")
    
    users = session.exec(select(User).where(User.cost_centre_id == cost_centre_id)).all()
    return users


# ==========================================
# MODULE WEIGHTS
# ==========================================

@router.get("/module-weights", response_model=List[ModuleWeightRead])
def list_module_weights(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """List all module weights."""
    return session.exec(select(ModuleWeight)).all()


@router.put("/module-weights/{module_weight_id}", response_model=ModuleWeightRead)
def update_module_weight(
    module_weight_id: int,
    data: ModuleWeightUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Update a module weight."""
    weight = session.get(ModuleWeight, module_weight_id)
    if not weight:
        raise HTTPException(status_code=404, detail="Module weight not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(weight, key, value)
    
    session.add(weight)
    session.commit()
    session.refresh(weight)
    return weight


# ==========================================
# BUDGET CONFIG
# ==========================================

@router.get("/budgets", response_model=List[BudgetConfigRead])
def list_budgets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """List all budget configurations."""
    return session.exec(select(BudgetConfig).order_by(BudgetConfig.effective_date.desc())).all()


@router.put("/budgets/{budget_id}", response_model=BudgetConfig)
def update_budget(
    budget_id: int,
    updates: BudgetConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Update a budget configuration."""
    budget = session.get(BudgetConfig, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Update fields only if provided
    if updates.effective_date is not None:
        budget.effective_date = updates.effective_date
    if updates.hosting_budget is not None:
        budget.hosting_budget = updates.hosting_budget
    if updates.development_budget is not None:
        budget.development_budget = updates.development_budget
    if updates.storage_weight_pct is not None:
        budget.storage_weight_pct = updates.storage_weight_pct
    if updates.notes is not None:
        budget.notes = updates.notes
    
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Delete a budget configuration."""
    budget = session.get(BudgetConfig, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    session.delete(budget)
    session.commit()
    return {"message": "Budget deleted"}


@router.get("/budgets/current", response_model=Optional[BudgetConfigRead])
def get_current_budget(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get the currently active budget (most recent by effective date)."""
    from datetime import date
    budget = session.exec(
        select(BudgetConfig)
        .where(BudgetConfig.effective_date <= date.today())
        .order_by(BudgetConfig.effective_date.desc())
    ).first()
    return budget


@router.post("/budgets", response_model=BudgetConfigRead)
def create_budget(
    data: BudgetConfigCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Create a new budget configuration."""
    budget = BudgetConfig(**data.model_dump())
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetConfigRead)
def update_budget(
    budget_id: int,
    data: BudgetConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Update a budget configuration."""
    budget = session.get(BudgetConfig, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(budget, key, value)
    
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


# ==========================================
# INVOICES
# ==========================================

@router.get("/invoices", response_model=List[MonthlyInvoiceRead])
def list_invoices(
    cost_centre_id: Optional[int] = None,
    year_month: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """List invoices with optional filters."""
    query = select(MonthlyInvoice)
    if cost_centre_id:
        query = query.where(MonthlyInvoice.cost_centre_id == cost_centre_id)
    if year_month:
        query = query.where(MonthlyInvoice.year_month == year_month)
    query = query.order_by(MonthlyInvoice.year_month.desc())
    return session.exec(query).all()


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Download invoice as PDF."""
    from services.pdf_invoice import generate_invoice_pdf
    from fastapi.responses import StreamingResponse
    import io
    
    invoice = session.get(MonthlyInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    cost_centre = session.get(CostCentre, invoice.cost_centre_id)
    # Handle deleted/missing cost centre gracefully-ish or fail
    if not cost_centre:
         # Create dummy for display if needed, or raise
         raise HTTPException(status_code=404, detail="Cost Centre for this invoice not found")
         
    pdf_bytes = generate_invoice_pdf(invoice, cost_centre)
    
    filename = f"Invoice_{invoice.year_month}_{cost_centre.code}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/invoices/{invoice_id}", response_model=MonthlyInvoiceRead)
def get_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get a specific invoice."""
    invoice = session.get(MonthlyInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/invoices/generate")
def generate_invoices_endpoint(
    year_month: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Generate invoices for a specific month."""
    from services.invoicing import generate_invoices
    
    # Validate format
    try:
        parts = year_month.split("-")
        if len(parts) != 2:
            raise ValueError()
        year, month = int(parts[0]), int(parts[1])
        if month < 1 or month > 12:
            raise ValueError()
    except:
        raise HTTPException(status_code=400, detail="Invalid year_month format (use YYYY-MM)")
    
    try:
        invoices = generate_invoices(year_month)
        return {
            "message": f"Generated {len(invoices)} invoices for {year_month}",
            "invoices": [
                {
                    "id": inv.id,
                    "cost_centre_id": inv.cost_centre_id,
                    "total_cost": inv.total_cost,
                    "share_pct": inv.share_pct
                }
                for inv in invoices
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# USAGE LOGS & STATISTICS
# ==========================================

from datetime import datetime, date
from domain.admin import UsageLog
from sqlalchemy import func

@router.get("/usage/summary")
def get_usage_summary(
    year_month: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get usage summary for a month, grouped by module and cost centre."""
    from sqlalchemy import text
    
    # Default to current month
    if not year_month:
        year_month = date.today().strftime("%Y-%m")
    
    # Parse year-month
    try:
        year, month = map(int, year_month.split("-"))
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
    except:
        raise HTTPException(status_code=400, detail="Invalid year_month format (use YYYY-MM)")
    
    # Get usage by module
    usage_by_module = session.exec(
        select(
            UsageLog.module,
            func.count(UsageLog.id).label("request_count"),
            func.sum(UsageLog.weight).label("weighted_total")
        )
        .where(UsageLog.timestamp >= start_date)
        .where(UsageLog.timestamp < end_date)
        .group_by(UsageLog.module)
    ).all()
    
    # Get usage by cost centre
    usage_by_cost_centre = session.exec(
        select(
            CostCentre.name,
            CostCentre.code,
            func.count(UsageLog.id).label("request_count"),
            func.sum(UsageLog.weight).label("weighted_total")
        )
        .join(User, User.id == UsageLog.user_id)
        .join(CostCentre, CostCentre.id == User.cost_centre_id, isouter=True)
        .where(UsageLog.timestamp >= start_date)
        .where(UsageLog.timestamp < end_date)
        .group_by(CostCentre.id)
    ).all()
    
    # Total weighted requests
    total = session.exec(
        select(func.sum(UsageLog.weight))
        .where(UsageLog.timestamp >= start_date)
        .where(UsageLog.timestamp < end_date)
    ).first() or 0
    
    return {
        "year_month": year_month,
        "total_weighted_requests": total,
        "by_module": [
            {"module": r[0], "request_count": r[1], "weighted_total": r[2]}
            for r in usage_by_module
        ],
        "by_cost_centre": [
            {
                "cost_centre_name": r[0] or "Unassigned",
                "cost_centre_code": r[1] or "N/A",
                "request_count": r[2],
                "weighted_total": r[3]
            }
            for r in usage_by_cost_centre
        ]
    }


@router.get("/usage/recent")
def get_recent_usage(
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get recent usage logs for debugging/monitoring."""
    logs = session.exec(
        select(UsageLog)
        .order_by(UsageLog.timestamp.desc())
        .limit(limit)
    ).all()
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "module": log.module,
            "weight": log.weight,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]


@router.get("/usage/count")
def get_usage_count(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get total usage log count (for monitoring that logging is working)."""
    count = session.exec(select(func.count(UsageLog.id))).first()
    return {"total_logs": count or 0}


# ==========================================
# STORAGE
# ==========================================

from domain.admin import StorageSnapshot
from services.storage import create_storage_snapshots, get_storage_summary

@router.get("/storage/summary")
def get_storage_summary_endpoint(
    snapshot_date: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get storage summary for a specific date or most recent."""
    parsed_date = None
    if snapshot_date:
        try:
            parsed_date = date.fromisoformat(snapshot_date)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    
    return get_storage_summary(session, parsed_date)


@router.post("/storage/snapshot")
def create_storage_snapshot_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Create a new storage snapshot for today."""
    snapshots = create_storage_snapshots(date.today())
    total_bytes = sum(s.size_bytes for s in snapshots)
    return {
        "message": f"Created {len(snapshots)} snapshots",
        "snapshot_date": date.today().isoformat(),
        "total_bytes": total_bytes,
        "project_count": len(snapshots)
    }


@router.get("/storage/snapshots")
def list_storage_snapshots(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """List all unique snapshot dates."""
    from sqlalchemy import distinct
    dates = session.exec(
        select(distinct(StorageSnapshot.snapshot_date))
        .order_by(StorageSnapshot.snapshot_date.desc())
    ).all()
    return {"snapshot_dates": [d.isoformat() for d in dates]}


@router.get("/storage/by-project")
def get_storage_by_project(
    module: Optional[str] = None,
    snapshot_date: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    """Get storage breakdown by project."""
    query = select(StorageSnapshot)
    
    if snapshot_date:
        try:
            parsed_date = date.fromisoformat(snapshot_date)
            query = query.where(StorageSnapshot.snapshot_date == parsed_date)
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        # Get most recent date
        latest = session.exec(
            select(StorageSnapshot.snapshot_date)
            .order_by(StorageSnapshot.snapshot_date.desc())
            .limit(1)
        ).first()
        if latest:
            query = query.where(StorageSnapshot.snapshot_date == latest)
    
    if module:
        query = query.where(StorageSnapshot.module == module)
    
    query = query.order_by(StorageSnapshot.size_bytes.desc())
    
    snapshots = session.exec(query).all()
    return [
        {
            "project_id": s.project_id,
            "module": s.module,
            "user_id": s.user_id,
            "size_bytes": s.size_bytes,
            "size_mb": round(s.size_bytes / (1024 * 1024), 2),
            "snapshot_date": s.snapshot_date.isoformat()
        }
        for s in snapshots
    ]

