from sqlmodel import Session
from ..domain.monitor import Monitor
from .base import BaseRepository

class MonitorRepository(BaseRepository[Monitor]):
    def __init__(self, session: Session):
        super().__init__(session, Monitor)
