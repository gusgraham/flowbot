from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from database import get_session
from services.analysis import RainfallService

router = APIRouter()

def get_rainfall_service(session: Session = Depends(get_session)) -> RainfallService:
    return RainfallService(session)

@router.get("/analysis/rainfall/{monitor_id}/cumulative")
def get_cumulative_rainfall(
    monitor_id: int, 
    start_date: Optional[datetime] = Query(None), 
    end_date: Optional[datetime] = Query(None),
    service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    return service.get_cumulative_rainfall(monitor_id, start_date, end_date)

@router.get("/analysis/rainfall/{monitor_id}/completeness")
def check_data_completeness(
    monitor_id: int, 
    service: RainfallService = Depends(get_rainfall_service)
) -> Dict[str, Any]:
    return service.check_data_completeness(monitor_id)

def get_event_service(session: Session = Depends(get_session)) -> Any:
    # Need to import EventService inside or at top. 
    # Since we defined it in the same file as RainfallService, we can import it.
    from services.analysis import EventService
    return EventService(session)

@router.post("/analysis/events/{monitor_id}/detect-storms")
def detect_storms(
    monitor_id: int,
    inter_event_hours: int = 6,
    min_total_mm: float = 2.0,
    service: Any = Depends(get_event_service)
) -> Dict[str, Any]:
    events = service.detect_storms(monitor_id, inter_event_hours, min_total_mm)
    return {"monitor_id": monitor_id, "events": events, "count": len(events)}

@router.post("/analysis/events/{monitor_id}/detect-dry-days")
def detect_dry_days(
    monitor_id: int,
    threshold_mm: float = 0.1,
    service: Any = Depends(get_event_service)
) -> Dict[str, Any]:
    days = service.detect_dry_days(monitor_id, threshold_mm)
    return {"monitor_id": monitor_id, "dry_days": days, "count": len(days)}

def get_fdv_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import FDVService
    return FDVService(session)

@router.get("/analysis/scatter/{monitor_id}")
def get_scatter_data(
    monitor_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    service: Any = Depends(get_fdv_service)
) -> Dict[str, Any]:
    points = service.get_scatter_data(monitor_id, start_date, end_date)
    return {"monitor_id": monitor_id, "points": points, "count": len(points)}

def get_spatial_service(session: Session = Depends(get_session)) -> Any:
    from services.analysis import SpatialService
    return SpatialService(session)

@router.post("/analysis/spatial/idw")
def calculate_idw(
    target_lat: float,
    target_lon: float,
    source_gauges: List[Dict[str, Any]],
    power: float = 2.0,
    service: Any = Depends(get_spatial_service)
) -> Dict[str, Any]:
    result = service.calculate_idw(target_lat, target_lon, source_gauges, power)
    return {"target_lat": target_lat, "target_lon": target_lon, "interpolated_value": result}
