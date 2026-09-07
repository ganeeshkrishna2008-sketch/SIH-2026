"""
backend/app/services/association_engine.py

Phase 3 — Multi-Camera Vehicle Association Engine

Associates vehicle observations (detections) across multiple cameras by:
  1. Normalizing plate text (OCR output normalization)
  2. Grouping observations by normalized plate
  3. Ordering chronologically within each group
  4. Validating transitions with temporal/spatial plausibility checks
  5. Splitting into separate tracks if transitions are implausible

All thresholds are configurable constants defined below.
"""
import math
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.detection import Detection
from app.models.camera import Camera
from app.models.vehicle import Vehicle


# ─── Configurable Association Thresholds ───────────────────────────────────────

# Minimum time (seconds) between two observations at different cameras
# to be considered the same journey. Observations closer than this at
# different cameras may indicate a data anomaly.
MIN_TRANSIT_TIME_SECONDS = 30

# Maximum time (seconds) between consecutive observations to be considered
# part of the same journey/track. Beyond this, start a new track segment.
MAX_TRANSIT_TIME_SECONDS = 7200  # 2 hours

# Maximum plausible average speed (km/h) between two camera observations.
# If the implied speed exceeds this, the transition is flagged as implausible.
MAX_PLAUSIBLE_SPEED_KMH = 200.0

# Minimum OCR confidence to include an observation in association.
# Observations below this threshold are still stored but excluded from
# high-confidence track association.
MIN_ASSOCIATION_CONFIDENCE = 0.0  # Include all by default


# ─── Plate Normalization ──────────────────────────────────────────────────────

def normalize_plate(raw_plate: str) -> str:
    """
    Normalize a license plate string for consistent matching.

    Applies:
    - Convert to uppercase
    - Remove spaces, hyphens, dots, and underscores
    - Strip any remaining non-alphanumeric characters
    - Strip leading/trailing whitespace

    Does NOT invent or correct characters — only reformats.

    Examples:
        "TS 09 AB 1234"  → "TS09AB1234"
        "ts-09-ab-1234"  → "TS09AB1234"
        "TS.09.AB.1234"  → "TS09AB1234"
        "TS09AB1234"     → "TS09AB1234"
    """
    if not raw_plate:
        return ""
    text = raw_plate.strip().upper()
    # Remove common separators: spaces, hyphens, dots, underscores
    text = text.replace(" ", "").replace("-", "").replace(".", "").replace("_", "")
    # Remove any remaining non-alphanumeric characters
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text


# ─── Haversine Distance (reuses same formula as trajectory_engine) ────────────

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# ─── Plausibility Check ──────────────────────────────────────────────────────

def is_transition_plausible(
    prev_lat: float, prev_lon: float, prev_time: datetime,
    curr_lat: float, curr_lon: float, curr_time: datetime,
    prev_camera_id: str, curr_camera_id: str,
) -> Tuple[bool, str]:
    """
    Check whether the transition between two consecutive observations
    is temporally and spatially plausible.

    Returns:
        (is_plausible: bool, reason: str)

    Reasons for rejection:
        - "same_camera_duplicate": Same camera, too close in time (likely duplicate)
        - "too_fast": Implied speed exceeds MAX_PLAUSIBLE_SPEED_KMH
        - "too_short_transit": Time gap < MIN_TRANSIT_TIME_SECONDS between different cameras
        - "time_gap_exceeded": Time gap > MAX_TRANSIT_TIME_SECONDS (new journey)
    """
    time_diff_seconds = (curr_time - prev_time).total_seconds()

    # Same camera back-to-back within 10 seconds → likely duplicate frame
    if prev_camera_id == curr_camera_id and time_diff_seconds < 10:
        return True, "same_camera_reobservation"

    # Different cameras but impossibly short transit
    if prev_camera_id != curr_camera_id and time_diff_seconds < MIN_TRANSIT_TIME_SECONDS:
        return False, "too_short_transit"

    # Time gap exceeds maximum → consider it a new journey
    if time_diff_seconds > MAX_TRANSIT_TIME_SECONDS:
        return False, "time_gap_exceeded"

    # Speed check
    distance_km = haversine_distance_km(prev_lat, prev_lon, curr_lat, curr_lon)
    if time_diff_seconds > 0 and distance_km > 0:
        speed_kmh = distance_km / (time_diff_seconds / 3600.0)
        if speed_kmh > MAX_PLAUSIBLE_SPEED_KMH:
            return False, f"too_fast ({speed_kmh:.0f} km/h implied)"

    return True, "plausible"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 0:
        return "N/A"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem = seconds % 60
    if rem == 0:
        return f"{minutes}m"
    return f"{minutes}m {rem}s"


# ─── Association Engine ───────────────────────────────────────────────────────

class AssociationEngine:
    """
    Groups vehicle detections into tracks by normalized plate,
    validates temporal/spatial plausibility of transitions,
    and provides search functionality.
    """

    @staticmethod
    def associate_all_vehicles(db: Session) -> List[dict]:
        """
        Associate all detections into vehicle tracks.

        Returns a list of track dictionaries, each containing:
        - track_id: unique identifier (e.g. "VT-001")
        - normalized_plate: the normalized plate number
        - raw_plates: list of original plate strings seen (before normalization)
        - vehicle_type: from the most confident detection or vehicle record
        - observations: list of observation dicts with full metadata
        - total_cameras: count of distinct cameras
        - first_seen / last_seen: timestamps
        - association_method: description of how the track was formed
        """
        # Load all detections ordered by timestamp
        detections = (
            db.query(Detection)
            .filter(Detection.confidence >= MIN_ASSOCIATION_CONFIDENCE)
            .order_by(Detection.timestamp.asc())
            .all()
        )

        if not detections:
            return []

        # Load camera metadata
        cameras = {c.camera_id: c for c in db.query(Camera).all()}

        # Load vehicle metadata
        vehicles = {}
        for v in db.query(Vehicle).all():
            vehicles[normalize_plate(v.plate_number)] = v

        # Group detections by normalized plate
        plate_groups: Dict[str, List[Detection]] = defaultdict(list)
        raw_plates_map: Dict[str, set] = defaultdict(set)

        for det in detections:
            norm = normalize_plate(det.plate_number)
            if norm:  # skip empty/invalid
                plate_groups[norm].append(det)
                raw_plates_map[norm].add(det.plate_number)

        # Build tracks
        all_tracks = []
        track_counter = 0

        for norm_plate in sorted(plate_groups.keys()):
            group_dets = plate_groups[norm_plate]
            # Already sorted by timestamp from query

            # Split into sub-tracks based on plausibility
            sub_tracks = AssociationEngine._split_into_plausible_tracks(group_dets)

            for sub_dets in sub_tracks:
                track_counter += 1
                track_id = f"VT-{track_counter:04d}"

                # Determine vehicle type
                vehicle_record = vehicles.get(norm_plate)
                if vehicle_record:
                    vehicle_type = vehicle_record.vehicle_type
                else:
                    # Use the most confident detection's vehicle_type
                    best_det = max(sub_dets, key=lambda d: d.confidence)
                    vehicle_type = best_det.vehicle_type

                # Build observation list with transit metadata
                observations = []
                prev_det = None
                for idx, det in enumerate(sub_dets, start=1):
                    cam = cameras.get(det.camera_id)
                    cam_name = cam.name if cam else det.camera_id

                    transit_time_sec = None
                    transit_time_fmt = None
                    distance_km = None
                    speed_kmh = None
                    plausibility = "origin"

                    if prev_det:
                        time_diff = (det.timestamp - prev_det.timestamp).total_seconds()
                        transit_time_sec = int(time_diff)
                        transit_time_fmt = format_duration(time_diff)
                        distance_km = haversine_distance_km(
                            prev_det.latitude, prev_det.longitude,
                            det.latitude, det.longitude
                        )
                        if time_diff > 0 and distance_km > 0:
                            speed_kmh = round(distance_km / (time_diff / 3600.0), 1)

                        _, plausibility = is_transition_plausible(
                            prev_det.latitude, prev_det.longitude, prev_det.timestamp,
                            det.latitude, det.longitude, det.timestamp,
                            prev_det.camera_id, det.camera_id,
                        )

                    obs = {
                        "step_number": idx,
                        "camera_id": det.camera_id,
                        "camera_name": cam_name,
                        "location_name": det.location_name,
                        "latitude": det.latitude,
                        "longitude": det.longitude,
                        "direction": det.direction,
                        "timestamp": det.timestamp.isoformat(),
                        "confidence": round(det.confidence, 3),
                        "vehicle_type": det.vehicle_type,
                        "transit_time_seconds": transit_time_sec,
                        "transit_time_formatted": transit_time_fmt,
                        "distance_from_prev_km": distance_km,
                        "estimated_speed_kmh": speed_kmh,
                        "plausibility": plausibility,
                        "source": "demo" if det.is_demo == 1 else "anpr",
                    }
                    observations.append(obs)
                    prev_det = det

                distinct_cameras = len(set(d.camera_id for d in sub_dets))
                first_seen = sub_dets[0].timestamp
                last_seen = sub_dets[-1].timestamp
                duration_minutes = round((last_seen - first_seen).total_seconds() / 60.0, 1)

                track = {
                    "track_id": track_id,
                    "normalized_plate": norm_plate,
                    "raw_plates": sorted(raw_plates_map[norm_plate]),
                    "vehicle_type": vehicle_type,
                    "observations": observations,
                    "total_observations": len(observations),
                    "total_cameras": distinct_cameras,
                    "first_seen": first_seen.isoformat(),
                    "last_seen": last_seen.isoformat(),
                    "duration_minutes": duration_minutes,
                    "is_multi_camera": distinct_cameras > 1,
                    "association_method": "normalized_plate_match + temporal_spatial_plausibility",
                }

                all_tracks.append(track)

        return all_tracks

    @staticmethod
    def _split_into_plausible_tracks(detections: List[Detection]) -> List[List[Detection]]:
        """
        Split a list of chronologically ordered detections (same normalized plate)
        into sub-tracks where each consecutive pair of observations has a
        plausible transition. If a transition is implausible due to time gap,
        start a new sub-track.
        """
        if not detections:
            return []

        sub_tracks: List[List[Detection]] = [[detections[0]]]

        for i in range(1, len(detections)):
            prev = detections[i - 1]
            curr = detections[i]

            plausible, reason = is_transition_plausible(
                prev.latitude, prev.longitude, prev.timestamp,
                curr.latitude, curr.longitude, curr.timestamp,
                prev.camera_id, curr.camera_id,
            )

            if plausible or reason == "same_camera_reobservation":
                # Continue current track
                sub_tracks[-1].append(curr)
            elif reason == "time_gap_exceeded":
                # Start a new track (different journey)
                sub_tracks.append([curr])
            else:
                # Implausible but within time window — still add to track
                # but the observation will be flagged with its plausibility reason
                sub_tracks[-1].append(curr)

        return sub_tracks

    @staticmethod
    def search_vehicle(db: Session, plate_query: str) -> List[dict]:
        """
        Search for vehicle tracks matching a plate query.
        Supports exact and partial (substring) matching on normalized plate.
        Returns matching tracks in chronological order.
        """
        norm_query = normalize_plate(plate_query)
        if not norm_query:
            return []

        all_tracks = AssociationEngine.associate_all_vehicles(db)

        # Exact match first, then partial
        exact = [t for t in all_tracks if t["normalized_plate"] == norm_query]
        if exact:
            return exact

        partial = [t for t in all_tracks if norm_query in t["normalized_plate"]]
        return partial

    @staticmethod
    def get_association_stats(db: Session) -> dict:
        """
        Return summary statistics about multi-camera vehicle associations.
        """
        all_tracks = AssociationEngine.associate_all_vehicles(db)

        total_tracks = len(all_tracks)
        multi_camera_tracks = sum(1 for t in all_tracks if t["is_multi_camera"])
        single_camera_tracks = total_tracks - multi_camera_tracks
        total_observations = sum(t["total_observations"] for t in all_tracks)

        # Find track with most cameras
        max_cameras_track = None
        if all_tracks:
            best = max(all_tracks, key=lambda t: t["total_cameras"])
            max_cameras_track = {
                "track_id": best["track_id"],
                "plate": best["normalized_plate"],
                "cameras": best["total_cameras"],
            }

        return {
            "total_tracks": total_tracks,
            "multi_camera_tracks": multi_camera_tracks,
            "single_camera_tracks": single_camera_tracks,
            "total_observations": total_observations,
            "most_cameras_track": max_cameras_track,
            "association_method": "normalized_plate_match + temporal_spatial_plausibility",
            "thresholds": {
                "min_transit_time_seconds": MIN_TRANSIT_TIME_SECONDS,
                "max_transit_time_seconds": MAX_TRANSIT_TIME_SECONDS,
                "max_plausible_speed_kmh": MAX_PLAUSIBLE_SPEED_KMH,
                "min_association_confidence": MIN_ASSOCIATION_CONFIDENCE,
            }
        }
