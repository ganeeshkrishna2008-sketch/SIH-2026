from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertReviewRequest

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.timestamp.desc()).all()

@router.patch("/{alert_id}/review", response_model=AlertResponse)
def review_alert(alert_id: int, review_data: AlertReviewRequest, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found")
    
    alert.status = review_data.status
    alert.reviewed_by = review_data.reviewed_by
    alert.reviewed_at = datetime.utcnow()
    if review_data.notes:
        alert.notes = review_data.notes

    db.commit()
    db.refresh(alert)
    return alert
