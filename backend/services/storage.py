"""
Storage Calculation Service

Calculates storage usage for projects and creates snapshots for cost allocation.
"""
import os
from datetime import date, datetime
from typing import Dict, List, Optional
from sqlmodel import Session, select

from database import engine
from domain.admin import StorageSnapshot
from domain.auth import User


# Module data directories
MODULE_DATA_DIRS = {
    "FSM": "data/fsm",
    "FSA": "data/fsa", 
    "WQ": "data/wq",
    "VER": "data/verification",
    "SSD": "data/ssd",
}


def get_directory_size(path: str) -> int:
    """Get total size of a directory in bytes."""
    total_size = 0
    if not os.path.exists(path):
        return 0
    
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, IOError):
                pass  # Skip files we can't access
    return total_size


def get_database_size() -> int:
    """Get size of the SQLite database file."""
    db_path = "flowbot.db"
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0


def calculate_project_storage(module: str, project_id: int) -> int:
    """Calculate storage for a specific project."""
    base_dir = MODULE_DATA_DIRS.get(module)
    if not base_dir:
        return 0
    
    project_dir = os.path.join(base_dir, str(project_id))
    return get_directory_size(project_dir)


def get_project_owner_map(session: Session) -> Dict[str, Dict[int, Optional[int]]]:
    """Get mapping of module -> project_id -> owner_id for all projects."""
    from domain.fsm import FsmProject
    from domain.fsa import FsaProject
    from domain.wq import WaterQualityProject
    from domain.verification import VerificationProject
    from domain.ssd import SSDProject
    
    owner_map = {
        "FSM": {},
        "FSA": {},
        "WQ": {},
        "VER": {},
        "SSD": {},
    }
    
    # FSM projects
    for p in session.exec(select(FsmProject)).all():
        owner_map["FSM"][p.id] = p.owner_id
    
    # FSA projects
    for p in session.exec(select(FsaProject)).all():
        owner_map["FSA"][p.id] = p.owner_id
    
    # WQ projects
    for p in session.exec(select(WaterQualityProject)).all():
        owner_map["WQ"][p.id] = p.owner_id
    
    # Verification projects
    for p in session.exec(select(VerificationProject)).all():
        owner_map["VER"][p.id] = p.owner_id
    
    # SSD projects
    for p in session.exec(select(SSDProject)).all():
        owner_map["SSD"][p.id] = p.owner_id
    
    return owner_map


def create_storage_snapshots(snapshot_date: Optional[date] = None) -> List[StorageSnapshot]:
    """
    Create storage snapshots for all projects.
    This should be run periodically (e.g., daily or weekly) to track storage over time.
    """
    if snapshot_date is None:
        snapshot_date = date.today()
    
    snapshots = []
    
    with Session(engine) as session:
        # Get project owners
        owner_map = get_project_owner_map(session)
        
        # Calculate storage for each module
        for module, base_dir in MODULE_DATA_DIRS.items():
            if not os.path.exists(base_dir):
                continue
            
            # List project directories
            for project_dir_name in os.listdir(base_dir):
                try:
                    project_id = int(project_dir_name)
                except ValueError:
                    continue  # Skip non-numeric directories
                
                project_path = os.path.join(base_dir, project_dir_name)
                if not os.path.isdir(project_path):
                    continue
                
                # Get storage size
                size_bytes = get_directory_size(project_path)
                if size_bytes == 0:
                    continue
                
                # Get owner
                owner_id = owner_map.get(module, {}).get(project_id)
                if owner_id is None:
                    continue  # Skip orphaned project data
                
                # Create snapshot
                snapshot = StorageSnapshot(
                    user_id=owner_id,
                    project_id=project_id,
                    module=module,
                    snapshot_date=snapshot_date,
                    size_bytes=size_bytes,
                )
                snapshots.append(snapshot)
        
        # Delete existing snapshots for this date and add new ones
        existing = session.exec(
            select(StorageSnapshot).where(StorageSnapshot.snapshot_date == snapshot_date)
        ).all()
        for e in existing:
            session.delete(e)
        
        for s in snapshots:
            session.add(s)
        
        session.commit()
        
        # Refresh snapshots to ensure they are available after session closes
        for s in snapshots:
            session.refresh(s)
    
    return snapshots


def get_storage_summary(session: Session, snapshot_date: Optional[date] = None) -> Dict:
    """Get storage summary for a specific date (or most recent)."""
    from sqlalchemy import func
    
    # If no date specified, get most recent snapshot date
    if snapshot_date is None:
        latest = session.exec(
            select(StorageSnapshot.snapshot_date)
            .order_by(StorageSnapshot.snapshot_date.desc())
            .limit(1)
        ).first()
        if not latest:
            return {"snapshot_date": None, "total_bytes": 0, "by_module": [], "by_user": []}
        snapshot_date = latest
    
    from domain.admin import CostCentre
    
    # Total storage
    total = session.exec(
        select(func.sum(StorageSnapshot.size_bytes))
        .where(StorageSnapshot.snapshot_date == snapshot_date)
    ).first() or 0
    
    # Storage by module
    by_module = session.exec(
        select(
            StorageSnapshot.module,
            func.sum(StorageSnapshot.size_bytes).label("total_bytes"),
            func.count(StorageSnapshot.id).label("project_count")
        )
        .where(StorageSnapshot.snapshot_date == snapshot_date)
        .group_by(StorageSnapshot.module)
    ).all()
    
    # Storage by cost centre
    by_cost_centre = session.exec(
        select(
            CostCentre.name,
            CostCentre.code,
            func.sum(StorageSnapshot.size_bytes).label("total_bytes"),
            func.count(StorageSnapshot.id).label("project_count")
        )
        .join(User, User.id == StorageSnapshot.user_id)
        .join(CostCentre, CostCentre.id == User.cost_centre_id, isouter=True)
        .where(StorageSnapshot.snapshot_date == snapshot_date)
        .group_by(CostCentre.id)
    ).all()
    
    return {
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
        "total_bytes": total,
        "database_size_bytes": get_database_size(),
        "by_module": [
            {"module": r[0], "total_bytes": r[1], "project_count": r[2]}
            for r in by_module
        ],
        "by_cost_centre": [
            {
                "cost_centre_name": r[0] or "Unassigned",
                "cost_centre_code": r[1] or "N/A",
                "total_bytes": r[2],
                "project_count": r[3]
            }
            for r in by_cost_centre
        ]
    }
