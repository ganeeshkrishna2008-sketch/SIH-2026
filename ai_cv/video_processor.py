"""
ai_cv/video_processor.py

Phase 2 Video Processing Pipeline:
  Video/Image input → Frame extraction → Plate region detection → OCR → Observation records

Key design decisions per implementation plan:
  - Works on authorized local test video files or synthetic test frames
  - Every observation is tagged with camera_id, timestamp, and confidence
  - Low-confidence OCR results are logged but NOT stored as detections
  - Annotated frames are saved to disk for display in the frontend
  - Does NOT claim real-time city-wide performance; designed for demo validation
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import cv2
import numpy as np

from ai_cv.plate_detector import detect_plate_region, detect_all_plate_regions
from ai_cv.ocr_engine import run_ocr


# Minimum OCR confidence to store as a real detection
MIN_CONFIDENCE_THRESHOLD = 0.50

# Directory for annotated output frames
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "anpr_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _annotate_frame(frame: np.ndarray, plate_regions: list, detections: list) -> np.ndarray:
    """Draw bounding boxes and plate text on the frame for visualization."""
    annotated = frame.copy()

    for crop, (x, y, w, h) in plate_regions:
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 200, 255), 2)

    for det in detections:
        plate = det.get("plate_number", "??")
        conf = det.get("confidence", 0)
        if conf > 0:
            label = f"{plate} ({conf*100:.0f}%)"
            cv2.putText(annotated, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 100), 2)

    return annotated


def process_video(
    video_path: str,
    camera_id: str = "CAM-ANPR",
    location_name: str = "ANPR Processing Zone",
    latitude: float = 17.3850,
    longitude: float = 78.4867,
    direction: str = "Northbound",
    frame_sample_interval: int = 30,  # Process every Nth frame
    min_confidence: float = MIN_CONFIDENCE_THRESHOLD,
    save_annotated: bool = True,
) -> Dict[str, Any]:
    """
    Process an authorized video file through the ANPR pipeline.

    Args:
        video_path: Absolute path to the local video file
        camera_id: Camera identifier to tag detections with
        location_name: Human-readable location description
        latitude/longitude: Camera coordinates for trajectory tracking
        direction: Vehicle movement direction at this camera
        frame_sample_interval: Sample every Nth frame (default 30 = ~1/sec at 30fps)
        min_confidence: Minimum OCR confidence to record a detection
        save_annotated: Save annotated output frames to disk

    Returns:
        {
            "status": "completed" | "error",
            "total_frames_processed": int,
            "detections": [...],
            "rejected_low_confidence": int,
            "output_dir": str,
            "duration_seconds": float,
        }
    """
    if not os.path.isfile(video_path):
        return {"status": "error", "message": f"Video file not found: {video_path}"}

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"status": "error", "message": f"Failed to open video: {video_path}"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_name = Path(video_path).stem

    print(f"[ANPR] Processing: {video_path}")
    print(f"[ANPR] Camera: {camera_id} | FPS: {fps:.1f} | Total Frames: {total_frames}")

    # Base timestamp for this video session (can be overridden)
    base_timestamp = datetime.utcnow()

    detections: List[Dict[str, Any]] = []
    rejected_count = 0
    frames_processed = 0
    frame_index = 0
    annotated_paths: List[str] = []

    start_time = time.time()

    while True:
        if time.time() - start_time > 25.0:
            print("[ANPR] Max processing time (25s) reached to prevent HTTP timeout. Stopping early.")
            break

        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_sample_interval == 0:
            frames_processed += 1
            frame_timestamp = base_timestamp + timedelta(seconds=frame_index / fps)

            # Detect plate regions in this frame
            plate_regions = detect_all_plate_regions(frame, max_regions=3)

            # Fallback: use lower half of frame if no regions found
            if not plate_regions:
                h_f, w_f = frame.shape[:2]
                lower = frame[h_f // 2:, :]
                plate_regions = [(lower, (0, h_f // 2, w_f, h_f // 2))]

            frame_detections = []
            for crop, bbox in plate_regions:
                plate_text, confidence = run_ocr(crop, min_confidence=min_confidence)

                if plate_text and confidence >= min_confidence:
                    detection = {
                        "camera_id": camera_id,
                        "plate_number": plate_text,
                        "confidence": round(confidence, 4),
                        "location_name": location_name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "direction": direction,
                        "timestamp": frame_timestamp.isoformat(),
                        "vehicle_type": "Other",  # Phase 3: will add vehicle classifier
                        "frame_index": frame_index,
                        "is_demo": 0,  # 0 = REAL ANPR detection (not synthetic)
                        "source": "anpr_video",
                    }
                    frame_detections.append(detection)
                    detections.append(detection)
                    print(f"[ANPR] Frame {frame_index}: Detected '{plate_text}' (conf={confidence:.2f})")
                elif plate_text is None and confidence > 0:
                    # Plate region found but OCR confidence too low — log only
                    rejected_count += 1
                    print(f"[ANPR] Frame {frame_index}: Plate region found but low confidence ({confidence:.2f}) — skipped")

            # Save annotated frame for visualization
            if save_annotated and plate_regions:
                annotated = _annotate_frame(frame, plate_regions, frame_detections)
                out_path = str(OUTPUT_DIR / f"{video_name}_frame_{frame_index:06d}.jpg")
                cv2.imwrite(out_path, annotated)
                annotated_paths.append(out_path)

        frame_index += 1

    cap.release()
    elapsed = round(time.time() - start_time, 2)

    print(f"[ANPR] Done. Frames processed: {frames_processed}, Detections: {len(detections)}, Rejected: {rejected_count}")

    return {
        "status": "completed",
        "video_path": video_path,
        "camera_id": camera_id,
        "total_frames_sampled": frames_processed,
        "total_frames": total_frames,
        "detections": detections,
        "rejected_low_confidence": rejected_count,
        "annotated_frames": annotated_paths,
        "output_dir": str(OUTPUT_DIR),
        "duration_seconds": elapsed,
    }


def process_single_image(
    image_path: str,
    camera_id: str = "CAM-ANPR",
    location_name: str = "ANPR Processing Zone",
    latitude: float = 17.3850,
    longitude: float = 78.4867,
    direction: str = "Northbound",
    min_confidence: float = MIN_CONFIDENCE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Process a single image file (useful for testing with synthetic plates).
    Returns the same structure as process_video for API compatibility.
    """
    if not os.path.isfile(image_path):
        return {"status": "error", "message": f"Image file not found: {image_path}"}

    frame = cv2.imread(image_path)
    if frame is None:
        return {"status": "error", "message": f"Failed to read image: {image_path}"}

    plate_regions = detect_all_plate_regions(frame, max_regions=5)

    # Fallback: if no regions found by contour detection, try OCR on lower-half of frame
    # (where license plates usually appear on vehicles)
    if not plate_regions:
        h, w = frame.shape[:2]
        lower_half = frame[h // 2:, :]
        plate_regions = [( lower_half, (0, h // 2, w, h // 2) )]
    detections = []
    rejected_count = 0

    for crop, bbox in plate_regions:
        plate_text, confidence = run_ocr(crop, min_confidence=min_confidence)
        if plate_text and confidence >= min_confidence:
            detections.append({
                "camera_id": camera_id,
                "plate_number": plate_text,
                "confidence": round(confidence, 4),
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "direction": direction,
                "timestamp": datetime.utcnow().isoformat(),
                "vehicle_type": "Other",
                "frame_index": 0,
                "is_demo": 0,
                "source": "anpr_image",
            })
        elif plate_text is None and confidence > 0:
            rejected_count += 1

    # Save annotated image
    annotated = _annotate_frame(frame, plate_regions, detections)
    out_name = Path(image_path).stem + "_annotated.jpg"
    out_path = str(OUTPUT_DIR / out_name)
    cv2.imwrite(out_path, annotated)

    return {
        "status": "completed",
        "image_path": image_path,
        "camera_id": camera_id,
        "total_frames_sampled": 1,
        "detections": detections,
        "rejected_low_confidence": rejected_count,
        "annotated_frames": [out_path],
        "output_dir": str(OUTPUT_DIR),
        "duration_seconds": 0,
    }
