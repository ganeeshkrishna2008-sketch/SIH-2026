"""
ai_cv/__init__.py — Phase 2 ANPR/OCR CV module.
"""
from ai_cv.plate_detector import detect_plate_region, detect_all_plate_regions
from ai_cv.ocr_engine import run_ocr, normalize_plate
from ai_cv.video_processor import process_video, process_single_image
from ai_cv.synthetic_test_generator import generate_test_frames, generate_synthetic_video

__all__ = [
    "detect_plate_region", "detect_all_plate_regions",
    "run_ocr", "normalize_plate",
    "process_video", "process_single_image",
    "generate_test_frames", "generate_synthetic_video",
]
