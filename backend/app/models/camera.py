from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    direction = Column(String(50), nullable=False)  # Northbound, Southbound, Eastbound, Westbound
    status = Column(String(20), default="ACTIVE")    # ACTIVE, INACTIVE, MAINTENANCE
    created_at = Column(DateTime, default=datetime.utcnow)
