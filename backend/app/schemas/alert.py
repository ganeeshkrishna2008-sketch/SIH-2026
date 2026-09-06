from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertBase(BaseModel):
    plate_number: str
    camera_id: str
    location_name: str
    timestamp: datetime
    confidence: float = 0.95
    alert_type: str = "Authorized Watchlist Match — Requires Human Review"
    status: str = "PENDING_REVIEW"
    reviewed_by: Optional[str] = None
    notes: Optional[str] = None

class AlertReviewRequest(BaseModel):
    status: str  # REVIEWED, DISMISSED
    reviewed_by: str
    notes: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
