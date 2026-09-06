import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Ensure backend root is on sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from app.database import engine, Base, SessionLocal
from app.models import Camera, Vehicle, Detection, Alert

def seed_database():
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Seeding Cameras (Phase 1: 4 Synthetic Cameras)...")
        cameras_data = [
            {
                "camera_id": "CAM-01",
                "name": "MG Road Junction Camera 01",
                "location_name": "MG Road / Central Junction",
                "latitude": 17.3850,
                "longitude": 78.4867,
                "direction": "Northbound",
                "status": "ACTIVE"
            },
            {
                "camera_id": "CAM-04",
                "name": "Ring Road East Toll Camera 04",
                "location_name": "Outer Ring Road East Gate",
                "latitude": 17.4100,
                "longitude": 78.5200,
                "direction": "Eastbound",
                "status": "ACTIVE"
            },
            {
                "camera_id": "CAM-07",
                "name": "Cyber Towers Flyover Camera 07",
                "location_name": "HITEC City / Cyber Towers Corridor",
                "latitude": 17.4500,
                "longitude": 78.3800,
                "direction": "Westbound",
                "status": "ACTIVE"
            },
            {
                "camera_id": "CAM-09",
                "name": "Airport Expressway South Camera 09",
                "location_name": "Airport Expressway Exit 4",
                "latitude": 17.2400,
                "longitude": 78.4300,
                "direction": "Southbound",
                "status": "ACTIVE"
            },
        ]

        cam_objs = {}
        for c in cameras_data:
            cam = Camera(**c)
            db.add(cam)
            cam_objs[c["camera_id"]] = cam

        db.commit()
        print(f"Created {len(cameras_data)} cameras.")

        print("Seeding Vehicles...")
        vehicles_data = [
            {"plate_number": "TS09AB1234", "vehicle_type": "Sedan", "color": "White", "is_watchlist": 0, "notes": "Standard commuter"},
            {"plate_number": "DL01CZ4567", "vehicle_type": "SUV", "color": "Black", "is_watchlist": 0, "notes": "Commercial fleet"},
            {"plate_number": "KA05MH8899", "vehicle_type": "Sedan", "color": "Silver", "is_watchlist": 1, "notes": "Authorized Watchlist Demo Subject"},
            {"plate_number": "MH12TR3321", "vehicle_type": "Bus", "color": "Blue", "is_watchlist": 0, "notes": "Intercity Transit"},
            {"plate_number": "HR26DQ5544", "vehicle_type": "Truck", "color": "Yellow", "is_watchlist": 0, "notes": "Logistics Freight"},
            {"plate_number": "AP09BK7788", "vehicle_type": "Motorcycle", "color": "Red", "is_watchlist": 0, "notes": "Delivery courier"},
            {"plate_number": "UP32EF9900", "vehicle_type": "SUV", "color": "Grey", "is_watchlist": 1, "notes": "Authorized Watchlist Demo Subject 2"},
            {"plate_number": "TN02AA4321", "vehicle_type": "Auto", "color": "Green-Yellow", "is_watchlist": 0, "notes": "Urban Para-transit"},
        ]

        for v in vehicles_data:
            db.add(Vehicle(**v))
        db.commit()
        print(f"Created {len(vehicles_data)} vehicles.")

        print("Seeding Detections and Multi-Camera Trajectories...")
        base_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)

        # 1. Primary Demo Trajectory: TS09AB1234 (CAM-01 -> CAM-04 -> CAM-07 -> CAM-09)
        trajectory_1 = [
            ("CAM-01", base_time + timedelta(minutes=2, seconds=15), 0.98),
            ("CAM-04", base_time + timedelta(minutes=9, seconds=40), 0.96),
            ("CAM-07", base_time + timedelta(minutes=16, seconds=10), 0.97),
            ("CAM-09", base_time + timedelta(minutes=25, seconds=30), 0.95),
        ]
        for cam_id, t_stamp, conf in trajectory_1:
            cam = cam_objs[cam_id]
            db.add(Detection(
                camera_id=cam_id,
                plate_number="TS09AB1234",
                vehicle_type="Sedan",
                confidence=conf,
                location_name=cam.location_name,
                direction=cam.direction,
                latitude=cam.latitude,
                longitude=cam.longitude,
                timestamp=t_stamp,
                is_demo=1
            ))

        # 2. Secondary Trajectory: DL01CZ4567 (CAM-01 -> CAM-04 -> CAM-07)
        trajectory_2 = [
            ("CAM-01", base_time + timedelta(minutes=5, seconds=0), 0.94),
            ("CAM-04", base_time + timedelta(minutes=12, seconds=30), 0.95),
            ("CAM-07", base_time + timedelta(minutes=21, seconds=0), 0.92),
        ]
        for cam_id, t_stamp, conf in trajectory_2:
            cam = cam_objs[cam_id]
            db.add(Detection(
                camera_id=cam_id,
                plate_number="DL01CZ4567",
                vehicle_type="SUV",
                confidence=conf,
                location_name=cam.location_name,
                direction=cam.direction,
                latitude=cam.latitude,
                longitude=cam.longitude,
                timestamp=t_stamp,
                is_demo=1
            ))

        # 3. Watchlist Trajectory: KA05MH8899 (CAM-07 -> CAM-04 -> CAM-09)
        trajectory_3 = [
            ("CAM-07", base_time + timedelta(minutes=10, seconds=0), 0.99),
            ("CAM-04", base_time + timedelta(minutes=18, seconds=45), 0.97),
            ("CAM-09", base_time + timedelta(minutes=28, seconds=10), 0.96),
        ]
        for cam_id, t_stamp, conf in trajectory_3:
            cam = cam_objs[cam_id]
            db.add(Detection(
                camera_id=cam_id,
                plate_number="KA05MH8899",
                vehicle_type="Sedan",
                confidence=conf,
                location_name=cam.location_name,
                direction=cam.direction,
                latitude=cam.latitude,
                longitude=cam.longitude,
                timestamp=t_stamp,
                is_demo=1
            ))

        # 4. Generate realistic background traffic across time buckets (09:00 - 10:00)
        # to satisfy traffic flow count requirements (e.g. 09:00-09:10: ~63, 09:10-09:20: ~93, etc.)
        bg_vehicles = [
            ("MH12TR3321", "Bus"),
            ("HR26DQ5544", "Truck"),
            ("AP09BK7788", "Motorcycle"),
            ("UP32EF9900", "SUV"),
            ("TN02AA4321", "Auto"),
        ]
        # generate additional random plates for traffic volume realism
        random.seed(42)
        generated_plates = [
            (f"TS{random.randint(1,15):02d}{chr(random.randint(65,90))}{chr(random.randint(65,90))}{random.randint(1000,9999)}",
             random.choice(["Sedan", "SUV", "Motorcycle", "Auto", "Truck", "Bus"]))
            for _ in range(35)
        ]
        all_traffic_pool = bg_vehicles + generated_plates

        # Time intervals targeting realistic distribution
        # 09:00-09:10: 25 observations
        # 09:10-09:20: 45 observations (peak)
        # 09:20-09:30: 38 observations
        # 09:30-09:40: 28 observations
        # 09:40-09:50: 20 observations
        # 09:50-10:00: 16 observations
        interval_specs = [
            (0, 10, 25),
            (10, 20, 45),
            (20, 30, 38),
            (30, 40, 28),
            (40, 50, 20),
            (50, 60, 16),
        ]

        for start_min, end_min, count in interval_specs:
            for _ in range(count):
                plate, v_type = random.choice(all_traffic_pool)
                cam_id = random.choice(list(cam_objs.keys()))
                cam = cam_objs[cam_id]
                offset_sec = random.randint(start_min * 60, end_min * 60 - 1)
                t_stamp = base_time + timedelta(seconds=offset_sec)
                conf = round(random.uniform(0.88, 0.99), 3)

                db.add(Detection(
                    camera_id=cam_id,
                    plate_number=plate,
                    vehicle_type=v_type,
                    confidence=conf,
                    location_name=cam.location_name,
                    direction=cam.direction,
                    latitude=cam.latitude,
                    longitude=cam.longitude,
                    timestamp=t_stamp,
                    is_demo=1
                ))

        db.commit()
        total_dets = db.query(Detection).count()
        print(f"Total Detections created: {total_dets}")

        print("Seeding Authorized Watchlist Alerts (Phase 1 Demo)...")
        alerts_data = [
            {
                "plate_number": "KA05MH8899",
                "camera_id": "CAM-07",
                "location_name": "HITEC City / Cyber Towers Corridor",
                "timestamp": base_time + timedelta(minutes=10, seconds=0),
                "confidence": 0.99,
                "alert_type": "Authorized Watchlist Match — Requires Human Review",
                "status": "PENDING_REVIEW",
                "notes": "Matched Flagged Plate DB (Demo Entry). Pending operator confirmation."
            },
            {
                "plate_number": "UP32EF9900",
                "camera_id": "CAM-01",
                "location_name": "MG Road / Central Junction",
                "timestamp": base_time + timedelta(minutes=15, seconds=30),
                "confidence": 0.94,
                "alert_type": "Authorized Watchlist Match — Requires Human Review",
                "status": "REVIEWED",
                "reviewed_by": "Officer R. Sharma (Badge #4092)",
                "notes": "Verified by operator. Route logging active."
            }
        ]
        for a in alerts_data:
            db.add(Alert(**a))

        db.commit()
        print(f"Created {len(alerts_data)} demo alerts.")

        print("Data seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
