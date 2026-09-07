"""
backend/app/routers/associations.py

Phase 3 — Multi-Camera Vehicle Association API Endpoints

Provides:
  GET /api/associations/tracks          — All vehicle tracks with cross-camera associations
  GET /api/associations/tracks/{plate}  — Single vehicle track by plate number
  GET /api/associations/search          — Fuzzy plate search returning matching tracks
  GET /api/associations/stats           — Association summary statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.association_engine import AssociationEngine
from app.schemas.association import (
    VehicleTrackResponse,
    AssociationStatsResponse,
)

router = APIRouter(prefix="/associations", tags=["Multi-Camera Association (Phase 3)"])


@router.get("/tracks", response_model=List[VehicleTrackResponse])
def get_all_tracks(
    multi_camera_only: bool = Query(False, description="If true, only return tracks seen at 2+ cameras"),
    db: Session = Depends(get_db),
):
    """
    Return all vehicle tracks with their cross-camera observation sequences.
    Each track groups observations of the same vehicle (by normalized plate)
    and validates temporal/spatial plausibility of transitions.
    """
    tracks = AssociationEngine.associate_all_vehicles(db)
    if multi_camera_only:
        tracks = [t for t in tracks if t["is_multi_camera"]]
    return tracks


@router.get("/search", response_model=List[VehicleTrackResponse])
def search_vehicle_tracks(
    q: str = Query(..., min_length=1, description="Plate number or partial plate to search"),
    db: Session = Depends(get_db),
):
    """
    Search for vehicle tracks by plate number (exact or partial match).
    Returns matching tracks with their full cross-camera observation history.
    """
    results = AssociationEngine.search_vehicle(db, q)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No vehicle tracks found matching plate '{q}'"
        )
    return results


@router.get("/stats", response_model=AssociationStatsResponse)
def get_association_stats(db: Session = Depends(get_db)):
    """
    Return summary statistics about multi-camera vehicle associations,
    including total tracks, multi-camera tracks, and configured thresholds.
    """
    return AssociationEngine.get_association_stats(db)


@router.get("/tracks/{plate_number}", response_model=List[VehicleTrackResponse])
def get_track_by_plate(plate_number: str, db: Session = Depends(get_db)):
    """
    Get the vehicle track(s) for a specific plate number.
    Returns all tracks associated with the normalized version of the input plate.
    Multiple tracks may exist if the same plate was observed in separate journeys.
    """
    results = AssociationEngine.search_vehicle(db, plate_number)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No vehicle track found for plate '{plate_number}'"
        )
    return results
