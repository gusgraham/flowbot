from typing import List
from sqlmodel import Session, select
from domain.visit import Visit
from repositories.base import BaseRepository

class VisitRepository(BaseRepository[Visit]):
    def __init__(self, session: Session):
        super().__init__(session, Visit)

    def list_by_install(self, install_id: int) -> List[Visit]:
        statement = select(Visit).where(Visit.install_id == install_id)
        return self.session.exec(statement).all()
