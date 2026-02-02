from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlmodel import Session, select

from database import get_session
from domain.auth import User
from api.deps import get_current_active_user
from domain.fsa import FsaDataset
from services.fsa_dwf_service import FsaDWFService
from pydantic import BaseModel

router = APIRouter(prefix="/fsa/dwf", tags=["FSA Dry Weather Flow"])

# Request/Response models
class DryDayStatus(BaseModel):
    id: int
    name: str # Event name or date string
    start_time: datetime
    end_time: datetime
    event_type: str
    enabled: bool

class DWFAnalysisResult(BaseModel):
    profile: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]
    stats: Dict[str, Any]

class DWFExportRequest(BaseModel):
    dataset_ids: List[int]
    start_date: datetime
    variable: str = "Flow"
    profile_line: str = "mean"  # mean, min, max
    sg_enabled: bool = False
    sg_window: int = 21
    sg_order: int = 3
    format: str = "infoworks"  # infoworks, generic

# -------------------------------------------------------------

@router.get("/datasets/{dataset_id}/dry-days", response_model=List[DryDayStatus])
def get_dry_days_status(
    dataset_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    service = FsaDWFService(session)
    return service.get_dry_days_status(dataset_id, dataset.project_id)

@router.put("/datasets/{dataset_id}/dry-days/{event_id}/exclude")
def exclude_dry_day(
    dataset_id: int,
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Mark a dry day as excluded (dashed line)"""
    service = FsaDWFService(session)
    service.toggle_dry_day(dataset_id, event_id, enabled=False)
    return {"status": "excluded"}

@router.delete("/datasets/{dataset_id}/dry-days/{event_id}/exclude")
def include_dry_day(
    dataset_id: int,
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Remove exclusion (solid line)"""
    service = FsaDWFService(session)
    service.toggle_dry_day(dataset_id, event_id, enabled=True)
    return {"status": "included"}

# ----- SG Filter Settings per Monitor -----

class SGSettingsRequest(BaseModel):
    sg_enabled: bool = False
    sg_window: int = 21
    sg_order: int = 3

class SGSettingsResponse(BaseModel):
    dataset_id: int
    sg_enabled: bool
    sg_window: int
    sg_order: int

@router.get("/datasets/{dataset_id}/sg-settings", response_model=SGSettingsResponse)
def get_sg_settings(
    dataset_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get SG filter settings for a monitor's DWF analysis."""
    from domain.fsa import FsaDWFMonitorSettings
    
    settings = session.exec(
        select(FsaDWFMonitorSettings).where(FsaDWFMonitorSettings.dataset_id == dataset_id)
    ).first()
    
    if settings:
        return SGSettingsResponse(
            dataset_id=dataset_id,
            sg_enabled=settings.sg_enabled,
            sg_window=settings.sg_window,
            sg_order=settings.sg_order
        )
    else:
        # Return defaults if no settings exist
        return SGSettingsResponse(
            dataset_id=dataset_id,
            sg_enabled=False,
            sg_window=21,
            sg_order=3
        )

@router.put("/datasets/{dataset_id}/sg-settings", response_model=SGSettingsResponse)
def update_sg_settings(
    dataset_id: int,
    request: SGSettingsRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update SG filter settings for a monitor's DWF analysis."""
    from domain.fsa import FsaDWFMonitorSettings, FsaDataset
    
    # Verify dataset exists
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get or create settings
    settings = session.exec(
        select(FsaDWFMonitorSettings).where(FsaDWFMonitorSettings.dataset_id == dataset_id)
    ).first()
    
    if settings:
        settings.sg_enabled = request.sg_enabled
        settings.sg_window = request.sg_window
        settings.sg_order = request.sg_order
    else:
        settings = FsaDWFMonitorSettings(
            dataset_id=dataset_id,
            sg_enabled=request.sg_enabled,
            sg_window=request.sg_window,
            sg_order=request.sg_order
        )
        session.add(settings)
    
    session.commit()
    session.refresh(settings)
    
    return SGSettingsResponse(
        dataset_id=dataset_id,
        sg_enabled=settings.sg_enabled,
        sg_window=settings.sg_window,
        sg_order=settings.sg_order
    )

# ----- Compute and Export -----

class ComputeRequest(BaseModel):
    candidate_event_ids: Optional[List[int]] = None
    sg_enabled: bool = False
    sg_window: int = 21
    sg_order: int = 3

@router.post("/datasets/{dataset_id}/compute") #, response_model=DWFAnalysisResult (complex dict)
def compute_dwf_analysis(
    dataset_id: int,
    request: ComputeRequest = Body(default=ComputeRequest()),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    dataset = session.get(FsaDataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    service = FsaDWFService(session)
    result = service.compute_dwf_analysis(
        dataset_id, 
        dataset.project_id, 
        request.candidate_event_ids,
        sg_enabled=request.sg_enabled,
        sg_window=request.sg_window,
        sg_order=request.sg_order
    )
    
    if "error" in result:
        # We can return 200 with error/empty data or 400?
        # Frontend might handle empty data better
        return result
        
    return result

@router.post("/projects/{project_id}/export")
def export_dwf(
    project_id: int,
    request: DWFExportRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    service = FsaDWFService(session)
    
    if request.format == "generic":
        csv_content = service.export_generic_csv(
            project_id, 
            request.dataset_ids, 
            request.start_date, 
            request.variable,
            request.profile_line,
            request.sg_enabled,
            request.sg_window,
            request.sg_order
        )
    else:  # infoworks
        csv_content = service.export_infoworks(
            project_id, 
            request.dataset_ids, 
            request.start_date, 
            request.variable,
            request.profile_line,
            request.sg_enabled,
            request.sg_window,
            request.sg_order
        )
    
    filename = f"DWF_Export_{request.variable}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
