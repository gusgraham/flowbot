from sqlmodel import Session
from domain.fsm import FsmProject, Site, Install
from repositories.base import BaseRepository

class ProjectRepository(BaseRepository[FsmProject]):
    def __init__(self, session: Session):
        super().__init__(session, FsmProject)

class SiteRepository(BaseRepository[Site]):
    def __init__(self, session: Session):
        super().__init__(session, Site)

class InstallRepository(BaseRepository[Install]):
    def __init__(self, session: Session):
        super().__init__(session, Install)
