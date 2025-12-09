from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_session
from domain.auth import Token, User
from repositories.auth import UserRepository
from services.auth import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "Engineer"

@router.post("/register")
def register_user(
    user_in: UserRegister,
    session: Session = Depends(get_session)
):
    """
    Public registration endpoint.
    New users are created with is_active=False (pending admin approval).
    Default permissions: FSA, WQ, Verification enabled; FSM disabled.
    """
    user_repo = UserRepository(session)
    
    # Check if user already exists
    existing = user_repo.get_by_username(user_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    auth_service = AuthService()
    hashed_password = auth_service.get_password_hash(user_in.password)
    
    # Create user with pending status and default permissions
    db_user = User(
        username=user_in.email,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        role=user_in.role,
        is_active=False,  # Pending admin approval
        is_superuser=False,
        access_fsm=False,  # Not included by default
        access_fsa=True,
        access_wq=True,
        access_verification=True,
        access_ssd=True  # SSD enabled by default
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return {
        "status": "success",
        "message": "Registration submitted! An administrator will review your request."
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user_repo = UserRepository(session)
    auth_service = AuthService()
    
    user = user_repo.get_by_username(form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please contact an administrator.",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
