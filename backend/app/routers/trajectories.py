from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.trajectory_engine import TrajectoryEngine
from app.schemas.trajectory import TrajectoryResponse
from app.models.detection import Detection

router = APIRouter(prefix="/trajectories", tags=["Trajectories"])

@router.get("/{plate_number}", response_model=TrajectoryResponse)
def get_trajectory_by_plate(plate_number: str, db: Session = Depends(get_db)):
    trajectory = TrajectoryEngine.get_vehicle_trajectory(db, plate_number)
    if not trajectory:
        raise HTTPException(
            status_code=404,
            detail=f"No observations found for vehicle plate '{plate_number}'"
        )
    return trajectory
