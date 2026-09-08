from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.camera import Camera
from app.models.detection import Detection
from app.schemas.camera import CameraResponse, CameraVehiclesResponse, CameraVehicleObservation
from app.services.association_engine import normalize_plate
from app.services.analytics_engine import map_vehicle_type

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

@router.get("/{camera_id}/vehicles", response_model=CameraVehiclesResponse)
def get_camera_vehicles(
    camera_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    query = db.query(Detection).filter(Detection.camera_id == camera_id)
    
    if start_time:
        query = query.filter(Detection.timestamp >= start_time)
    if end_time:
        query = query.filter(Detection.timestamp <= end_time)
        
    detections = query.order_by(Detection.timestamp.desc()).limit(limit).all()
    
    unique_plates = set()
    observations = []
    
    for det in detections:
        norm_plate = normalize_plate(det.plate_number)
        if norm_plate:
            unique_plates.add(norm_plate)
        observations.append(CameraVehicleObservation(
            plate_number=det.plate_number,
            normalized_plate=norm_plate,
            vehicle_type=map_vehicle_type(det.vehicle_type),
            timestamp=det.timestamp,
            confidence=det.confidence,
            direction=det.direction,
            location_name=det.location_name,
            is_demo=det.is_demo
        ))
        
    return CameraVehiclesResponse(
        camera_id=cam.camera_id,
        camera_name=cam.name,
        total_detections=len(observations),
        unique_vehicles=len(unique_plates),
        vehicles=observations
    )
