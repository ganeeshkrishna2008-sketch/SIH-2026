from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(30), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(50), default="Sedan")  # Sedan, SUV, Bus, Truck, Motorcycle, Auto
    color = Column(String(30), default="Unknown")
    is_watchlist = Column(Integer, default=0)           # 1 if in authorized watchlist, 0 otherwise
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
