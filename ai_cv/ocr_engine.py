"""
ai_cv/ocr_engine.py

OCR engine for license plate text extraction.
Uses EasyOCR as primary backend.
Includes:
  - Pre-processing pipeline (upscale, sharpen, threshold) to improve OCR accuracy
  - Post-processing with Indian plate format normalization
  - Conservative confidence handling: low-confidence results are NOT silently corrected
"""
import re
import numpy as np
from typing import Optional, Tuple, Any

# Lazy-import EasyOCR to avoid crashes at startup if not installed yet
_reader = None

def _get_reader():
    """Lazy-initialize EasyOCR reader (English only). Downloads model on first call."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader


def preprocess_for_ocr(crop: np.ndarray) -> np.ndarray:
    """
    Enhance a plate crop for EasyOCR:
      1. Upscale if too small (EasyOCR performs better with taller text)
      2. Convert to grayscale
      3. Apply CLAHE contrast enhancement for sharp, legible characters without binarization artifacts
    """
    import cv2
    h, w = crop.shape[:2]

    # Upscale if too small
    target_h = 100
    if 0 < h < target_h:
        scale = target_h / h
        crop = cv2.resize(crop, (int(w * scale), target_h), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced


def normalize_plate(raw_text: str) -> str:
    """
    Normalize a raw OCR string to a canonical Indian license plate format.
    Indian format: [State-Code (2 alpha)] [District (1-2 digits)] [Series (0-3 alpha)] [Number (1-4 digits)]
    Examples: TS09AB1234, DL01CZ4567, KA05MH8899, KA02MN1826, 21BH1234AA

    Rules:
      - Remove all whitespace and special characters except alphanumeric
      - Convert to uppercase
      - Reject any non-matching string (e.g. CAMERA, SAFEPRO, ROAD)
    """
    if not raw_text:
        return ""
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper().strip())

    if len(cleaned) < 5 or len(cleaned) > 12:
        return ""

    # Validate against standard Indian license plate patterns
    # Pattern 1: Standard (e.g. TS09AB1234, DL1C1234, KA02MN1826)
    std_pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{1,4}$'

    # Pattern 2: Bharat Series (e.g. 21BH1234AA)
    bh_pattern = r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$'

    if re.match(std_pattern, cleaned) or re.match(bh_pattern, cleaned):
        return cleaned

    return ""


def run_ocr(
    crop: np.ndarray,
    min_confidence: float = 0.50,
    return_details: bool = False,
) -> Any:
    """
    Run EasyOCR on a plate crop.
    Evaluates candidate text tokens and token combinations.
    
    If return_details=False (default):
      returns (normalized_plate_text, confidence)
    If return_details=True:
      returns (normalized_plate_text, confidence, decision, reason, raw_text)
    """
    if crop is None or crop.size == 0:
        if return_details:
            return None, 0.0, "REJECTED", "Empty crop image", ""
        return None, 0.0

    try:
        reader = _get_reader()

        # Try enhanced grayscale first (CLAHE)
        preprocessed = preprocess_for_ocr(crop)
        results = reader.readtext(preprocessed, detail=1, paragraph=False)

        # Also inspect original color crop for comparison
        direct_results = reader.readtext(crop, detail=1, paragraph=False)
        if direct_results:
            if not results:
                results = direct_results
            else:
                results.extend(direct_results)

        if not results:
            if return_details:
                return None, 0.0, "REJECTED", "No OCR text detected", ""
            return None, 0.0

        raw_strings = [r[1].strip() for r in results if r[1].strip()]
        first_raw = raw_strings[0] if raw_strings else ""
        valid_candidates = []

        # 1. Evaluate individual tokens
        for _, text, conf in results:
            cleaned = text.strip()
            if cleaned:
                norm = normalize_plate(cleaned)
                if norm:
                    valid_candidates.append((norm, float(conf), cleaned))

        # 2. Evaluate combinations of consecutive tokens (for multi-line or split plates)
        n = len(results)
        for i in range(n):
            for j in range(i + 2, min(i + 5, n + 1)):
                joined = ' '.join(r[1].strip() for r in results[i:j])
                norm = normalize_plate(joined)
                if norm:
                    avg_c = float(sum(r[2] for r in results[i:j]) / (j - i))
                    valid_candidates.append((norm, avg_c, joined))

        # 3. Evaluate full concatenation as fallback
        all_text = ''.join(r[1].strip() for r in results if r[1].strip())
        norm_all = normalize_plate(all_text)
        if norm_all:
            avg_all = float(sum(r[2] for r in results) / len(results))
            valid_candidates.append((norm_all, avg_all, all_text))

        if valid_candidates:
            # Sort by confidence descending
            valid_candidates.sort(key=lambda x: x[1], reverse=True)
            best_plate, best_conf, best_raw = valid_candidates[0]

            if best_conf >= min_confidence:
                if return_details:
                    return best_plate, round(best_conf, 4), "ACCEPTED", "Valid Indian plate format", best_raw
                return best_plate, round(best_conf, 4)
            else:
                if return_details:
                    return None, round(best_conf, 4), "REJECTED", f"Low confidence ({best_conf*100:.1f}% < {min_confidence*100:.0f}%)", best_raw
                return None, round(best_conf, 4)

        # No valid plate format was found among detected text tokens
        if return_details:
            return None, 0.0, "REJECTED", f"Invalid plate format (read: '{first_raw}')", first_raw
        return None, 0.0

    except Exception as e:
        print(f"[OCR] Error during OCR processing: {e}")
        if return_details:
            return None, 0.0, "REJECTED", f"OCR error: {e}", ""
        return None, 0.0
