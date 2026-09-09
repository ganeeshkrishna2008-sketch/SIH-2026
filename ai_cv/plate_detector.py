"""
ai_cv/plate_detector.py

License plate detection using classical computer vision.
Supports both real-world frames and synthetic rendered test images.

Strategy order:
  1. Bright-rectangle detection (works on synthetic rendered plates)
  2. Canny + rectangular contour detection (works on real-world plates)
  3. Adaptive threshold + morphology (fallback)
"""
import cv2
import numpy as np
from typing import Optional, Tuple, List


def _is_valid_plate_aspect(w: int, h: int, frame_w: int = 1280, frame_h: int = 720) -> bool:
    """
    Check if bounding box dimensions match plausible license plate geometry:
      - Standard Indian plate: ~4.16 aspect ratio (500mm x 120mm)
      - Two-line / motorcycle: ~2.0 - 2.5 aspect ratio (200mm x 100mm)
      - Upper limits prevent treating entire roads, tree lines, or car hoods as plates
    """
    if h <= 0 or w <= 0:
        return False
    aspect = w / h
    area = w * h

    # Aspect ratio bounds
    if not (1.6 <= aspect <= 7.5):
        return False

    # Minimum size (reject tiny noise)
    if w < 35 or h < 10 or area < 400:
        return False

    # Maximum size relative to frame (reject roads, buildings, entire cars)
    if w > int(frame_w * 0.40) or h > int(frame_h * 0.22) or area > 45000:
        return False

    return True


def _score_plate_candidate(w: int, h: int) -> float:
    """Score candidate by closeness to typical Indian license plate aspect ratios."""
    if h == 0:
        return 0.0
    aspect = w / h
    score_std = 1.0 / (1.0 + abs(aspect - 4.16))
    score_sq = 1.0 / (1.0 + abs(aspect - 2.2))
    return max(score_std, score_sq)


def _extract_crop(frame: np.ndarray, x: int, y: int, w: int, h: int, margin: int = 5) -> np.ndarray:
    h_img, w_img = frame.shape[:2]
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(w_img, x + w + margin)
    y2 = min(h_img, y + h + margin)
    return frame[y1:y2, x1:x2]


def _detect_bright_rectangles(frame: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Strategy 1: Find bright (white/light) rectangular blobs on darker background.
    Effective for high-contrast plates and synthetic rendered plates.
    """
    results = []
    h_img, w_img = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()

    # Threshold for bright regions
    _, bright = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # Morphological closing to connect plate text pixels into solid rectangle
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    closed = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if _is_valid_plate_aspect(w, h, w_img, h_img):
            score = _score_plate_candidate(w, h)
            candidates.append((score, (x, y, w, h)))

    candidates.sort(key=lambda c: c[0], reverse=True)
    for _, (x, y, w, h) in candidates[:15]:
        crop = _extract_crop(frame, x, y, w, h, margin=3)
        if crop.size > 0:
            results.append((crop, (x, y, w, h)))

    return results


def _detect_canny_contours(frame: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Strategy 2: Bilateral filter + Canny edges + rectangular contour matching.
    Works well on real-world plate captures.
    """
    results = []
    h_img, w_img = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    bilateral = cv2.bilateralFilter(blurred, 11, 17, 17)
    edges = cv2.Canny(bilateral, 30, 200)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if 4 <= len(approx) <= 8:
            x, y, w, h = cv2.boundingRect(approx)
            if _is_valid_plate_aspect(w, h, w_img, h_img):
                score = _score_plate_candidate(w, h)
                candidates.append((score, (x, y, w, h)))

    candidates.sort(key=lambda c: c[0], reverse=True)
    for _, (x, y, w, h) in candidates[:20]:
        crop = _extract_crop(frame, x, y, w, h, margin=4)
        if crop.size > 0:
            results.append((crop, (x, y, w, h)))

    return results


def _detect_morph_threshold(frame: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Strategy 3: Otsu threshold + morphology. Fallback for tricky lighting.
    """
    results = []
    h_img, w_img = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 4))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if _is_valid_plate_aspect(w, h, w_img, h_img):
            score = _score_plate_candidate(w, h)
            candidates.append((score, (x, y, w, h)))

    candidates.sort(key=lambda c: c[0], reverse=True)
    for _, (x, y, w, h) in candidates[:15]:
        crop = _extract_crop(frame, x, y, w, h, margin=3)
        if crop.size > 0:
            results.append((crop, (x, y, w, h)))

    return results


def detect_all_plate_regions(
    frame: np.ndarray,
    max_regions: int = 5
) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Run detection strategies and merge unique candidate regions by bounding box overlap.
    Returns list of (crop_image, (x, y, w, h)) tuples.
    """
    if frame is None or frame.size == 0:
        return []

    h_img, w_img = frame.shape[:2]
    all_candidates = []

    # 1. Overlay panel region (common in traffic surveillance cameras & ANPR feeds)
    overlay_w = min(360, int(w_img * 0.30))
    overlay_h = min(180, int(h_img * 0.25))
    overlay_crop = frame[0:overlay_h, 0:overlay_w]
    if overlay_crop.size > 0:
        all_candidates.append((overlay_crop, (0, 0, overlay_w, overlay_h)))

    # 2. Geometric candidate detection (Canny, Bright Rectangles, Morphology)
    all_candidates.extend(_detect_bright_rectangles(frame))
    all_candidates.extend(_detect_canny_contours(frame))
    all_candidates.extend(_detect_morph_threshold(frame))

    if not all_candidates:
        return []

    # Deduplicate by IoU: if two boxes overlap >40%, keep the first
    def iou(b1, b2):
        x1, y1, w1, h1 = b1
        x2, y2, w2, h2 = b2
        ix = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        iy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        inter = ix * iy
        union = w1 * h1 + w2 * h2 - inter
        return inter / max(union, 1)

    unique = []
    for crop, bbox in all_candidates:
        if not any(iou(bbox, b) > 0.40 for _, b in unique):
            unique.append((crop, bbox))
        if len(unique) >= max_regions:
            break

    return unique


def detect_plate_region(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Convenience function: return the single best plate crop, or None.
    """
    regions = detect_all_plate_regions(frame, max_regions=1)
    if regions:
        return regions[0][0]
    return None
