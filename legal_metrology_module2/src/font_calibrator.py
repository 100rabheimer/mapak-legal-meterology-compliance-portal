import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional

class FontCalibrator:
    """
    Stage 3: Numeral Font Height Calibration & Statutory Rule 7 Verification.
    Calculates pixel-to-mm scale ratio k = mm / pixels, measures physical numeral height h_mm,
    and checks against Rule 7 statutory font size tables based on PDP Area (cm^2).
    """

    # Rule 7 Statutory Minimum Numeral Heights (in mm) based on PDP Area (cm^2)
    # Reference: Rule 7(2) Table of Legal Metrology (Packaged Commodities) Rules
    RULE_7_THRESHOLDS = [
        {"max_area": 50.0, "min_height_mm": 1.0, "min_height_molded_mm": 1.5, "label": "Area <= 50 cm^2"},
        {"max_area": 100.0, "min_height_mm": 1.5, "min_height_molded_mm": 2.0, "label": "50 cm^2 < Area <= 100 cm^2"},
        {"max_area": 500.0, "min_height_mm": 2.0, "min_height_molded_mm": 4.0, "label": "100 cm^2 < Area <= 500 cm^2"},
        {"max_area": float("inf"), "min_height_mm": 4.0, "min_height_molded_mm": 6.0, "label": "Area > 500 cm^2"},
    ]

    # Standard EAN-13 Barcode Height reference anchor (~25.93 mm)
    DEFAULT_BARCODE_HEIGHT_MM = 25.93

    def __init__(self, known_ref_mm: float = 25.93):
        self.known_ref_mm = known_ref_mm

    def compute_scale_ratio(self, image: np.ndarray, detected_ref_pixels: Optional[float] = None) -> float:
        """
        Computes scale ratio k = mm / pixel.
        If detected_ref_pixels is not provided, attempts to detect a barcode height or uses vertical DPI estimate.
        """
        if detected_ref_pixels and detected_ref_pixels > 0:
            return self.known_ref_mm / float(detected_ref_pixels)

        # Attempt to detect barcode height using OpenCV barcode detector / edge gradient
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Calculate vertical Sobel gradient to detect vertical barcode lines
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=-1)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=-1)
        gradient = cv2.subtract(grad_x, grad_y)
        gradient = cv2.convertScaleAbs(gradient)
        blurred = cv2.blur(gradient, (9, 9))
        _, thresh = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        barcode_px_height = None
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = float(bw) / bh
            if 1.5 <= aspect_ratio <= 4.0 and bh > (h * 0.05):
                barcode_px_height = bh
                break

        if barcode_px_height:
            return self.known_ref_mm / float(barcode_px_height)

        # Fallback scale ratio estimation (assuming standard PDP scanning resolution ~ 150 DPI = ~5.9 pixels/mm)
        # 1 inch = 25.4 mm -> 150 DPI = 150/25.4 = 5.905 px/mm -> k = 1 / 5.905 = 0.1693 mm/px
        # We estimate k based on PDP image height relative to typical package height (~150mm)
        estimated_pdp_height_mm = 150.0
        return estimated_pdp_height_mm / float(h)

    def measure_numeral_height(self, crop_image: np.ndarray, scale_ratio_k: float) -> Tuple[float, float]:
        """
        Measures font height of numerals inside the cropped text declaration ROI image.
        Returns (height_in_pixels, height_in_mm).
        """
        if crop_image is None or crop_image.size == 0:
            return 0.0, 0.0

        gray = cv2.cvtColor(crop_image, cv2.COLOR_BGR2GRAY) if len(crop_image.shape) == 3 else crop_image
        
        # Thresholding to isolate glyph contours
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h_crop, w_crop = crop_image.shape[:2]
        glyph_heights = []

        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Filter glyph candidates based on aspect ratio and non-trivial size
            if 0.1 <= float(bw)/bh <= 2.5 and (h_crop * 0.1) <= bh <= (h_crop * 0.95):
                glyph_heights.append(bh)

        if glyph_heights:
            # Use 75th percentile / maximum typical numeral glyph height
            height_px = float(np.percentile(glyph_heights, 75))
        else:
            # Fallback to ~60% of crop height
            height_px = float(h_crop * 0.6)

        height_mm = height_px * scale_ratio_k
        return round(height_px, 2), round(height_mm, 2)

    def verify_rule_7_font_compliance(self, pdp_area_cm2: float, measured_height_mm: float) -> Dict[str, Any]:
        """
        Verifies measured numeral height h_mm against Rule 7 threshold based on PDP Area (cm^2).
        """
        req = self.RULE_7_THRESHOLDS[-1]
        for rule in self.RULE_7_THRESHOLDS:
            if pdp_area_cm2 <= rule["max_area"]:
                req = rule
                break

        min_req_mm = req["min_height_mm"]
        # Standard optical sensor rounding tolerance (2% e.g. 1.99mm vs 2.0mm rounding)
        tolerance_mm = 0.02 * min_req_mm
        is_compliant = (measured_height_mm + tolerance_mm) >= min_req_mm

        return {
            "pdp_area_cm2": pdp_area_cm2,
            "measured_font_height_mm": measured_height_mm,
            "statutory_min_height_mm": min_req_mm,
            "rule_category": req["label"],
            "is_compliant": is_compliant,
            "rule_citation": "Rule 7(2), Legal Metrology (Packaged Commodities) Rules, 2011",
            "violation_details": None if is_compliant else (
                f"Measured font height ({measured_height_mm} mm) is less than the statutory minimum "
                f"({min_req_mm} mm) required for PDP area {pdp_area_cm2} cm^2."
            )
        }
