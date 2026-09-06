from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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
