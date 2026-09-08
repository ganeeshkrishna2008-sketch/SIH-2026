from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("/{plate_number}")
def get_vehicle_details(plate_number: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()
    if vehicle:
        return {
            "status": "found",
            "plate_number": vehicle.plate_number,
            "vehicle_type": vehicle.vehicle_type,
            "color": vehicle.color,
            "owner_name": vehicle.owner_name,
            "registration_date": vehicle.registration_date,
            "chassis_number": vehicle.chassis_number,
            "engine_number": vehicle.engine_number,
            "is_watchlist": bool(vehicle.is_watchlist),
            "notes": vehicle.notes,
        }
    else:
        # Mock Vahan Response for unknown vehicles detected in ANPR
        return {
            "status": "not_found",
            "plate_number": plate_number,
            "vehicle_type": "Unknown",
            "color": "Unknown",
            "owner_name": "Records Unavailable",
            "registration_date": "N/A",
            "chassis_number": "N/A",
            "engine_number": "N/A",
            "is_watchlist": False,
            "notes": "No RTO details found for this plate.",
        }
