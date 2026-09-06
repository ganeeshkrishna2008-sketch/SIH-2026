"""
ai_cv/synthetic_test_generator.py

Generates synthetic test images with rendered Indian-format license plates.
Used as Phase 2 authorized test data when no real video is available.

This allows full end-to-end ANPR pipeline testing without requiring a physical camera.
Generated plates are clearly labeled as synthetic/test data.
"""
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "test_frames"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _render_plate_on_image(
    bg_width: int,
    bg_height: int,
    plate_text: str,
    plate_x_ratio: float = 0.3,
    plate_y_ratio: float = 0.55,
) -> np.ndarray:
    """
    Create a synthetic road scene image with a white rectangular plate bearing plate_text.
    Simulates a camera capture of a vehicle in a lane.
    """
    # Background: dark asphalt grey road
    frame = np.full((bg_height, bg_width, 3), (45, 45, 50), dtype=np.uint8)

    # Add some road lane markings for realism
    lane_color = (120, 120, 120)
    cv2.line(frame, (bg_width // 3, 0), (bg_width // 3, bg_height), lane_color, 1)
    cv2.line(frame, (2 * bg_width // 3, 0), (2 * bg_width // 3, bg_height), lane_color, 1)
    # Dashed center line
    for y in range(0, bg_height, 40):
        cv2.line(frame, (bg_width // 2, y), (bg_width // 2, y + 20), (200, 200, 0), 2)

    # Vehicle body: dark rectangle
    veh_x1 = int(bg_width * 0.18)
    veh_y1 = int(bg_height * 0.15)
    veh_x2 = int(bg_width * 0.82)
    veh_y2 = int(bg_height * 0.90)
    cv2.rectangle(frame, (veh_x1, veh_y1), (veh_x2, veh_y2), (70, 90, 130), -1)

    # Windshield gradient (tinted)
    shield_x1 = veh_x1 + 20
    shield_y1 = veh_y1 + 10
    shield_x2 = veh_x2 - 20
    shield_y2 = veh_y1 + 80
    cv2.rectangle(frame, (shield_x1, shield_y1), (shield_x2, shield_y2), (20, 30, 60), -1)

    # License plate: white background, black text
    plate_w = int(bg_width * 0.38)
    plate_h = int(bg_height * 0.10)
    px = int(bg_width * plate_x_ratio)
    py = int(bg_height * plate_y_ratio)

    cv2.rectangle(frame, (px, py), (px + plate_w, py + plate_h), (240, 240, 240), -1)  # white plate
    cv2.rectangle(frame, (px, py), (px + plate_w, py + plate_h), (50, 50, 50), 2)      # border

    # Blue strip at top (Indian plate format)
    cv2.rectangle(frame, (px, py), (px + plate_w, py + int(plate_h * 0.25)), (200, 100, 0), -1)

    # Render plate text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_scale = plate_h / 50.0
    text_thickness = max(1, int(plate_h / 30))
    (tw, th), _ = cv2.getTextSize(plate_text, font, text_scale, text_thickness)
    tx = px + (plate_w - tw) // 2
    ty = py + plate_h - int(plate_h * 0.15)
    cv2.putText(frame, plate_text, (tx, ty), font, text_scale, (10, 10, 10), text_thickness, cv2.LINE_AA)

    # Headlights
    cv2.circle(frame, (veh_x1 + 30, veh_y2 - 25), 12, (230, 230, 200), -1)
    cv2.circle(frame, (veh_x2 - 30, veh_y2 - 25), 12, (230, 230, 200), -1)

    # Add mild noise for realism
    noise = np.random.randint(0, 12, frame.shape, dtype=np.uint8)
    frame = cv2.add(frame, noise)

    return frame


def generate_test_frames(
    plates: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    resolution: Tuple[int, int] = (640, 480),
    noise_level: str = "low",  # "low", "medium", "high"
) -> List[Tuple[str, str]]:
    """
    Generate synthetic test frames for a list of plate strings.
    Returns list of (image_path, plate_text) tuples.

    Args:
        plates: License plate strings to render. Defaults to a preset demo set.
        output_dir: Where to save frames. Defaults to data/test_frames/
        resolution: (width, height) of generated frames
        noise_level: Amount of blur/compression noise to apply
    """
    if plates is None:
        plates = [
            "TS09AB1234",
            "DL01CZ4567",
            "KA05MH8899",
            "MH12TR3321",
            "HR26DQ5544",
            "AP09BK7788",
        ]

    if output_dir is None:
        output_dir = TEST_DATA_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    w, h = resolution

    for idx, plate in enumerate(plates):
        # Vary plate position slightly for robustness testing
        x_ratio = 0.25 + (idx % 3) * 0.05
        y_ratio = 0.50 + (idx % 2) * 0.05

        frame = _render_plate_on_image(w, h, plate, x_ratio, y_ratio)

        # Apply noise
        if noise_level == "medium":
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
        elif noise_level == "high":
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            # Add JPEG compression artifacts
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            _, encoded = cv2.imencode(".jpg", frame, encode_param)
            frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

        filename = f"synth_{plate}_{idx:02d}.jpg"
        filepath = str(output_dir / filename)
        cv2.imwrite(filepath, frame)
        results.append((filepath, plate))
        print(f"[GEN] Generated synthetic test frame: {filepath}")

    print(f"[GEN] Created {len(results)} synthetic test frames in {output_dir}")
    return results


def generate_synthetic_video(
    plates: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    fps: float = 10.0,
    frames_per_plate: int = 15,
    resolution: Tuple[int, int] = (640, 480),
) -> str:
    """
    Generate a synthetic MP4 video cycling through rendered plates.
    Each plate appears for `frames_per_plate` frames, simulating a vehicle passing through.

    Returns path to the generated video file.
    """
    if plates is None:
        plates = ["TS09AB1234", "DL01CZ4567", "KA05MH8899", "MH12TR3321"]

    if output_path is None:
        output_path = str(TEST_DATA_DIR / "synthetic_anpr_test.mp4")

    w, h = resolution
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for plate in plates:
        base_frame = _render_plate_on_image(w, h, plate)
        for f in range(frames_per_plate):
            # Add per-frame motion noise
            dx = np.random.randint(-2, 3)
            dy = np.random.randint(-2, 3)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            jitter = cv2.warpAffine(base_frame, M, (w, h))
            # Add random brightness variation
            brightness = np.random.randint(-8, 9)
            jitter = np.clip(jitter.astype(np.int16) + brightness, 0, 255).astype(np.uint8)
            writer.write(jitter)

    writer.release()
    print(f"[GEN] Generated synthetic test video: {output_path}")
    print(f"[GEN] Contains {len(plates)} plates × {frames_per_plate} frames each at {fps}fps")
    return output_path
