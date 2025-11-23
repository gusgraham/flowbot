from typing import List, Optional
from sqlmodel import Session
from domain.visit import Visit, VisitCreate
from repositories.visit import VisitRepository
from repositories.project import InstallRepository
from infra.storage import StorageService

class InstallService:
    def __init__(self, session: Session):
        self.session = session
        self.visit_repo = VisitRepository(session)
        self.install_repo = InstallRepository(session)
        self.storage_service = StorageService()

    # Visits
    def create_visit(self, visit_in: VisitCreate) -> Visit:
        visit = Visit.from_orm(visit_in)
        return self.visit_repo.create(visit)

    def list_visits(self, install_id: int) -> List[Visit]:
        return self.visit_repo.list_by_install(install_id)

    # Ingestion
    def upload_data(self, install_id: int, file_content: bytes, filename: str):
        # Save raw file to disk
        file_path = self.storage_service.save_file(file_content, filename, subfolder=f"installs/{install_id}")
        
        # Process file (Parse & Create TimeSeries)
        # We need to instantiate TimeSeriesService here or inject it
        # For simplicity, we'll instantiate it
        from services.timeseries import TimeSeriesService
        ts_service = TimeSeriesService(self.session)
        ts_service.process_upload(file_path=file_path, original_filename=filename, install_id=install_id)
        
        return file_path
