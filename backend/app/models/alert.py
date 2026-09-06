from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(30), index=True, nullable=False)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id"), nullable=False)
    location_name = Column(String(150), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence = Column(Float, default=0.95)
    alert_type = Column(String(100), default="Authorized Watchlist Match — Requires Human Review")
    status = Column(String(50), default="PENDING_REVIEW")  # PENDING_REVIEW, REVIEWED, DISMISSED
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)
