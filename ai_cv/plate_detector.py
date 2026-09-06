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


def _is_valid_plate_aspect(w: int, h: int) -> bool:
    """Check if width/height ratio matches Indian license plate (approx 2.5–7.5)."""
    if h == 0:
        return False
    aspect = w / h
    return 2.0 <= aspect <= 8.5 and w > 40 and h > 10


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
    Effective for synthetic rendered plates where the plate is a white rectangle.
    """
    results = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()

    # Threshold for bright regions
    _, bright = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # Morphological closing to connect plate text pixels into solid rectangle
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    closed = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 800:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if _is_valid_plate_aspect(w, h):
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
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    bilateral = cv2.bilateralFilter(blurred, 11, 17, 17)
    edges = cv2.Canny(bilateral, 30, 200)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 800:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.018 * peri, True)
        if 4 <= len(approx) <= 6:
            x, y, w, h = cv2.boundingRect(approx)
            if _is_valid_plate_aspect(w, h):
                crop = _extract_crop(frame, x, y, w, h, margin=4)
                if crop.size > 0:
                    results.append((crop, (x, y, w, h)))

    return results


def _detect_morph_threshold(frame: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Strategy 3: Otsu threshold + morphology. Fallback for tricky lighting.
    """
    results = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 4))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:15]:
        area = cv2.contourArea(cnt)
        if area < 600:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if _is_valid_plate_aspect(w, h):
            crop = _extract_crop(frame, x, y, w, h, margin=3)
            if crop.size > 0:
                results.append((crop, (x, y, w, h)))

    return results


def detect_all_plate_regions(
    frame: np.ndarray,
    max_regions: int = 5
) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Run all three strategies and merge unique results by bounding box overlap.
    Returns list of (crop_image, (x, y, w, h)) tuples.
    """
    if frame is None or frame.size == 0:
        return []

    all_candidates = []
    all_candidates.extend(_detect_bright_rectangles(frame))
    all_candidates.extend(_detect_canny_contours(frame))
    all_candidates.extend(_detect_morph_threshold(frame))

    if not all_candidates:
        return []

    # Deduplicate by IoU: if two boxes overlap >50%, keep the larger
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
        if not any(iou(bbox, b) > 0.5 for _, b in unique):
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
