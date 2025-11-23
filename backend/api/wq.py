from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session
from database import get_session
from services.wq import WQService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> WQService:
    return WQService(session)

@router.post("/wq/{monitor_id}/upload")
async def upload_wq_data(
    monitor_id: int,
    file: UploadFile = File(...),
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    try:
        content = await file.read()
        created_ts = service.import_wq_data(monitor_id, content, file.filename)
        return {
            "monitor_id": monitor_id,
            "message": "WQ data imported successfully",
            "created_records": len(created_ts),
            "variables": [ts.variable for ts in created_ts]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wq/{monitor_id}/data")
def get_wq_data(
    monitor_id: int,
    service: WQService = Depends(get_service)
) -> List[Dict[str, Any]]:
    return service.get_wq_timeseries(monitor_id)

@router.get("/wq/{monitor_id}/correlation")
def correlate_wq_flow(
    monitor_id: int,
    service: WQService = Depends(get_service)
) -> Dict[str, Any]:
    return service.correlate_wq_flow(monitor_id)
