from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_camera_vehicles_endpoint():
    print("Testing GET /api/cameras/{camera_id}/vehicles")
    
    # Test valid camera
    res = client.get("/api/cameras/CAM-01/vehicles")
    assert res.status_code == 200
    data = res.json()
    assert data["camera_id"] == "CAM-01"
    assert "vehicles" in data
    
    # Test order
    vehicles = data["vehicles"]
    if len(vehicles) > 1:
        for i in range(len(vehicles) - 1):
            # desc order
            assert vehicles[i]["timestamp"] >= vehicles[i+1]["timestamp"]
            
    # Test invalid camera
    res = client.get("/api/cameras/INVALID_CAM/vehicles")
    assert res.status_code == 404
    
    print("All tests passed.")

if __name__ == "__main__":
    test_camera_vehicles_endpoint()

