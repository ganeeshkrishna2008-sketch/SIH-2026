"""
backend/app/routers/anpr.py

REST API endpoints for Phase 2 ANPR pipeline:
  POST /api/anpr/process-image   — Process a single image file
  POST /api/anpr/process-video   — Process a local video file
  GET  /api/anpr/status          — ANPR engine status and library versions
  GET  /api/anpr/results         — Recent ANPR processing results (stored in DB)
  POST /api/anpr/generate-test   — Generate synthetic test data and optionally process it
"""
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.detection import Detection
from app.models.camera import Camera
from app.schemas.detection import DetectionResponse

# Path to ai_cv module (project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

router = APIRouter(prefix="/anpr", tags=["ANPR Phase 2"])


# ─── Request/Response models ───────────────────────────────────────────────────

class ProcessImageRequest(BaseModel):
    image_path: str
    camera_id: str = "CAM-01"
    min_confidence: float = 0.50

class ProcessVideoRequest(BaseModel):
    video_path: str
    camera_id: str = "CAM-01"
    frame_sample_interval: int = 30
    min_confidence: float = 0.50

class GenerateTestRequest(BaseModel):
    plates: Optional[List[str]] = None
    generate_video: bool = True
    run_anpr: bool = True
    camera_id: str = "CAM-01"
    noise_level: str = "low"  # "low", "medium", "high"
    min_confidence: float = 0.30  # Lower default for synthetic rendered plates

class ANPRResult(BaseModel):
    status: str
    camera_id: str
    total_frames_sampled: int
    detections_stored: int
    rejected_low_confidence: int
    detections: list
    annotated_frames: list
    duration_seconds: float
    message: Optional[str] = None


# ─── Helper: store detections from ANPR result into DB ────────────────────────

def _store_detections_in_db(db: Session, anpr_result: dict, camera_id: str) -> int:
    """Write ANPR detections to the DB detection table, returning count stored."""
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()

    stored = 0
    for det_data in anpr_result.get("detections", []):
        # Parse timestamp
        ts_str = det_data.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:
            ts = datetime.utcnow()

        detection = Detection(
            camera_id=det_data.get("camera_id", camera_id),
            plate_number=det_data.get("plate_number", "UNKNOWN"),
            vehicle_type=det_data.get("vehicle_type", "Other"),
            confidence=det_data.get("confidence", 0.0),
            location_name=cam.location_name if cam else det_data.get("location_name", "ANPR Zone"),
            direction=cam.direction if cam else det_data.get("direction", "Unknown"),
            latitude=cam.latitude if cam else det_data.get("latitude", 17.3850),
            longitude=cam.longitude if cam else det_data.get("longitude", 78.4867),
            timestamp=ts,
            is_demo=0,  # Real ANPR detection
        )
        db.add(detection)
        stored += 1

    if stored > 0:
        db.commit()
    return stored


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
def get_anpr_status():
    """Return ANPR engine availability and installed library versions."""
    status = {
        "anpr_engine": "Phase 2 — Active",
        "libraries": {}
    }

    try:
        import cv2
        status["libraries"]["opencv"] = cv2.__version__
        status["opencv_available"] = True
    except ImportError:
        status["libraries"]["opencv"] = "Not installed"
        status["opencv_available"] = False

    try:
        import easyocr
        status["libraries"]["easyocr"] = easyocr.__version__
        status["easyocr_available"] = True
    except ImportError:
        status["libraries"]["easyocr"] = "Not installed"
        status["easyocr_available"] = False

    try:
        import torch
        status["libraries"]["torch"] = torch.__version__
    except ImportError:
        status["libraries"]["torch"] = "Not installed"

    status["test_data_dir"] = str(PROJECT_ROOT / "data" / "test_frames")
    status["output_dir"] = str(PROJECT_ROOT / "data" / "anpr_output")

    return status


@router.post("/generate-test", response_model=ANPRResult)
def generate_and_process_test(
    req: GenerateTestRequest = Body(default=GenerateTestRequest()),
    db: Session = Depends(get_db)
):
    """
    Generate synthetic test frames with rendered license plates and optionally
    run the full ANPR pipeline on them. Stores results in the database.
    """
    try:
        from ai_cv.synthetic_test_generator import generate_test_frames, generate_synthetic_video
        from ai_cv.video_processor import process_video, process_single_image
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ANPR libraries not available: {e}. Install opencv-python-headless and easyocr."
        )

    cam = db.query(Camera).filter(Camera.camera_id == req.camera_id).first()
    cam_location = cam.location_name if cam else "ANPR Test Zone"
    cam_lat = cam.latitude if cam else 17.3850
    cam_lon = cam.longitude if cam else 78.4867
    cam_dir = cam.direction if cam else "Northbound"

    all_detections = []
    rejected_count = 0
    annotated_frames = []
    total_frames_sampled = 0

    if req.generate_video:
        # Generate a synthetic test video and process it
        video_path = generate_synthetic_video(
            plates=req.plates,
            fps=10.0,
            frames_per_plate=15,
        )
        if req.run_anpr:
            result = process_video(
                video_path=video_path,
                camera_id=req.camera_id,
                location_name=cam_location,
                latitude=cam_lat,
                longitude=cam_lon,
                direction=cam_dir,
                frame_sample_interval=10,  # Every 10th frame for the short synthetic video
                min_confidence=req.min_confidence,
            )
            all_detections.extend(result.get("detections", []))
            rejected_count += result.get("rejected_low_confidence", 0)
            annotated_frames.extend(result.get("annotated_frames", []))
            total_frames_sampled += result.get("total_frames_sampled", 0)
    else:
        # Generate individual test images for each plate
        test_frames = generate_test_frames(
            plates=req.plates,
            noise_level=req.noise_level,
        )
        if req.run_anpr:
            for img_path, plate in test_frames:
                result = process_single_image(
                    image_path=img_path,
                    camera_id=req.camera_id,
                    location_name=cam_location,
                    latitude=cam_lat,
                    longitude=cam_lon,
                    direction=cam_dir,
                    min_confidence=req.min_confidence,
                )
                all_detections.extend(result.get("detections", []))
                rejected_count += result.get("rejected_low_confidence", 0)
                annotated_frames.extend(result.get("annotated_frames", []))
                total_frames_sampled += 1

    # Store detections in the existing DB
    stored_count = 0
    if req.run_anpr and all_detections:
        result_for_storage = {"detections": all_detections}
        stored_count = _store_detections_in_db(db, result_for_storage, req.camera_id)

    return ANPRResult(
        status="completed",
        camera_id=req.camera_id,
        total_frames_sampled=total_frames_sampled,
        detections_stored=stored_count,
        rejected_low_confidence=rejected_count,
        detections=all_detections,
        annotated_frames=annotated_frames,
        duration_seconds=0,
        message=f"ANPR pipeline completed. {stored_count} detections stored, {rejected_count} rejected (low confidence)."
    )


@router.post("/process-image", response_model=ANPRResult)
def process_image_endpoint(req: ProcessImageRequest, db: Session = Depends(get_db)):
    """Process a single authorized image through the ANPR pipeline."""
    try:
        from ai_cv.video_processor import process_single_image
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"ANPR library missing: {e}")

    cam = db.query(Camera).filter(Camera.camera_id == req.camera_id).first()

    result = process_single_image(
        image_path=req.image_path,
        camera_id=req.camera_id,
        location_name=cam.location_name if cam else "ANPR Zone",
        latitude=cam.latitude if cam else 17.3850,
        longitude=cam.longitude if cam else 78.4867,
        direction=cam.direction if cam else "Northbound",
        min_confidence=req.min_confidence,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Error processing image"))

    stored = _store_detections_in_db(db, result, req.camera_id)

    return ANPRResult(
        status="completed",
        camera_id=req.camera_id,
        total_frames_sampled=1,
        detections_stored=stored,
        rejected_low_confidence=result.get("rejected_low_confidence", 0),
        detections=result.get("detections", []),
        annotated_frames=result.get("annotated_frames", []),
        duration_seconds=result.get("duration_seconds", 0),
    )


@router.post("/process-video", response_model=ANPRResult)
def process_video_endpoint(req: ProcessVideoRequest, db: Session = Depends(get_db)):
    """Process an authorized local video file through the ANPR pipeline."""
    try:
        from ai_cv.video_processor import process_video
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"ANPR library missing: {e}")

    cam = db.query(Camera).filter(Camera.camera_id == req.camera_id).first()

    result = process_video(
        video_path=req.video_path,
        camera_id=req.camera_id,
        location_name=cam.location_name if cam else "ANPR Zone",
        latitude=cam.latitude if cam else 17.3850,
        longitude=cam.longitude if cam else 78.4867,
        direction=cam.direction if cam else "Northbound",
        frame_sample_interval=req.frame_sample_interval,
        min_confidence=req.min_confidence,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Error processing video"))

    stored = _store_detections_in_db(db, result, req.camera_id)

    return ANPRResult(
        status="completed",
        camera_id=req.camera_id,
        total_frames_sampled=result.get("total_frames_sampled", 0),
        detections_stored=stored,
        rejected_low_confidence=result.get("rejected_low_confidence", 0),
        detections=result.get("detections", []),
        annotated_frames=result.get("annotated_frames", []),
        duration_seconds=result.get("duration_seconds", 0),
    )


@router.get("/results", response_model=List[DetectionResponse])
def get_anpr_results(limit: int = 50, db: Session = Depends(get_db)):
    """Return real ANPR detections (is_demo=0) stored by the pipeline."""
    return (
        db.query(Detection)
        .filter(Detection.is_demo == 0)
        .order_by(Detection.timestamp.desc())
        .limit(limit)
        .all()
    )

@router.post("/upload-video", response_model=ANPRResult)
async def upload_video_endpoint(
    video: UploadFile = File(...),
    camera_id: str = Form("CAM-01"),
    frame_sample_interval: int = Form(30),
    min_confidence: float = Form(0.50),
    db: Session = Depends(get_db)
):
    """Process an uploaded video file through the ANPR pipeline."""
    try:
        from ai_cv.video_processor import process_video
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"ANPR library missing: {e}")

    # Validate file extension
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    ext = Path(video.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file format {ext}. Supported: {', '.join(allowed_extensions)}")

    # Save to temp file
    fd, temp_path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            shutil.copyfileobj(video.file, f)

        cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()

        result = process_video(
            video_path=temp_path,
            camera_id=camera_id,
            location_name=cam.location_name if cam else "ANPR Zone",
            latitude=cam.latitude if cam else 17.3850,
            longitude=cam.longitude if cam else 78.4867,
            direction=cam.direction if cam else "Northbound",
            frame_sample_interval=frame_sample_interval,
            min_confidence=min_confidence,
        )

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "Error processing video"))

        stored = _store_detections_in_db(db, result, camera_id)

        # Remove absolute paths from response to not leak server paths
        annotated = [Path(p).name for p in result.get("annotated_frames", [])]

        return ANPRResult(
            status="completed",
            camera_id=camera_id,
            total_frames_sampled=result.get("total_frames_sampled", 0),
            detections_stored=stored,
            rejected_low_confidence=result.get("rejected_low_confidence", 0),
            detections=result.get("detections", []),
            annotated_frames=annotated,
            duration_seconds=result.get("duration_seconds", 0),
        )
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
