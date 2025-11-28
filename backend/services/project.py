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

    def update_project(self, project_id: int, project_update: ProjectCreate) -> Optional[Project]:
        # Basic update logic - in a real app, use a dedicated Update schema
        project = self.project_repo.get(project_id)
        if not project:
            return None
        
        project_data = project_update.dict(exclude_unset=True)
        for key, value in project_data.items():
            setattr(project, key, value)
            
        return self.project_repo.update(project)

    def list_projects(self, offset: int = 0, limit: int = 100) -> List[Project]:
        return self.project_repo.list(offset, limit)

    def delete_project(self, project_id: int) -> bool:
        # TODO: Add cascade delete logic if needed (though DB FKs might handle it)
        # For now, just delete the project
        return self.project_repo.delete(project_id)

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
        monitor = Monitor.model_validate(monitor_in)
        return self.monitor_repo.create(monitor)
    
    def list_monitors(self, offset: int = 0, limit: int = 100) -> List[Monitor]:
        return self.monitor_repo.list(offset, limit)
    
    def list_monitors_by_site(self, site_id: int) -> List[Monitor]:
        # Get all installs for this site, then get unique monitors
        from domain.project import Install
        from domain.monitor import Monitor
        from sqlmodel import select
        
        statement = select(Install).where(Install.site_id == site_id)
        installs = self.session.exec(statement).all()
        monitor_ids = list(set([i.monitor_id for i in installs if i.monitor_id]))
        
        if not monitor_ids:
            return []
        
        # Fetch monitors by IDs
        statement = select(Monitor).where(Monitor.id.in_(monitor_ids))
        return list(self.session.exec(statement).all())
    
    def list_monitors_by_project(self, project_id: int) -> List[Monitor]:
        # Get all monitors and filter by project_id
        all_monitors = self.monitor_repo.list(limit=1000)
        return [m for m in all_monitors if m.project_id == project_id]


    # Installs
    def create_install(self, install_in: InstallCreate) -> Install:
        install = Install.from_orm(install_in)
        return self.install_repo.create(install)
    
    def list_installs(self, project_id: int) -> List[Install]:
        all_installs = self.install_repo.list(limit=1000)
        return [i for i in all_installs if i.project_id == project_id]

    def import_project_from_csv(self, csv_content: bytes):
        import pandas as pd
        import io
        from datetime import datetime
        
        try:
            df = pd.read_csv(io.BytesIO(csv_content))
        except Exception as e:
            raise ValueError(f"Invalid CSV format: {e}")
            
        required_cols = ['ProjectName', 'SiteID', 'MonitorID']
        if not all(col in df.columns for col in required_cols):
             # Try legacy format mapping if needed, or raise error
             # Legacy CSV might have different headers.
             # For now, assume this format or map if possible.
             pass

        # Group by Project
        for project_name, p_group in df.groupby('ProjectName'):
            # Check if project exists?
            # For now, create new
            project = self.create_project(ProjectCreate(name=project_name, client_ref=project_name, job_number="IMPORTED"))
            
            for index, row in p_group.iterrows():
                # Create Site
                site_id_str = str(row.get('SiteID', f"SITE-{index}"))
                site = self.create_site(SiteCreate(
                    project_id=project.id,
                    site_id=site_id_str,
                    address=str(row.get('Address', '')),
                    mh_ref=str(row.get('MHRef', ''))
                ))
                
                # Create Monitor
                monitor_id_str = str(row.get('MonitorID', f"MON-{index}"))
                monitor = self.create_monitor(MonitorCreate(
                    monitor_asset_id=monitor_id_str,
                    monitor_type=str(row.get('MonitorType', 'Flow Monitor'))
                ))
                
                # Create Install
                install_date_val = row.get('InstallDate')
                if pd.isna(install_date_val):
                    install_date = datetime.now()
                else:
                    install_date = pd.to_datetime(install_date_val)

                self.create_install(InstallCreate(
                    project_id=project.id,
                    site_id=site.id,
                    monitor_id=monitor.id,
                    install_date=install_date,
                    fm_pipe_shape=str(row.get('PipeShape', 'Circular')),
                    fm_pipe_dim_a=float(row.get('PipeWidth', 0)) if not pd.isna(row.get('PipeWidth')) else 0,
                    fm_pipe_dim_b=float(row.get('PipeHeight', 0)) if not pd.isna(row.get('PipeHeight')) else 0
                ))
