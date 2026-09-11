import cv2
import numpy as np

class FontHeightCalibrator:
    """
    Numeral Font Height Calibrator under Legal Metrology Rule 7.
    Measures physical height (mm) of numerals in Net Quantity and MRP declarations
    using reference geometry (barcode/scale marker or DPI) and audits against Rule 7 area brackets.
    """
    
    # Rule 7 Statutory Minimum Numeral Height Table (Rule 7(1) & Rule 7(2))
    # Area (cm²) -> (Min Height Regular mm, Min Height Moulded/Blown/Perforated mm)
    RULE_7_THRESHOLDS = [
        (50, 1.0, 1.5),       # <= 50 cm²
        (100, 1.5, 2.0),      # 50 < Area <= 100 cm²
        (500, 2.5, 4.0),      # 100 < Area <= 500 cm²
        (2500, 4.0, 6.0),     # 500 < Area <= 2500 cm²
        (float('inf'), 6.0, 6.0) # > 2500 cm²
    ]

    def __init__(self, default_dpi=150):
        self.default_dpi = default_dpi

    def get_required_min_height(self, pdp_area_cm2, is_moulded_or_perforated=False):
        """Returns statutory minimum height (mm) for a given PDP area under Rule 7."""
        for limit_area, min_regular, min_moulded in self.RULE_7_THRESHOLDS:
            if pdp_area_cm2 <= limit_area:
                return min_moulded if is_moulded_or_perforated else min_regular
        return 6.0

    def calculate_scale_ratio(self, image_np, pdp_info=None):
        """
        Calculates pixel-to-mm ratio k = mm / pixels.
        Attempts to detect reference scale line (e.g. 50mm scale) or barcode height,
        or uses DPI resolution math.
        """
        h, w = image_np.shape[:2]
        
        # 1. Search for red reference scale marker (255, 0, 0 in RGB)
        hsv = cv2.cvtColor(image_np, cv2.COLOR_BGR2HSV)
        # Red color range
        mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
        red_mask = mask1 | mask2

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            # If horizontal scale line found (width > 80px, height < 20px)
            if cw > 80 and ch < 30:
                # Standard scale marker is 50 mm
                k = 50.0 / float(cw)
                print(f"[CALIBRATOR] Detected 50mm reference scale marker. k = {k:.4f} mm/px")
                return k

        # 2. Fallback using PDP physical dimension estimate
        if pdp_info and "pdp_size_cm" in pdp_info:
            pdp_h_cm = pdp_info["pdp_size_cm"][1]
            pdp_h_mm = pdp_h_cm * 10.0
            pdp_h_px = pdp_info["pdp_bbox"][3]
            if pdp_h_px > 0:
                k = pdp_h_mm / float(pdp_h_px)
                print(f"[CALIBRATOR] Calculated scale from PDP height ({pdp_h_cm} cm). k = {k:.4f} mm/px")
                return k

        # 3. Default DPI resolution scaling: 1 inch = 25.4 mm
        k = 25.4 / float(self.default_dpi)
        print(f"[CALIBRATOR] Using DPI scale factor ({self.default_dpi} DPI). k = {k:.4f} mm/px")
        return k

    def measure_numeral_height(self, image_np, bbox_normalized, scale_k):
        """
        Measures physical height (mm) of numerals inside normalized bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
        """
        h, w = image_np.shape[:2]
        ymin, xmin, ymax, xmax = bbox_normalized
        
        y1, y2 = int((ymin / 1000.0) * h), int((ymax / 1000.0) * h)
        x1, x2 = int((xmin / 1000.0) * w), int((xmax / 1000.0) * w)

        box_h_px = max(1, y2 - y1)
        
        # Numeral line height inside box (typically ~60-80% of box height)
        numeral_h_px = box_h_px * 0.70
        height_mm = numeral_h_px * scale_k

        return round(height_mm, 2), box_h_px

    def audit_font_height(self, image_np, field_bbox, pdp_area_cm2, field_name="Net Quantity", pdp_info=None):
        """
        Audits field numeral font height against Rule 7 requirements.
        """
        scale_k = self.calculate_scale_ratio(image_np, pdp_info)
        measured_mm, height_px = self.measure_numeral_height(image_np, field_bbox, scale_k)
        required_mm = self.get_required_min_height(pdp_area_cm2)

        is_compliant = measured_mm >= required_mm
        
        return {
            "field_name": field_name,
            "pdp_area_cm2": pdp_area_cm2,
            "measured_height_mm": measured_mm,
            "required_min_height_mm": required_mm,
            "pixel_to_mm_ratio": round(scale_k, 5),
            "is_compliant": is_compliant,
            "rule_id": "RULE_7_FONT",
            "statutory_ref": f"Rule 7 of Legal Metrology (Packaged Commodities) Rules, 2011 (Min {required_mm} mm for PDP {pdp_area_cm2} cm²)"
        }
