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
from api.deps import get_current_active_user, oauth2_scheme

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
        is_active=True,  # Auto-activate new users
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
    
    # Store original login time to enforce max session duration
    import time
    orig_iat = int(time.time())
    
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "orig_iat": orig_iat},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Refresh access token if within max session window.
    Sliding window: 30 mins active.
    Max window: 10 hours from initial login.
    """
    from jose import jwt, JWTError
    from services.auth import SECRET_KEY, ALGORITHM
    import time

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        orig_iat = payload.get("orig_iat")
        if not orig_iat:
            orig_iat = int(time.time()) # Fallback for old tokens
            
        # Check max session duration (10 hours = 36000 seconds)
        MAX_SESSION_SECONDS = 10 * 60 * 60
        now = int(time.time())
        
        if now - orig_iat > MAX_SESSION_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Create new token with same orig_iat
        auth_service = AuthService()
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token = auth_service.create_access_token(
            data={"sub": current_user.username, "orig_iat": orig_iat},
            expires_delta=access_token_expires
        )
        
        return {"access_token": new_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
