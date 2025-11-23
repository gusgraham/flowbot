from typing import Optional
from sqlmodel import Session, select
from ..domain.auth import User
from .base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()
