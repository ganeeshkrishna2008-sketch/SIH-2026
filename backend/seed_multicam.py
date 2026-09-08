"""
backend/seed_multicam.py

Phase 3 -- Multi-Camera Demo Data Seeder

Adds synthetic multi-camera vehicle observations to demonstrate
cross-camera vehicle association. Designed to work WITH the existing
seed_data.py -- it re-seeds everything from scratch to ensure consistency.

ALL DATA IS CLEARLY MARKED AS DEMO/SYNTHETIC.

Demo Scenario:
  Vehicle A (TS09AB1234): CAM-01 -> CAM-04 -> CAM-07  (plausible times)
  Vehicle B (DL01CZ4567): CAM-02 -> CAM-05            (plausible times)
  Vehicle C (KA05MH8899): CAM-01 -> CAM-07            (plausible times)
  Vehicle D (MH12TR3321): CAM-02 -> CAM-04 -> CAM-09   (plausible times)
  Vehicle E with OCR variants: "TS 09 AB 1234" at CAM-09 (should merge with Vehicle A)
  Implausible test: Same plate at CAM-01 and CAM-07 within 20 seconds (should be flagged)
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Ensure backend root is on sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from app.database import engine, Base, SessionLocal
from app.models import Camera, Vehicle, Detection, Alert


def seed_multicam_database():
    print("=" * 60)
    print("  Phase 3 -- Multi-Camera Demo Data Seeder")
    print("=" * 60)
    print()

    print("Dropping and re-creating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # --- Cameras (6 cameras for Phase 3) ------------------------------
        print("Seeding 6 camera nodes...")
        cameras_data = [
            {
                "camera_id": "CAM-01",
                "name": "MG Road Junction Camera 01",
                "location_name": "MG Road / Central Junction",
                "latitude": 17.3850,
                "longitude": 78.4867,
                "direction": "Northbound",
                "status": "ACTIVE",
            },
            {
                "camera_id": "CAM-02",
                "name": "Begumpet Flyover Camera 02",
                "location_name": "Begumpet Flyover / NH65",
                "latitude": 17.4400,
                "longitude": 78.4700,
                "direction": "Northbound",
                "status": "ACTIVE",
            },
            {
                "camera_id": "CAM-04",
                "name": "Ring Road East Toll Camera 04",
                "location_name": "Outer Ring Road East Gate",
                "latitude": 17.4100,
                "longitude": 78.5200,
                "direction": "Eastbound",
                "status": "ACTIVE",
            },
            {
                "camera_id": "CAM-05",
                "name": "Miyapur Corridor Camera 05",
                "location_name": "Miyapur X-Roads / Metro Station",
                "latitude": 17.4950,
                "longitude": 78.3550,
                "direction": "Westbound",
                "status": "ACTIVE",
            },
            {
                "camera_id": "CAM-07",
                "name": "Cyber Towers Flyover Camera 07",
                "location_name": "HITEC City / Cyber Towers Corridor",
                "latitude": 17.4500,
                "longitude": 78.3800,
                "direction": "Westbound",
                "status": "ACTIVE",
            },
            {
                "camera_id": "CAM-09",
                "name": "Airport Expressway South Camera 09",
                "location_name": "Airport Expressway Exit 4",
                "latitude": 17.2400,
                "longitude": 78.4300,
                "direction": "Southbound",
                "status": "ACTIVE",
            },
        ]

        cam_objs = {}
        for c in cameras_data:
            cam = Camera(**c)
            db.add(cam)
            cam_objs[c["camera_id"]] = c  # store dict for convenience
        db.commit()
        print(f"  [OK] Created {len(cameras_data)} cameras")

        # --- Vehicles -----------------------------------------------------
        print("Seeding vehicles...")
        vehicles_data = [
            {"plate_number": "TS09AB1234", "vehicle_type": "Car", "color": "White",
             "is_watchlist": 0, "notes": "Primary demo vehicle -- crosses 4 cameras"},
            {"plate_number": "DL01CZ4567", "vehicle_type": "Car", "color": "Black",
             "is_watchlist": 0, "notes": "Secondary demo vehicle -- 2 cameras"},
            {"plate_number": "KA05MH8899", "vehicle_type": "Car", "color": "Silver",
             "is_watchlist": 1, "notes": "Authorized Watchlist Demo Subject"},
            {"plate_number": "MH12TR3321", "vehicle_type": "Bus", "color": "Blue",
             "is_watchlist": 0, "notes": "Intercity Transit -- 3 cameras"},
            {"plate_number": "HR26DQ5544", "vehicle_type": "Truck", "color": "Yellow",
             "is_watchlist": 0, "notes": "Logistics -- single camera"},
            {"plate_number": "AP09BK7788", "vehicle_type": "Motorcycle", "color": "Red",
             "is_watchlist": 0, "notes": "Delivery courier -- single camera"},
            {"plate_number": "UP32EF9900", "vehicle_type": "Car", "color": "Grey",
             "is_watchlist": 1, "notes": "Authorized Watchlist Demo Subject 2"},
            {"plate_number": "TN02AA4321", "vehicle_type": "Other", "color": "Green-Yellow",
             "is_watchlist": 0, "notes": "Urban Para-transit"},
        ]

        for v in vehicles_data:
            db.add(Vehicle(**v))
        db.commit()
        print(f"  [OK] Created {len(vehicles_data)} vehicles")

        # --- Multi-Camera Trajectories ------------------------------------
        print("Seeding multi-camera detection trajectories...")

        base_time = datetime.utcnow().replace(hour=9, minute=0, second=0, microsecond=0)

        def add_detection(plate, cam_id, ts, conf=0.96, v_type="Car"):
            """Helper to add a detection with full camera metadata."""
            cam = cam_objs[cam_id]
            db.add(Detection(
                camera_id=cam_id,
                plate_number=plate,
                vehicle_type=v_type,
                confidence=conf,
                location_name=cam["location_name"],
                direction=cam["direction"],
                latitude=cam["latitude"],
                longitude=cam["longitude"],
                timestamp=ts,
                is_demo=1,
            ))

        # -- Vehicle A: TS09AB1234 -- CAM-01 -> CAM-04 -> CAM-07 (plausible)
        print("  -> Vehicle A (TS09AB1234): CAM-01 -> CAM-04 -> CAM-07")
        add_detection("TS09AB1234", "CAM-01", base_time + timedelta(minutes=2, seconds=14), 0.98)
        add_detection("TS09AB1234", "CAM-04", base_time + timedelta(minutes=7, seconds=31), 0.96)
        add_detection("TS09AB1234", "CAM-07", base_time + timedelta(minutes=13, seconds=48), 0.97)

        # -- Vehicle A OCR variant at CAM-09 -- should merge with same track
        # Simulates OCR outputting "TS 09 AB 1234" with spaces
        print("  -> Vehicle A OCR variant (TS 09 AB 1234): CAM-09")
        add_detection("TS 09 AB 1234", "CAM-09", base_time + timedelta(minutes=25, seconds=0), 0.88)

        # -- Vehicle B: DL01CZ4567 -- CAM-02 -> CAM-05 (plausible)
        print("  -> Vehicle B (DL01CZ4567): CAM-02 -> CAM-05")
        add_detection("DL01CZ4567", "CAM-02", base_time + timedelta(minutes=5, seconds=0), 0.94, "Car")
        add_detection("DL01CZ4567", "CAM-05", base_time + timedelta(minutes=14, seconds=20), 0.95, "Car")

        # -- Vehicle C: KA05MH8899 -- CAM-01 -> CAM-07 (plausible)
        print("  -> Vehicle C (KA05MH8899): CAM-01 -> CAM-07")
        add_detection("KA05MH8899", "CAM-01", base_time + timedelta(minutes=10, seconds=0), 0.99)
        add_detection("KA05MH8899", "CAM-07", base_time + timedelta(minutes=18, seconds=45), 0.97)

        # -- Vehicle D: MH12TR3321 -- CAM-02 -> CAM-04 -> CAM-09 (plausible)
        print("  -> Vehicle D (MH12TR3321): CAM-02 -> CAM-04 -> CAM-09")
        add_detection("MH12TR3321", "CAM-02", base_time + timedelta(minutes=3, seconds=0), 0.93, "Bus")
        add_detection("MH12TR3321", "CAM-04", base_time + timedelta(minutes=12, seconds=0), 0.91, "Bus")
        add_detection("MH12TR3321", "CAM-09", base_time + timedelta(minutes=28, seconds=0), 0.90, "Bus")

        # -- Vehicle E: HR26DQ5544 -- single camera only (CAM-04)
        print("  -> Vehicle E (HR26DQ5544): CAM-04 only")
        add_detection("HR26DQ5544", "CAM-04", base_time + timedelta(minutes=8, seconds=30), 0.92, "Truck")

        # -- Vehicle F: AP09BK7788 -- single camera only (CAM-01)
        print("  -> Vehicle F (AP09BK7788): CAM-01 only")
        add_detection("AP09BK7788", "CAM-01", base_time + timedelta(minutes=6, seconds=15), 0.89, "Motorcycle")

        # -- Implausible Transition Test: TN02AA4321 at CAM-01 and CAM-07
        # within 20 seconds -- these cameras are ~12 km apart
        # This is physically impossible and should be flagged
        print("  -> Implausible test (TN02AA4321): CAM-01 -> CAM-07 in 20 seconds")
        add_detection("TN02AA4321", "CAM-01", base_time + timedelta(minutes=15, seconds=0), 0.95, "Other")
        add_detection("TN02AA4321", "CAM-07", base_time + timedelta(minutes=15, seconds=20), 0.93, "Other")

        db.commit()

        # -- Background traffic for realism --------------------------------
        print("Seeding background traffic volume...")
        random.seed(42)
        bg_plates = [
            (f"TS{random.randint(1,15):02d}{chr(random.randint(65,90))}{chr(random.randint(65,90))}{random.randint(1000,9999)}",
             random.choice(["Car", "Motorcycle", "Bus", "Truck", "Other"]))
            for _ in range(30)
        ]

        cam_ids = list(cam_objs.keys())
        interval_specs = [
            (0, 10, 20),   # 09:00-09:10
            (10, 20, 35),  # 09:10-09:20 (peak)
            (20, 30, 28),  # 09:20-09:30
            (30, 40, 22),  # 09:30-09:40
            (40, 50, 15),  # 09:40-09:50
            (50, 60, 12),  # 09:50-10:00
        ]

        bg_count = 0
        for start_min, end_min, count in interval_specs:
            for _ in range(count):
                plate, v_type = random.choice(bg_plates)
                cam_id = random.choice(cam_ids)
                cam = cam_objs[cam_id]
                offset_sec = random.randint(start_min * 60, end_min * 60 - 1)
                t_stamp = base_time + timedelta(seconds=offset_sec)
                conf = round(random.uniform(0.88, 0.99), 3)

                db.add(Detection(
                    camera_id=cam_id,
                    plate_number=plate,
                    vehicle_type=v_type,
                    confidence=conf,
                    location_name=cam["location_name"],
                    direction=cam["direction"],
                    latitude=cam["latitude"],
                    longitude=cam["longitude"],
                    timestamp=t_stamp,
                    is_demo=1,
                ))
                bg_count += 1

        db.commit()
        print(f"  [OK] Added {bg_count} background traffic detections")

        total_dets = db.query(Detection).count()
        print(f"  [OK] Total detections in database: {total_dets}")

        # --- Alerts -------------------------------------------------------
        print("Seeding authorized watchlist alerts...")
        alerts_data = [
            {
                "plate_number": "KA05MH8899",
                "camera_id": "CAM-01",
                "location_name": "MG Road / Central Junction",
                "timestamp": base_time + timedelta(minutes=10, seconds=0),
                "confidence": 0.99,
                "alert_type": "Authorized Watchlist Match — Requires Human Review",
                "status": "PENDING_REVIEW",
                "notes": "Matched Flagged Plate DB (Demo Entry). Pending operator confirmation.",
            },
            {
                "plate_number": "UP32EF9900",
                "camera_id": "CAM-02",
                "location_name": "Begumpet Flyover / NH65",
                "timestamp": base_time + timedelta(minutes=15, seconds=30),
                "confidence": 0.94,
                "alert_type": "Authorized Watchlist Match — Requires Human Review",
                "status": "REVIEWED",
                "reviewed_by": "Officer R. Sharma (Badge #4092)",
                "notes": "Verified by operator. Route logging active.",
            },
        ]
        for a in alerts_data:
            db.add(Alert(**a))
        db.commit()
        print(f"  [OK] Created {len(alerts_data)} demo alerts")

        # --- Summary -----------------------------------------------------
        print()
        print("=" * 60)
        print("  Multi-Camera Demo Data Seeding Complete!")
        print("=" * 60)
        print()
        print("  Demo Vehicles with Multi-Camera Trajectories:")
        print("    Vehicle A (TS09AB1234):  CAM-01 -> CAM-04 -> CAM-07 -> CAM-09")
        print("    Vehicle B (DL01CZ4567):  CAM-02 -> CAM-05")
        print("    Vehicle C (KA05MH8899):  CAM-01 -> CAM-07  [WATCHLIST]")
        print("    Vehicle D (MH12TR3321):  CAM-02 -> CAM-04 -> CAM-09")
        print("    Vehicle E (HR26DQ5544):  CAM-04 only")
        print("    Vehicle F (AP09BK7788):  CAM-01 only")
        print()
        print("  Test Cases Included:")
        print("    [OK] OCR variant merging: 'TS 09 AB 1234' -> 'TS09AB1234'")
        print("    [OK] Implausible transition: TN02AA4321 at CAM-01->CAM-07 in 20s")
        print("    [OK] Separate vehicles remain distinct")
        print("    [OK] Background traffic for analytics realism")
        print()

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_multicam_database()
