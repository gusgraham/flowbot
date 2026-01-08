from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_session
from domain.auth import User, UserCreate, UserRead, UserUpdate
from repositories.auth import UserRepository
from services.auth import AuthService
from api.deps import get_current_active_superuser, get_current_active_user

router = APIRouter()

@router.get("/me", response_model=UserRead)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user

@router.get("", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    repo = UserRepository(session)
    # Basic pagination implementation using the repo's session directly for now
    # Ideally UserRepository should expose a get_multi method
    from sqlmodel import select
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users

@router.post("", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    repo = UserRepository(session)
    user = repo.get_by_username(user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    auth_service = AuthService()
    hashed_password = auth_service.get_password_hash(user_in.password)
    
    # Create user dict excluding password, then add hashed_password
    user_data = user_in.model_dump(exclude={"password"})
    db_user = User(**user_data, hashed_password=hashed_password)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    repo = UserRepository(session)
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    user_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in user_data:
        auth_service = AuthService()
        password = user_data.pop("password")
        user.hashed_password = auth_service.get_password_hash(password)
        
    for key, value in user_data.items():
        setattr(user, key, value)
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_superuser),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account",
        )
    
    # Clean up related records to avoid foreign key constraint violations
    # Delete collaborator entries (link tables)
    from sqlmodel import text
    collaborator_tables = [
        "fsm_projectcollaborator",
        "fsa_projectcollaborator", 
        "wq_projectcollaborator",
        "ver_projectcollaborator",
        "ssd_projectcollaborator",
    ]
    for table in collaborator_tables:
        session.exec(text(f"DELETE FROM {table} WHERE user_id = :user_id").bindparams(user_id=user_id))
    
    # Set owner_id to NULL for projects owned by this user
    project_tables = [
        "fsm_project",
        "fsa_project",
        "wq_project",
        "ver_project",
        "ssd_project",
    ]
    for table in project_tables:
        session.exec(text(f"UPDATE {table} SET owner_id = NULL WHERE owner_id = :user_id").bindparams(user_id=user_id))
    
    session.delete(user)
    session.commit()
    return {"status": "success", "message": "User deleted"}


# ==========================================
# USER USAGE (self-service)
# ==========================================

from datetime import datetime, date
from sqlmodel import select
from sqlalchemy import func
from domain.admin import UsageLog, StorageSnapshot

@router.get("/me/usage")
def get_my_usage(
    year_month: str = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get the current user's usage statistics."""
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
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid year_month format")
    
    # Get usage by module
    usage_data = session.exec(
        select(
            UsageLog.module,
            func.count(UsageLog.id).label("request_count"),
            func.sum(UsageLog.weight).label("weighted_total")
        )
        .where(UsageLog.user_id == current_user.id)
        .where(UsageLog.timestamp >= start_date)
        .where(UsageLog.timestamp < end_date)
        .group_by(UsageLog.module)
    ).all()
    
    total_weighted = sum(r[2] or 0 for r in usage_data)
    total_requests = sum(r[1] or 0 for r in usage_data)
    
    return {
        "year_month": year_month,
        "total_requests": total_requests,
        "total_weighted": total_weighted,
        "by_module": [
            {
                "module": r[0],
                "request_count": r[1],
                "weighted_total": r[2] or 0,
                "percentage": round((r[2] or 0) / total_weighted * 100, 1) if total_weighted > 0 else 0
            }
            for r in usage_data
        ]
    }


@router.get("/me/storage")
def get_my_storage(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get the current user's storage usage (projects they own)."""
    # Get most recent snapshot date
    latest = session.exec(
        select(StorageSnapshot.snapshot_date)
        .order_by(StorageSnapshot.snapshot_date.desc())
        .limit(1)
    ).first()
    
    if not latest:
        return {
            "snapshot_date": None,
            "total_bytes": 0,
            "total_mb": 0,
            "projects": []
        }
    
    # Get storage for this user's projects
    storage_data = session.exec(
        select(StorageSnapshot)
        .where(StorageSnapshot.user_id == current_user.id)
        .where(StorageSnapshot.snapshot_date == latest)
        .order_by(StorageSnapshot.size_bytes.desc())
    ).all()
    
    total_bytes = sum(s.size_bytes for s in storage_data)
    
    return {
        "snapshot_date": latest.isoformat(),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "projects": [
            {
                "project_id": s.project_id,
                "module": s.module,
                "size_bytes": s.size_bytes,
                "size_mb": round(s.size_bytes / (1024 * 1024), 2)
            }
            for s in storage_data
        ]
    }

