from typing import List, Optional
from sqlmodel import Session
from domain.project import Project, ProjectCreate, Site, SiteCreate, Install, InstallCreate
from domain.monitor import Monitor, MonitorCreate
from repositories.project import ProjectRepository, SiteRepository, InstallRepository
from repositories.monitor import MonitorRepository

class ProjectService:
    def __init__(self, session: Session):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.site_repo = SiteRepository(session)
        self.install_repo = InstallRepository(session)
        self.monitor_repo = MonitorRepository(session)

    # Projects
    def create_project(self, project_in: ProjectCreate) -> Project:
        project = Project.from_orm(project_in)
        return self.project_repo.create(project)

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.project_repo.get(project_id)

    def list_projects(self, offset: int = 0, limit: int = 100) -> List[Project]:
        return self.project_repo.list(offset, limit)

    # Sites
    def create_site(self, site_in: SiteCreate) -> Site:
        site = Site.from_orm(site_in)
        return self.site_repo.create(site)
    
    def list_sites(self, project_id: int) -> List[Site]:
        # TODO: Add filtering by project_id in repo
        # For now, just listing all or filtering in memory (inefficient, fix later)
        all_sites = self.site_repo.list(limit=1000)
        return [s for s in all_sites if s.project_id == project_id]

    # Monitors
    def create_monitor(self, monitor_in: MonitorCreate) -> Monitor:
        monitor = Monitor.from_orm(monitor_in)
        return self.monitor_repo.create(monitor)
    
    def list_monitors(self, offset: int = 0, limit: int = 100) -> List[Monitor]:
        return self.monitor_repo.list(offset, limit)

    # Installs
    def create_install(self, install_in: InstallCreate) -> Install:
        install = Install.from_orm(install_in)
        return self.install_repo.create(install)
    
    def list_installs(self, project_id: int) -> List[Install]:
        all_installs = self.install_repo.list(limit=1000)
        return [i for i in all_installs if i.project_id == project_id]
