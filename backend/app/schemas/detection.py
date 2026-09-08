from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DetectionBase(BaseModel):
    camera_id: str
    plate_number: str
    vehicle_type: str = "Car"
    confidence: float = 0.95
    location_name: str
    direction: str
    latitude: float
    longitude: float
    timestamp: datetime
    image_url: Optional[str] = None
    is_demo: int = 1

class DetectionCreate(DetectionBase):
    pass

class DetectionResponse(DetectionBase):
    id: int

    class Config:
        from_attributes = True
