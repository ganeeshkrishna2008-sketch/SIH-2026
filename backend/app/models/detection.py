from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id"), index=True, nullable=False)
    plate_number = Column(String(30), index=True, nullable=False)
    vehicle_type = Column(String(50), default="Sedan")
    confidence = Column(Float, nullable=False, default=0.95)
    location_name = Column(String(150), nullable=False)
    direction = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    image_url = Column(String(255), nullable=True)
    is_demo = Column(Integer, default=1)  # 1 indicates DEMO DATA
