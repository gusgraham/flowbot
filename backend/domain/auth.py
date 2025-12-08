from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    role: str = "Engineer" # Admin, Engineer, Manager, Field
    access_fsm: bool = True # Grant access to FSM module
    access_fsa: bool = True
    access_wq: bool = True
    access_verification: bool = True

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    # Relationships
    # projects: List["FsmProject"] = Relationship(back_populates="owner")
    # collaborations: List["FsmProject"] = Relationship(link_model="ProjectCollaborator")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    access_fsm: Optional[bool] = None
    access_fsa: Optional[bool] = None
    access_wq: Optional[bool] = None
    access_verification: Optional[bool] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None
