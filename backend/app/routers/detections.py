from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.detection import Detection
from app.schemas.detection import DetectionResponse

router = APIRouter(prefix="/detections", tags=["Detections"])

@router.get("", response_model=List[DetectionResponse])
def get_detections(
    limit: int = Query(50, ge=1, le=500),
    camera_id: Optional[str] = None,
    plate_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Detection)
    if camera_id:
        query = query.filter(Detection.camera_id == camera_id)
    if plate_number:
        query = query.filter(Detection.plate_number.ilike(f"%{plate_number.strip().upper()}%"))
    
    return query.order_by(Detection.timestamp.desc()).limit(limit).all()

@router.get("/plates", response_model=List[str])
def get_unique_plates(db: Session = Depends(get_db)):
    results = db.query(Detection.plate_number).distinct().order_by(Detection.plate_number.asc()).all()
    return [r[0] for r in results]
