from typing import List, Dict, Any
from sqlmodel import Session, select
from domain.fsm import FsmProject, Install, Monitor, Visit

class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def get_monitor_status(self, project_id: int) -> List[Dict[str, Any]]:
        # Mock logic for now - in reality would query installs/monitors and check last data/visit
        statement = select(Install).where(Install.project_id == project_id)
        installs = self.session.exec(statement).all()
        
        status_list = []
        for install in installs:
            status_list.append({
                "install_id": install.id,
                "monitor_id": install.monitor_id,
                "site_id": install.site_id,
                "status": "Active", # Logic to determine status
                "last_data": "2023-10-27", # Logic to get last data
                "battery": "12.5V" # Logic to get last battery
            })
        return status_list

    def get_monitor_history(self, monitor_id: int) -> List[Dict[str, Any]]:
        # Get visits and events for a monitor
        # For now just visits
        # Need to find installs for this monitor first?
        # Or just query visits linked to installs linked to this monitor?
        # This is complex SQLModel join.
        # For now, simple mock.
        return [{"date": "2023-10-01", "type": "Visit", "details": "Installed"}]

    def get_data_summary(self, project_id: int) -> Dict[str, Any]:
        return {
            "total_monitors": 10,
            "active_monitors": 8,
            "data_completeness": "95%"
        }

    def get_issues(self, project_id: int) -> List[Dict[str, Any]]:
        return [
            {"install_id": 1, "issue": "Low Battery", "severity": "High"},
            {"install_id": 2, "issue": "Missing Data", "severity": "Medium"}
        ]
