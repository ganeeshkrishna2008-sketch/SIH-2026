from fastapi.testclient import TestClient
from backend.app.main import app
import tempfile
import os

client = TestClient(app)

def test_upload():
    fd, path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(fd, 'wb') as f:
        f.write(b"dummy video content")
        
    with open(path, 'rb') as f:
        # Since dummy video will fail openCV parsing, we expect an error or 0 frames
        response = client.post(
            "/api/anpr/upload-video",
            files={"video": ("test.mp4", f, "video/mp4")},
            data={
                "camera_id": "CAM-01",
                "frame_sample_interval": "30",
                "min_confidence": "0.50"
            }
        )
    os.remove(path)
    print(response.status_code)
    print(response.json())

if __name__ == "__main__":
    test_upload()
