from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TrajectoryStep(BaseModel):
    step_number: int
    camera_id: str
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    direction: str
    timestamp: datetime
    confidence: float
    vehicle_type: str
    time_diff_from_prev_seconds: Optional[int] = None
    time_diff_formatted: Optional[str] = None
    distance_from_prev_km: Optional[float] = None
    estimated_speed_kmh: Optional[float] = None

class TrajectoryResponse(BaseModel):
    plate_number: str
    vehicle_type: str
    total_observations: int
    first_seen: datetime
    last_seen: datetime
    total_duration_minutes: float
    is_watchlist: bool = False
    trajectory: List[TrajectoryStep]
