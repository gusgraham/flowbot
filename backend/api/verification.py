from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session
from database import get_session
from services.verification import VerificationService

router = APIRouter()

def get_service(session: Session = Depends(get_session)) -> VerificationService:
    return VerificationService(session)

@router.post("/verification/{monitor_id}/upload-model")
async def upload_model_results(
    monitor_id: int,
    file: UploadFile = File(...),
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    try:
        content = await file.read()
        created_ts = service.import_model_results(monitor_id, content, file.filename)
        return {
            "monitor_id": monitor_id,
            "message": "Model results imported successfully",
            "created_records": len(created_ts)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verification/{monitor_id}/compare")
def get_comparison_data(
    monitor_id: int,
    start_date: str = None,
    end_date: str = None,
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    return service.get_comparison_data(monitor_id, start_date, end_date)

@router.get("/verification/{monitor_id}/scores")
def calculate_scores(
    monitor_id: int,
    start_date: str = None,
    end_date: str = None,
    service: VerificationService = Depends(get_service)
) -> Dict[str, Any]:
    return service.calculate_scores(monitor_id, start_date, end_date)
