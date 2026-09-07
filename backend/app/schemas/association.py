"""
backend/app/schemas/association.py

Pydantic response schemas for Phase 3 Multi-Camera Vehicle Association API.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AssociationObservation(BaseModel):
    """A single observation within a vehicle track."""
    step_number: int
    camera_id: str
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    direction: str
    timestamp: str  # ISO format
    confidence: float
    vehicle_type: str
    transit_time_seconds: Optional[int] = None
    transit_time_formatted: Optional[str] = None
    distance_from_prev_km: Optional[float] = None
    estimated_speed_kmh: Optional[float] = None
    plausibility: str = "origin"
    source: str = "demo"


class VehicleTrackResponse(BaseModel):
    """A vehicle track — a group of associated cross-camera observations."""
    track_id: str
    normalized_plate: str
    raw_plates: List[str]
    vehicle_type: str
    observations: List[AssociationObservation]
    total_observations: int
    total_cameras: int
    first_seen: str  # ISO format
    last_seen: str  # ISO format
    duration_minutes: float
    is_multi_camera: bool
    association_method: str


class AssociationStatsResponse(BaseModel):
    """Summary statistics for multi-camera vehicle associations."""
    total_tracks: int
    multi_camera_tracks: int
    single_camera_tracks: int
    total_observations: int
    most_cameras_track: Optional[Dict[str, Any]] = None
    association_method: str
    thresholds: Dict[str, Any]
