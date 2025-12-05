from typing import List
from sqlmodel import Session, select
from domain.fsm import TimeSeries
from repositories.base import BaseRepository

class TimeSeriesRepository(BaseRepository[TimeSeries]):
    def __init__(self, session: Session):
        super().__init__(session, TimeSeries)
    
    def list_by_install(self, install_id: int) -> List[TimeSeries]:
        statement = select(TimeSeries).where(TimeSeries.install_id == install_id)
        return self.session.exec(statement).all()

    def list_by_monitor(self, monitor_id: int) -> List[TimeSeries]:
        statement = select(TimeSeries).where(TimeSeries.monitor_id == monitor_id)
        return self.session.exec(statement).all()
