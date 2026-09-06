import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.main import app

def test_all():
    client = TestClient(app)
    
    # 1. Health & Root
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    print("[OK] GET / passed")

    # 2. Cameras
    r = client.get("/api/cameras")
    assert r.status_code == 200, f"Cameras failed: {r.text}"
    cameras = r.json()
    assert len(cameras) == 4, f"Expected 4 cameras, got {len(cameras)}"
    print(f"[OK] GET /api/cameras passed ({len(cameras)} cameras)")

    # 3. Detections
    r = client.get("/api/detections?limit=10")
    assert r.status_code == 200, f"Detections failed: {r.text}"
    dets = r.json()
    assert len(dets) > 0, "No detections returned"
    print(f"[OK] GET /api/detections passed ({len(dets)} returned)")

    # 4. Trajectory for TS09AB1234
    r = client.get("/api/trajectories/TS09AB1234")
    assert r.status_code == 200, f"Trajectory failed: {r.text}"
    traj = r.json()
    assert traj["plate_number"] == "TS09AB1234"
    assert len(traj["trajectory"]) == 4
    print(f"[OK] GET /api/trajectories/TS09AB1234 passed (4 steps: CAM-01 -> CAM-04 -> CAM-07 -> CAM-09)")

    # 5. Analytics Summary
    r = client.get("/api/analytics/summary")
    assert r.status_code == 200, f"Analytics failed: {r.text}"
    analytics = r.json()
    assert analytics["total_detections"] > 0
    assert len(analytics["volume_by_camera"]) == 4
    assert len(analytics["volume_by_interval"]) > 0
    print(f"[OK] GET /api/analytics/summary passed (Total dets: {analytics['total_detections']}, Peak interval: {analytics['peak_time_interval']['interval']})")

    # 6. Alerts
    r = client.get("/api/alerts")
    assert r.status_code == 200, f"Alerts failed: {r.text}"
    alerts = r.json()
    assert len(alerts) >= 2
    print(f"[OK] GET /api/alerts passed ({len(alerts)} alerts)")

    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all()
