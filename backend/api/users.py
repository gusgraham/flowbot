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

@router.get("/", response_model=List[UserRead])
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

@router.post("/", response_model=UserRead)
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
    
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        role=user_in.role,
        is_superuser=user_in.is_superuser,
        is_active=user_in.is_active,
    )
    
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
    
    if user_in.password:
        auth_service = AuthService()
        hashed_password = auth_service.get_password_hash(user_in.password)
        user.hashed_password = hashed_password
    
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.is_superuser is not None:
        user.is_superuser = user_in.is_superuser
    if user_in.role is not None:
        user.role = user_in.role
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
