from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CameraBase(BaseModel):
    camera_id: str
    name: str
    location_name: str
    latitude: float
    longitude: float
    direction: str
    status: str = "ACTIVE"

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CameraVehicleObservation(BaseModel):
    plate_number: str
    normalized_plate: str
    vehicle_type: str
    timestamp: datetime
    confidence: float
    direction: str
    location_name: str
    is_demo: int

class CameraVehiclesResponse(BaseModel):
    camera_id: str
    camera_name: str
    total_detections: int
    unique_vehicles: int
    vehicles: List[CameraVehicleObservation]
