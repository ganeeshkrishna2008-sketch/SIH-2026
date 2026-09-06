from pydantic import BaseModel
from typing import List, Dict, Any

class CameraVolume(BaseModel):
    camera_id: str
    camera_name: str
    location_name: str
    vehicle_count: int
    percentage: float

class TimeIntervalVolume(BaseModel):
    time_interval: str   # e.g. "09:00 - 09:10"
    start_time: str
    vehicle_count: int
    hourly_rate_estimate: int

class VehicleTypeCount(BaseModel):
    vehicle_type: str
    count: int
    percentage: float

class AnalyticsSummaryResponse(BaseModel):
    total_detections: int
    unique_vehicles: int
    active_cameras: int
    busiest_camera: Dict[str, Any]
    peak_time_interval: Dict[str, Any]
    volume_by_camera: List[CameraVolume]
    volume_by_interval: List[TimeIntervalVolume]
    vehicle_type_distribution: List[VehicleTypeCount]
