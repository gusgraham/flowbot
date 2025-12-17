"""
Dry Day Analysis API Router

Endpoints for:
- Importing full-period observed data
- Detecting and managing dry days
- Generating 24-hour flow chart data
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session

from database import get_session
from domain.auth import User
from api.deps import get_current_active_user
from domain.verification_models import (
    VerificationFullPeriodImport, VerificationFullPeriodImportRead, VerificationFullPeriodImportUpdate,
    VerificationDryDay, VerificationDryDayRead, VerificationDryDayUpdate
)
from services.dry_day_service import DryDayService


router = APIRouter(prefix="/verification", tags=["Dry Day Analysis"])


# ============================================
# FULL PERIOD IMPORTS
# ============================================

@router.get("/projects/{project_id}/full-period-imports", response_model=List[VerificationFullPeriodImportRead])
def list_full_period_imports(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all full-period imports for a verification project."""
    service = DryDayService(session)
    return service.get_full_period_imports(project_id)


@router.post("/projects/{project_id}/full-period-imports/preview")
async def preview_full_period_import(
    project_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Preview a CSV file to detect available columns before importing."""
    content = await file.read()
    service = DryDayService(session)
    result = service.preview_full_period_import(content, file.filename or "unknown.csv")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/projects/{project_id}/full-period-imports", response_model=VerificationFullPeriodImportRead)
async def import_full_period_data(
    project_id: int,
    file: UploadFile = File(...),
    name: str = Form(...),
    day_rainfall_threshold_mm: float = Form(0.0),
    antecedent_threshold_mm: float = Form(1.0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import full-period observed data from a CSV file.
    
    The CSV should have columns for:
    - timestamp/time/datetime
    - flow (optional)
    - depth (optional)
    - velocity (optional)
    - rainfall (required for dry day detection)
    """
    content = await file.read()
    service = DryDayService(session)
    
    try:
        import_record = service.import_full_period_data(
            project_id=project_id,
            file_content=content,
            filename=file.filename or "unknown.csv",
            name=name,
            day_rainfall_threshold_mm=day_rainfall_threshold_mm,
            antecedent_threshold_mm=antecedent_threshold_mm
        )
        return import_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/full-period-imports/{import_id}", response_model=VerificationFullPeriodImportRead)
def get_full_period_import(
    import_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a specific full-period import."""
    service = DryDayService(session)
    import_record = service.get_full_period_import(import_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_record


@router.delete("/full-period-imports/{import_id}")
def delete_full_period_import(
    import_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a full-period import and all associated data."""
    service = DryDayService(session)
    if not service.delete_full_period_import(import_id):
        raise HTTPException(status_code=404, detail="Import not found")
    return {"status": "deleted"}


# ============================================
# DRY DAY DETECTION & MANAGEMENT
# ============================================

@router.post("/full-period-imports/{import_id}/detect-dry-days")
def detect_dry_days(
    import_id: int,
    day_threshold_mm: Optional[float] = None,
    antecedent_threshold_mm: Optional[float] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect dry days based on rainfall criteria for each monitor.
    
    A dry day is any calendar day where:
    - Day rainfall <= day_threshold_mm (default 0mm)
    - Previous calendar day rainfall < antecedent_threshold_mm (default 1mm)
    
    This will replace any previously detected dry days for this import.
    Returns summary of dry days detected per monitor.
    """
    service = DryDayService(session)
    try:
        return service.detect_dry_days(
            import_id,
            day_threshold_mm=day_threshold_mm,
            antecedent_threshold_mm=antecedent_threshold_mm
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/full-period-imports/{import_id}/monitors")
def list_fp_monitors(
    import_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all monitors with full-period data for an import."""
    service = DryDayService(session)
    return service.get_fp_monitors(import_id)


@router.get("/fp-monitors/{fp_monitor_id}/dry-days", response_model=List[VerificationDryDayRead])
def list_dry_days(
    fp_monitor_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all detected dry days for a specific full-period monitor."""
    service = DryDayService(session)
    return service.get_dry_days(fp_monitor_id)


@router.get("/full-period-imports/{import_id}/dry-days")
def list_all_dry_days_for_import(
    import_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """List all detected dry days for all monitors in an import."""
    service = DryDayService(session)
    dry_days_by_monitor = service.get_dry_days_for_import(import_id)
    
    # Convert to serializable format with monitor info
    fp_monitors = service.get_fp_monitors(import_id)
    result = []
    for fpm in fp_monitors:
        dry_days = dry_days_by_monitor.get(fpm["id"], [])
        result.append({
            "fp_monitor_id": fpm["id"],
            "monitor_id": fpm["monitor_id"],
            "monitor_name": fpm["monitor_name"],
            "dry_days": [
                {
                    "id": dd.id,
                    "date": dd.date.isoformat(),
                    "day_rainfall_mm": dd.day_rainfall_mm,
                    "antecedent_rainfall_mm": dd.antecedent_rainfall_mm,
                    "is_included": dd.is_included,
                    "notes": dd.notes
                }
                for dd in dry_days
            ]
        })
    return result


@router.put("/dry-days/{dry_day_id}", response_model=VerificationDryDayRead)
def update_dry_day(
    dry_day_id: int,
    update: VerificationDryDayUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Update a dry day (typically to toggle inclusion or add notes)."""
    service = DryDayService(session)
    try:
        return service.update_dry_day(dry_day_id, update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fp-monitors/{fp_monitor_id}/24hr-chart")
def get_monitor_dry_day_chart(
    fp_monitor_id: int,
    series_type: str = 'flow',
    day_filter: str = 'all',
    smoothing_frac: float = 0.0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get 24-hour chart data for a specific monitor and series type.
    """
    service = DryDayService(session)
    try:
        return service.get_monitor_dry_day_chart(
            fp_monitor_id,
            series_type=series_type,
            day_filter=day_filter,
            smoothing_frac=smoothing_frac
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/fp-monitors/{fp_monitor_id}/save-profiles")
def save_dwf_profiles(
    fp_monitor_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate and save DWF profiles (benchmarks) for the monitor."""
    service = DryDayService(session)
    try:
        count = service.save_dwf_profiles(fp_monitor_id)
        return {"message": f"Saved {count} DWF profiles"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# 24-HOUR FLOW CHART DATA
# ============================================

@router.get("/full-period-imports/{import_id}/24hr-flow-chart")
def get_24hr_flow_chart(
    import_id: int,
    smoothing: float = 0.0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get 24-hour flow chart data for all included dry days.
    
    Returns:
    - day_traces: Individual flow traces for each dry day
    - envelope: Min/max/mean values at each minute, optionally smoothed
    
    Args:
        smoothing: SG filter smoothing fraction (0.0 = no smoothing, higher = smoother)
    """
    service = DryDayService(session)
    try:
        return service.get_24hr_flow_chart_data(import_id, smoothing_frac=smoothing)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
