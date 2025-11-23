from sqlmodel import Session
from domain.project import Project, Site, Install
from repositories.base import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: Session):
        super().__init__(session, Project)

class SiteRepository(BaseRepository[Site]):
    def __init__(self, session: Session):
        super().__init__(session, Site)

class InstallRepository(BaseRepository[Install]):
    def __init__(self, session: Session):
        super().__init__(session, Install)
