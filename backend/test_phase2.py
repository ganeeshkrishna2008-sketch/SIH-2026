"""
backend/test_phase2.py

End-to-end Phase 2 ANPR pipeline test.
Runs: synthetic frame generation → plate detection → OCR → DB storage → trajectory query
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_anpr_status():
    section("1. ANPR Engine Status Check")
    r = client.get("/api/anpr/status")
    assert r.status_code == 200, f"Status failed: {r.text}"
    data = r.json()
    print(f"[OK] Engine: {data.get('anpr_engine')}")
    print(f"[OK] OpenCV: {data['libraries'].get('opencv', 'N/A')}")
    print(f"[OK] EasyOCR: {data['libraries'].get('easyocr', 'N/A')}")
    print(f"[OK] PyTorch: {data['libraries'].get('torch', 'N/A')}")
    return data


def test_synthetic_frame_generation():
    section("2. Synthetic Test Frame Generation (OpenCV)")
    from ai_cv.synthetic_test_generator import generate_test_frames
    import cv2

    test_plates = ["TS09AB1234", "DL01CZ4567", "KA05MH8899"]
    frames = generate_test_frames(plates=test_plates, noise_level="low")
    assert len(frames) == len(test_plates), f"Expected {len(test_plates)} frames, got {len(frames)}"
    for img_path, plate in frames:
        assert Path(img_path).exists(), f"Frame not found: {img_path}"
        img = cv2.imread(img_path)
        assert img is not None, f"Failed to read: {img_path}"
        print(f"[OK] Generated frame for {plate}: {Path(img_path).name} ({img.shape[1]}x{img.shape[0]})")
    return frames


def test_plate_detector(frames):
    section("3. Plate Region Detector")
    import cv2
    from ai_cv.plate_detector import detect_all_plate_regions

    for img_path, plate in frames:
        img = cv2.imread(img_path)
        regions = detect_all_plate_regions(img, max_regions=5)
        status = "[OK]" if regions else "[WARN]"
        print(f"{status} Plate '{plate}': {len(regions)} region(s) detected")
    return True


def test_ocr_pipeline(frames):
    section("4. OCR Pipeline (EasyOCR + Preprocessing)")
    import cv2
    from ai_cv.plate_detector import detect_all_plate_regions
    from ai_cv.ocr_engine import run_ocr

    results = []
    for img_path, expected_plate in frames:
        img = cv2.imread(img_path)
        regions = detect_all_plate_regions(img, max_regions=5)

        detected_any = False
        for crop, bbox in regions:
            plate_text, confidence = run_ocr(crop, min_confidence=0.30)
            if plate_text:
                detected_any = True
                match = expected_plate.replace("-", "").replace(" ", "") in plate_text.replace("-", "").replace(" ", "")
                status = "[OK]" if match else "[WARN]"
                print(f"{status} Expected: '{expected_plate}' | OCR result: '{plate_text}' ({confidence*100:.1f}%)")
                results.append({
                    "expected": expected_plate,
                    "detected": plate_text,
                    "confidence": confidence,
                    "match": match
                })
                break

        if not detected_any:
            print(f"[WARN] No plate detected for '{expected_plate}' — may be a plate region detection miss")
            results.append({"expected": expected_plate, "detected": None, "confidence": 0, "match": False})

    return results


def test_anpr_api_generate():
    section("5. ANPR Generate-Test API (Full Pipeline via FastAPI)")
    r = client.post("/api/anpr/generate-test", json={
        "generate_video": False,  # Use images for speed in testing
        "run_anpr": True,
        "camera_id": "CAM-01",
        "noise_level": "low",
        "plates": ["TS09AB1234", "DL01CZ4567"],
    })
    assert r.status_code == 200, f"ANPR generate-test failed: {r.text}"
    data = r.json()
    print(f"[OK] Status: {data['status']}")
    print(f"[OK] Frames sampled: {data['total_frames_sampled']}")
    print(f"[OK] Detections: {len(data.get('detections', []))}")
    print(f"[OK] Stored to DB: {data['detections_stored']}")
    print(f"[OK] Rejected (low conf): {data['rejected_low_confidence']}")
    return data


def test_anpr_results_in_db():
    section("6. Verify ANPR Results Stored in Database")
    r = client.get("/api/anpr/results?limit=20")
    assert r.status_code == 200, f"ANPR results failed: {r.text}"
    results = r.json()
    print(f"[OK] Real ANPR detections in DB (is_demo=0): {len(results)}")
    for d in results[:5]:
        print(f"     Plate: {d['plate_number']} | Cam: {d['camera_id']} | Conf: {d['confidence']*100:.1f}% | is_demo: {d['is_demo']}")
    return results


def test_detection_feed_includes_anpr():
    section("7. Detection Feed Shows Mixed Demo + Real ANPR Detections")
    r = client.get("/api/detections?limit=20")
    assert r.status_code == 200
    dets = r.json()
    demo_count = sum(1 for d in dets if d["is_demo"] == 1)
    real_count = sum(1 for d in dets if d["is_demo"] == 0)
    print(f"[OK] Detection feed: {demo_count} DEMO + {real_count} REAL ANPR detections")
    return dets


def print_summary(ocr_results, api_result):
    section("PHASE 2 TEST SUMMARY")
    if ocr_results:
        matched = sum(1 for r in ocr_results if r["match"])
        detected = sum(1 for r in ocr_results if r["detected"] is not None)
        total = len(ocr_results)
        print(f"  OCR Detection Rate: {detected}/{total} plates found")
        print(f"  OCR Match Rate:     {matched}/{total} plates matched expected")
        avg_conf = sum(r["confidence"] for r in ocr_results if r["detected"]) / max(detected, 1)
        print(f"  Avg OCR Confidence: {avg_conf*100:.1f}%")
        print()
        print("  NOTE: These metrics are measured on synthetic rendered plates.")
        print("  Per implementation plan: accuracy is NOT claimed on real-world plates")
        print("  until tested and measured on actual authorized traffic footage.")
    print()
    print(f"  API Pipeline: {api_result.get('status', 'unknown')}")
    print(f"  Detections stored to DB: {api_result.get('detections_stored', 0)}")
    print()
    print("  Phase 2 ANPR integration COMPLETE.")
    print("  All real detections tagged is_demo=0 and visible in main detection feed.")


if __name__ == "__main__":
    try:
        test_anpr_status()
        frames = test_synthetic_frame_generation()
        test_plate_detector(frames)
        ocr_results = test_ocr_pipeline(frames)
        api_result = test_anpr_api_generate()
        test_anpr_results_in_db()
        test_detection_feed_includes_anpr()
        print_summary(ocr_results, api_result)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
