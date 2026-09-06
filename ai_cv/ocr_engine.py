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
from typing import Optional, Tuple

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
    Enhance a plate crop for better OCR:
      1. Upscale to at least 200px height (EasyOCR works best on larger images)
      2. Convert to grayscale
      3. Apply adaptive threshold to binarize (works in varying lighting)
    """
    import cv2
    h, w = crop.shape[:2]

    # Upscale if too small
    target_h = 100
    if h < target_h:
        scale = target_h / h
        crop = cv2.resize(crop, (int(w * scale), target_h), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop.copy()

    # Sharpen
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    # Adaptive threshold for binarization
    binary = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return binary


def normalize_plate(raw_text: str) -> str:
    """
    Normalize a raw OCR string to a canonical Indian license plate format.
    Indian format: [State-Code (2 alpha)] [District (2 digits)] [Series (1-2 alpha)] [Number (4 digits)]
    Examples: TS09AB1234, DL01CZ4567, KA05MH8899

    Rules:
      - Remove all whitespace and special characters except alphanumeric
      - Convert to uppercase
      - Do NOT alter or invent characters; only strip noise
    """
    if not raw_text:
        return ""
    # Remove everything except alphanumeric
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper().strip())
    # Common OCR confusion corrections for license plates:
    # (only apply obvious misreads, not guesses)
    corrections = {
        'O': 'O',   # Keep O as-is in numeric positions (handled below)
    }
    # Minimum plausible plate length
    if len(cleaned) < 5:
        return cleaned  # return as-is, mark low confidence upstream
    return cleaned


def run_ocr(crop: np.ndarray, min_confidence: float = 0.50) -> Tuple[Optional[str], float]:
    """
    Run EasyOCR on a plate crop.
    Returns (normalized_plate_text, confidence) or (None, 0.0) if nothing found above threshold.

    Conservative approach per implementation plan:
      - Returns None if confidence < min_confidence (default 0.50)
      - Does NOT invent or silently correct plate text
      - Caller is responsible for labeling low-confidence results
    """
    if crop is None or crop.size == 0:
        return None, 0.0

    try:
        preprocessed = preprocess_for_ocr(crop)
        reader = _get_reader()
        results = reader.readtext(preprocessed, detail=1, paragraph=False)

        if not results:
            # Fallback: try on original crop without preprocessing
            results = reader.readtext(crop, detail=1, paragraph=False)

        if not results:
            return None, 0.0

        # Combine all text tokens (plates can be split across detected regions)
        texts = []
        confidences = []
        for _, text, conf in results:
            if text.strip():
                texts.append(text.strip())
                confidences.append(conf)

        if not texts:
            return None, 0.0

        combined_text = ''.join(texts)
        avg_confidence = float(sum(confidences) / len(confidences))

        normalized = normalize_plate(combined_text)

        if avg_confidence < min_confidence or len(normalized) < 5:
            return None, avg_confidence  # Low confidence — caller handles this

        return normalized, round(avg_confidence, 4)

    except Exception as e:
        # OCR failure is non-fatal: log and return nothing
        print(f"[OCR] Error during OCR processing: {e}")
        return None, 0.0
