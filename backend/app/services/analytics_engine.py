from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from collections import defaultdict
from app.models.detection import Detection
from app.models.camera import Camera
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    CameraVolume,
    TimeIntervalVolume,
    VehicleTypeCount
)

# Centralized mapping for high-level dashboard vehicle categories
VEHICLE_TYPE_MAP: Dict[str, str] = {
    "car": "Car",
    "sedan": "Car",
    "suv": "Car",
    "motorcycle": "Motorcycle",
    "bike": "Motorcycle",
    "bus": "Bus",
    "truck": "Truck",
    "auto": "Other",
    "unknown": "Other",
}

def map_vehicle_type(v_type: Optional[str]) -> str:
    """
    Map raw or detected vehicle type string to high-level category:
    Car, Motorcycle, Bus, Truck, Other
    Handles whitespace and case-insensitivity safely.
    """
    if not v_type:
        return "Other"
    clean = str(v_type).strip().lower()
    return VEHICLE_TYPE_MAP.get(clean, "Other")

class AnalyticsEngine:
    @staticmethod
    def get_summary_analytics(db: Session) -> AnalyticsSummaryResponse:
        total_detections = db.query(func.count(Detection.id)).scalar() or 0
        unique_vehicles = db.query(func.count(distinct(Detection.plate_number))).scalar() or 0
        active_cameras = db.query(func.count(Camera.id)).filter(Camera.status == "ACTIVE").scalar() or 0

        # Volume by camera
        camera_counts = (
            db.query(Detection.camera_id, func.count(Detection.id).label("cnt"))
            .group_by(Detection.camera_id)
            .all()
        )
        cam_meta = {c.camera_id: c for c in db.query(Camera).all()}
        
        volume_by_camera: List[CameraVolume] = []
        busiest_cam_info = {"camera_id": "N/A", "name": "N/A", "count": 0}

        for cam_id, count in camera_counts:
            cam = cam_meta.get(cam_id)
            cam_name = cam.name if cam else cam_id
            loc_name = cam.location_name if cam else "Unknown"
            pct = round((count / total_detections * 100), 1) if total_detections > 0 else 0.0
            
            vol = CameraVolume(
                camera_id=cam_id,
                camera_name=cam_name,
                location_name=loc_name,
                vehicle_count=count,
                percentage=pct
            )
            volume_by_camera.append(vol)

            if count > busiest_cam_info["count"]:
                busiest_cam_info = {
                    "camera_id": cam_id,
                    "name": cam_name,
                    "location": loc_name,
                    "count": count
                }

        volume_by_camera.sort(key=lambda x: x.vehicle_count, reverse=True)

        # Volume by 10-minute time intervals
        all_detections = db.query(Detection.timestamp).order_by(Detection.timestamp.asc()).all()
        interval_counts: Dict[str, int] = defaultdict(int)

        for (ts,) in all_detections:
            # Round down to 10 minute interval
            bucket_minute = (ts.minute // 10) * 10
            start_str = f"{ts.hour:02d}:{bucket_minute:02d}"
            end_min = bucket_minute + 10
            end_hour = ts.hour
            if end_min >= 60:
                end_min = 0
                end_hour = (end_hour + 1) % 24
            interval_str = f"{start_str} - {end_hour:02d}:{end_min:02d}"
            interval_counts[interval_str] += 1

        volume_by_interval: List[TimeIntervalVolume] = []
        peak_interval_info = {"interval": "N/A", "count": 0, "hourly_rate": 0}

        # Keep sorted by interval start
        for interval_str, count in interval_counts.items():
            start_str = interval_str.split(" - ")[0]
            hourly_rate = count * 6  # 10 min * 6 = 1 hour
            volume_by_interval.append(TimeIntervalVolume(
                time_interval=interval_str,
                start_time=start_str,
                vehicle_count=count,
                hourly_rate_estimate=hourly_rate
            ))
            if count > peak_interval_info["count"]:
                peak_interval_info = {
                    "interval": interval_str,
                    "count": count,
                    "hourly_rate": hourly_rate
                }

        volume_by_interval.sort(key=lambda x: x.start_time)

        # Vehicle type distribution (grouped into high-level categories: Car, Motorcycle, Bus, Truck, Other)
        type_counts = (
            db.query(Detection.vehicle_type, func.count(Detection.id))
            .group_by(Detection.vehicle_type)
            .all()
        )
        grouped_counts: Dict[str, int] = defaultdict(int)
        for v_type, count in type_counts:
            cat = map_vehicle_type(v_type)
            grouped_counts[cat] += count

        valid_total = sum(grouped_counts.values())
        vehicle_type_distribution: List[VehicleTypeCount] = []
        if valid_total > 0:
            for cat, count in grouped_counts.items():
                if count > 0:
                    pct = round((count / valid_total * 100), 1)
                    vehicle_type_distribution.append(VehicleTypeCount(
                        vehicle_type=cat,
                        count=count,
                        percentage=pct
                    ))
            vehicle_type_distribution.sort(key=lambda x: x.count, reverse=True)

            # Ensure sum of percentages equals exactly 100.0% when observations exist
            if vehicle_type_distribution:
                diff = round(100.0 - sum(item.percentage for item in vehicle_type_distribution), 1)
                if diff != 0.0:
                    vehicle_type_distribution[0].percentage = round(vehicle_type_distribution[0].percentage + diff, 1)

        return AnalyticsSummaryResponse(
            total_detections=total_detections,
            unique_vehicles=unique_vehicles,
            active_cameras=active_cameras,
            busiest_camera=busiest_cam_info,
            peak_time_interval=peak_interval_info,
            volume_by_camera=volume_by_camera,
            volume_by_interval=volume_by_interval,
            vehicle_type_distribution=vehicle_type_distribution
        )
