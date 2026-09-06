import math
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.detection import Detection
from app.models.camera import Camera
from app.models.vehicle import Vehicle
from app.schemas.trajectory import TrajectoryStep, TrajectoryResponse

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def format_time_diff(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if rem_seconds == 0:
        return f"{minutes}m"
    return f"{minutes}m {rem_seconds}s"

class TrajectoryEngine:
    @staticmethod
    def get_vehicle_trajectory(db: Session, plate_number: str) -> Optional[TrajectoryResponse]:
        normalized_plate = plate_number.strip().upper().replace(" ", "").replace("-", "")
        
        # Query all detections for this plate ordered chronologically
        detections = (
            db.query(Detection)
            .filter(Detection.plate_number == normalized_plate)
            .order_by(Detection.timestamp.asc())
            .all()
        )
        
        if not detections:
            # Fallback: try case-insensitive partial match
            detections = (
                db.query(Detection)
                .filter(Detection.plate_number.ilike(f"%{normalized_plate}%"))
                .order_by(Detection.timestamp.asc())
                .all()
            )

        if not detections:
            return None

        # Check vehicle metadata
        vehicle_record = db.query(Vehicle).filter(Vehicle.plate_number == detections[0].plate_number).first()
        is_watchlist = bool(vehicle_record.is_watchlist) if vehicle_record else False
        vehicle_type = vehicle_record.vehicle_type if vehicle_record else detections[0].vehicle_type

        # Fetch camera names map
        cameras = {c.camera_id: c for c in db.query(Camera).all()}

        steps: List[TrajectoryStep] = []
        prev_detection: Optional[Detection] = None

        for idx, det in enumerate(detections, start=1):
            cam = cameras.get(det.camera_id)
            cam_name = cam.name if cam else det.camera_id

            time_diff_sec = None
            time_diff_fmt = None
            dist_km = None
            speed_kmh = None

            if prev_detection:
                time_diff_sec = int((det.timestamp - prev_detection.timestamp).total_seconds())
                time_diff_fmt = format_time_diff(max(0, time_diff_sec))
                dist_km = calculate_haversine_distance_km(
                    prev_detection.latitude, prev_detection.longitude,
                    det.latitude, det.longitude
                )
                if time_diff_sec > 0 and dist_km > 0:
                    speed_kmh = round((dist_km / (time_diff_sec / 3600.0)), 1)

            step = TrajectoryStep(
                step_number=idx,
                camera_id=det.camera_id,
                camera_name=cam_name,
                location_name=det.location_name,
                latitude=det.latitude,
                longitude=det.longitude,
                direction=det.direction,
                timestamp=det.timestamp,
                confidence=round(det.confidence, 3),
                vehicle_type=det.vehicle_type,
                time_diff_from_prev_seconds=time_diff_sec,
                time_diff_formatted=time_diff_fmt,
                distance_from_prev_km=dist_km,
                estimated_speed_kmh=speed_kmh
            )
            steps.append(step)
            prev_detection = det

        first_seen = steps[0].timestamp
        last_seen = steps[-1].timestamp
        total_duration = round((last_seen - first_seen).total_seconds() / 60.0, 1)

        return TrajectoryResponse(
            plate_number=detections[0].plate_number,
            vehicle_type=vehicle_type,
            total_observations=len(steps),
            first_seen=first_seen,
            last_seen=last_seen,
            total_duration_minutes=total_duration,
            is_watchlist=is_watchlist,
            trajectory=steps
        )
