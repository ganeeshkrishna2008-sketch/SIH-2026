from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.camera import Camera
from app.models.detection import Detection
from app.schemas.camera import CameraResponse

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).order_by(Camera.camera_id.asc()).all()

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    return cam
