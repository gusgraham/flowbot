"""
Invoice Generation Service

Generates monthly invoices for cost centres based on usage and storage data.
"""
import json
from datetime import datetime, date
from typing import Dict, List, Optional
from sqlmodel import Session, select
from sqlalchemy import func

from database import engine
from domain.admin import (
    CostCentre, BudgetConfig, MonthlyInvoice, UsageLog, StorageSnapshot
)
from domain.auth import User


def get_current_budget(session: Session, target_date: Optional[date] = None) -> Optional[BudgetConfig]:
    """Get the currently active budget configuration for a specific date (default: today)."""
    if target_date is None:
        target_date = date.today()
        
    return session.exec(
        select(BudgetConfig)
        .where(BudgetConfig.effective_date <= target_date)
        .order_by(BudgetConfig.effective_date.desc())
    ).first()

def calculate_usage_shares(session: Session, year_month: str) -> Dict[int, Dict]:
    """
    Calculate weighted usage shares for each cost centre.
    Returns: {cost_centre_id: {"weighted_total": float, "request_count": int, "by_module": {...}}}
    """
    # Parse year-month
    year, month = map(int, year_month.split("-"))
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Get usage by cost centre (including users assigned to each)
    shares = {}
    
    # Get all cost centres
    cost_centres = session.exec(select(CostCentre)).all()
    for cc in cost_centres:
        shares[cc.id] = {
            "name": cc.name,
            "code": cc.code,
            "is_overhead": cc.is_overhead,
            "weighted_total": 0.0,
            "request_count": 0,
            "by_module": {}
        }
    
    # Add "unassigned" pseudo cost centre (id = None becomes 0)
    shares[0] = {
        "name": "Unassigned",
        "code": "N/A",
        "is_overhead": True,  # Treat as overhead
        "weighted_total": 0.0,
        "request_count": 0,
        "by_module": {}
    }
    
    # Get all usage logs for the month, joined with user's cost centre
    usage_data = session.exec(
        select(
            User.cost_centre_id,
            UsageLog.module,
            func.count(UsageLog.id).label("count"),
            func.sum(UsageLog.weight).label("weighted")
        )
        .join(User, User.id == UsageLog.user_id)
        .where(UsageLog.timestamp >= start_date)
        .where(UsageLog.timestamp < end_date)
        .group_by(User.cost_centre_id, UsageLog.module)
    ).all()
    
    for row in usage_data:
        cc_id = row[0] or 0  # None becomes 0 (unassigned)
        module = row[1]
        count = row[2]
        weighted = row[3] or 0
        
        if cc_id not in shares:
            continue
        
        shares[cc_id]["weighted_total"] += weighted
        shares[cc_id]["request_count"] += count
        if module not in shares[cc_id]["by_module"]:
            shares[cc_id]["by_module"][module] = {"count": 0, "weighted": 0}
        shares[cc_id]["by_module"][module]["count"] += count
        shares[cc_id]["by_module"][module]["weighted"] += weighted
    
    return shares


def calculate_storage_shares(session: Session, year_month: str = None) -> Dict[int, Dict]:
    """
    Calculate storage shares based on the AVERAGE daily storage over the month.
    Returns: {cost_centre_id: {"total_bytes": float, "project_count": int}}
    """
    if year_month:
        year, month = map(int, year_month.split("-"))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    else:
        # Default to current month if not specified (legacy behavior)
        today = date.today()
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1)
        else:
            end_date = date(today.year, today.month + 1, 1)

    shares = {}
    
    # Get all cost centres
    cost_centres = session.exec(select(CostCentre)).all()
    for cc in cost_centres:
        shares[cc.id] = {
            "name": cc.name,
            "code": cc.code,
            "is_overhead": cc.is_overhead,
            "total_bytes": 0.0,
            "project_count": 0
        }
    
    # Unassigned placeholder
    shares[0] = {
        "name": "Unassigned",
        "code": "N/A",
        "is_overhead": True,
        "total_bytes": 0.0,
        "project_count": 0
    }
    
    # Get all snapshots for the month
    snapshots = session.exec(
        select(StorageSnapshot)
        .where(StorageSnapshot.snapshot_date >= start_date)
        .where(StorageSnapshot.snapshot_date < end_date)
    ).all()
    
    if not snapshots:
        return shares

    # Group by Cost Centre and Date to get specific daily totals
    # Then average those daily totals.
    
    # Structure: { date: { cc_id: total_bytes } }
    daily_totals: Dict[date, Dict[int, int]] = {}
    
    # Also track project count (use max seen in month? or average? Max is probably safer/fairer expectation)
    cc_project_counts: Dict[int, int] = {} 

    for s in snapshots:
        d = s.snapshot_date
        
        # Resolve owner to cost centre
        owner = session.get(User, s.user_id)
        cc_id = owner.cost_centre_id if owner else 0
        cc_id = cc_id or 0
        
        if d not in daily_totals:
            daily_totals[d] = {}
        
        if cc_id not in daily_totals[d]:
            daily_totals[d][cc_id] = 0
            
        daily_totals[d][cc_id] += s.size_bytes
        
        # Just track raw count of snapshots for project count metric (simplification)
        cc_project_counts[cc_id] = cc_project_counts.get(cc_id, 0) + 1

    # Now calculate average for each CC
    # Divisor is the number of days we successfully took snapshots (to be fair)
    num_days_with_data = len(daily_totals)
    
    if num_days_with_data == 0:
         return shares
         
    # Aggregate totals from daily_totals
    cc_grand_totals: Dict[int, float] = {}
    
    for day_data in daily_totals.values():
        for cc_id, bytes_val in day_data.items():
            cc_grand_totals[cc_id] = cc_grand_totals.get(cc_id, 0.0) + bytes_val
            
    # Compute averages
    for cc_id, grand_total in cc_grand_totals.items():
        if cc_id in shares:
            shares[cc_id]["total_bytes"] = grand_total / num_days_with_data
            # Approximate project count (total snapshots / days)
            shares[cc_id]["project_count"] = int(cc_project_counts.get(cc_id, 0) / num_days_with_data)

    return shares


def distribute_overhead(shares: Dict[int, float], overhead_ids: List[int]) -> Dict[int, float]:
    """
    Distribute overhead shares proportionally to non-overhead centres.
    """
    if not shares:
        return {}
    
    # Calculate totals
    overhead_total = sum(shares.get(oid, 0) for oid in overhead_ids)
    non_overhead_total = sum(v for k, v in shares.items() if k not in overhead_ids)
    
    if non_overhead_total == 0:
        # All usage is overhead - return as-is
        return shares
    
    # Redistribute
    result = {}
    for cc_id, value in shares.items():
        if cc_id in overhead_ids:
            result[cc_id] = 0  # Overhead gets zeroed out
        else:
            # Get proportion of non-overhead
            proportion = value / non_overhead_total if non_overhead_total > 0 else 0
            # Add proportional share of overhead
            result[cc_id] = value + (overhead_total * proportion)
    
    return result


def generate_invoices(year_month: str) -> List[MonthlyInvoice]:
    """
    Generate monthly invoices for all cost centres.
    
    This should be run at the end of a month to create invoices.
    """
    with Session(engine) as session:
        # Determine the end of the month for budget selection
        year, month = map(int, year_month.split("-"))
        if month == 12:
            end_of_month = date(year, 12, 31)
        else:
            # First day of next month minus 1 day
            next_month = date(year, month + 1, 1)
            end_of_month = date(year, month, (next_month - date(year, month, 1)).days)

        # Get budget active at the end of the target month
        budget = get_current_budget(session, target_date=end_of_month)
        if not budget:
            raise ValueError(f"No budget configuration found effective on or before {end_of_month}")
        
        total_budget = budget.hosting_budget + budget.development_budget
        storage_weight_pct = budget.storage_weight_pct
        usage_weight_pct = 100 - storage_weight_pct
        
        # Get usage shares
        usage_shares = calculate_usage_shares(session, year_month)
        
        # Get storage shares
        storage_shares = calculate_storage_shares(session, year_month)
        
        # Calculate raw shares (before overhead distribution)
        total_usage = sum(s["weighted_total"] for s in usage_shares.values())
        total_storage = sum(s.get("total_bytes", 0) for s in storage_shares.values())
        
        # Convert to percentage shares
        usage_pcts = {
            cc_id: (s["weighted_total"] / total_usage * 100) if total_usage > 0 else 0
            for cc_id, s in usage_shares.items()
        }
        storage_pcts = {
            cc_id: (s.get("total_bytes", 0) / total_storage * 100) if total_storage > 0 else 0
            for cc_id, s in storage_shares.items()
        }
        
        # Identify overhead cost centres
        overhead_ids = [0]  # Unassigned is always overhead
        for cc_id, s in usage_shares.items():
            if s.get("is_overhead", False):
                overhead_ids.append(cc_id)
        
        # Distribute overhead
        usage_pcts_final = distribute_overhead(usage_pcts, overhead_ids)
        storage_pcts_final = distribute_overhead(storage_pcts, overhead_ids)
        
        # Generate invoices
        invoices = []
        
        # Delete existing invoices for this month
        existing = session.exec(
            select(MonthlyInvoice).where(MonthlyInvoice.year_month == year_month)
        ).all()
        for e in existing:
            session.delete(e)
        
        # Create new invoices (only for non-overhead cost centres with actual data)
        cost_centres = session.exec(select(CostCentre)).all()
        for cc in cost_centres:
            if cc.is_overhead:
                continue  # Skip overhead centres
            
            usage_pct = usage_pcts_final.get(cc.id, 0)
            storage_pct = storage_pcts_final.get(cc.id, 0)
            
            # Combined share based on weights
            combined_pct = (usage_pct * usage_weight_pct / 100) + (storage_pct * storage_weight_pct / 100)
            
            if combined_pct == 0:
                continue  # Skip if no usage
            
            # Calculate costs
            utilization_cost = total_budget * (usage_weight_pct / 100) * (usage_pct / 100)
            storage_cost = total_budget * (storage_weight_pct / 100) * (storage_pct / 100)
            total_cost = utilization_cost + storage_cost
            
            # Build details JSON
            details = {
                "usage": usage_shares.get(cc.id, {}),
                "storage": storage_shares.get(cc.id, {}),
                "usage_pct": round(usage_pct, 2),
                "storage_pct": round(storage_pct, 2),
            }
            
            invoice = MonthlyInvoice(
                cost_centre_id=cc.id,
                year_month=year_month,
                total_budget=total_budget,
                share_pct=round(combined_pct, 2),
                utilization_cost=round(utilization_cost, 2),
                storage_cost=round(storage_cost, 2),
                total_cost=round(total_cost, 2),
                details_json=json.dumps(details),
                generated_at=datetime.now()
            )
            invoices.append(invoice)
            session.add(invoice)
        
        session.commit()
        
        # Refresh invoices to ensure they are available after session closes
        for inv in invoices:
            session.refresh(inv)
        
        return invoices
