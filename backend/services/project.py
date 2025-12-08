from typing import List, Optional
from datetime import datetime
from sqlmodel import Session
from domain.fsm import (
    FsmProject, FsmProjectCreate, FsmProjectUpdate, Site, SiteCreate, Install, InstallCreate, 
    Monitor, MonitorCreate, RawDataSettings, RawDataSettingsCreate, RawDataSettingsUpdate
)
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
    def create_project(self, project_in: FsmProjectCreate, owner_id: int) -> FsmProject:
        project = FsmProject.from_orm(project_in)
        project.owner_id = owner_id
        return self.project_repo.create(project)

    def get_project(self, project_id: int) -> Optional[FsmProject]:
        return self.project_repo.get(project_id)

    def update_project(self, project_id: int, project_update: FsmProjectUpdate) -> Optional[FsmProject]:
        # Basic update logic - in a real app, use a dedicated Update schema
        project = self.project_repo.get(project_id)
        if not project:
            return None
        
        project_data = project_update.dict(exclude_unset=True)
        for key, value in project_data.items():
            setattr(project, key, value)
            
        return self.project_repo.update(project_id, project)

    def list_projects(self, offset: int = 0, limit: int = 100, owner_id: Optional[int] = None) -> List[FsmProject]:
        # If owner_id is provided, filter by it.
        # BaseRepository.list doesn't support filtering, so we might need to do it manually or add a method to repo.
        # For now, let's do it here or use a custom query.
        if owner_id:
            from sqlmodel import select
            statement = select(FsmProject).where(FsmProject.owner_id == owner_id).offset(offset).limit(limit)
            return self.session.exec(statement).all()
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
        from domain.fsm import Install, Monitor
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
        # Create the install first to get an ID
        created_install = self.install_repo.create(install)
        
        # Now create default RawDataSettings
        try:
            # Fetch project for defaults
            project = self.project_repo.get(created_install.project_id)
            default_path = project.default_download_path if project else None
            
            # Create settings linked to this install
            settings = RawDataSettings(
                install_id=created_install.id,
                file_path=default_path,
                pipe_shape=created_install.fm_pipe_shape,
                pipe_width=created_install.fm_pipe_width_mm,
                pipe_height=created_install.fm_pipe_height_mm,
                # Default empty/None for others
            )
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(created_install) # Refresh to load relationship if needed
            
        except Exception as e:
            print(f"Error creating default RawDataSettings: {e}")
            # We don't want to fail the install creation just because settings failed,
            # but ideally we should log this.
            pass
            
        return created_install
    
    
    def list_installs(self, project_id: int) -> List[Install]:
        all_installs = self.install_repo.list(limit=1000)
        return [i for i in all_installs if i.project_id == project_id]
    
    def get_install(self, install_id: int) -> Optional[Install]:
        return self.install_repo.get(install_id)
    
    def delete_install(self, install_id: int):
        self.install_repo.delete(install_id)
    
    def uninstall_install(self, install_id: int, removal_date: datetime):
        install = self.install_repo.get(install_id)
        if install:
            install.removal_date = removal_date
            self.session.add(install)
            self.session.commit()
            self.session.refresh(install)

    def import_project_from_csv(self, csv_content: bytes, owner_id: int):
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
            project = self.create_project(FsmProjectCreate(name=project_name, client=project_name, job_number="IMPORTED"), owner_id=owner_id)
            
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
                    fm_pipe_dim_b=float(row.get('PipeHeight', 0)) if not pd.isna(row.get('PipeHeight')) else 0
                ))
    
    # Raw Data Settings
    def get_raw_data_settings(self, install_id: int) -> Optional[RawDataSettings]:
        from sqlmodel import select
        statement = select(RawDataSettings).where(RawDataSettings.install_id == install_id)
        return self.session.exec(statement).first()
    
    def update_raw_data_settings(self, install_id: int, settings_update: RawDataSettingsUpdate) -> RawDataSettings:
        from sqlmodel import select
        # Try to get existing settings
        statement = select(RawDataSettings).where(RawDataSettings.install_id == install_id)
        settings = self.session.exec(statement).first()
        
        if not settings:
            # Create new settings if none exist
            settings = RawDataSettings(install_id=install_id)
        
        # Update fields
        update_data = settings_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)
        
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings
    
    def resolve_file_format(self, file_format: str, install: Install, project: FsmProject) -> str:
        """Resolve file format template with actual values."""
        import os
        
        # Get monitor for this install
        monitor = self.monitor_repo.get(install.monitor_id) if install.monitor_id else None
        site = self.site_repo.get(install.site_id) if install.site_id else None
        
        resolved = file_format
        if monitor:
            resolved = resolved.replace('{pmac_id}', monitor.pmac_id or '')
            resolved = resolved.replace('{ast_id}', monitor.monitor_asset_id or '')
        if install:
            resolved = resolved.replace('{inst_id}', install.install_id or '')
            resolved = resolved.replace('{cl_ref}', install.client_ref or '')
        if site:
            resolved = resolved.replace('{site_id}', site.site_id or '')
        if project:
            resolved = resolved.replace('{prj_id}', project.job_number or '')
        
        return resolved
    
    def validate_file_exists(self, file_path: str, file_format: str, install: Install) -> bool:
        """Check if a file exists at the resolved path."""
        import os
        
        project = self.get_project(install.project_id)
        resolved_format = self.resolve_file_format(file_format, install, project)
        full_path = os.path.join(file_path, resolved_format)
        
        return os.path.isfile(full_path)
