from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from domain.admin import CostCentre

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
    access_ssd: bool = True  # Spill Storage Design module

class User(UserBase, table=True):
    __tablename__ = "auth_user"
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    cost_centre_id: Optional[int] = Field(default=None, foreign_key="admin_cost_centre.id")
    
    # Relationships
    cost_centre: Optional["CostCentre"] = Relationship(back_populates="users")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    cost_centre_id: Optional[int] = None

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
    access_ssd: Optional[bool] = None
    cost_centre_id: Optional[int] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None
