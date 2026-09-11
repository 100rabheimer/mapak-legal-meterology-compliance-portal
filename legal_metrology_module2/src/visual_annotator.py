import cv2
import numpy as np
import os
from typing import Dict, Any, List, Tuple, Optional

class VisualAnnotator:
    """
    Stage 5: Visual Bounding Box Annotator & Inspector Overlay Renderer.
    Renders:
      - Green Bounding Boxes for compliant declarations.
      - Red Bounding Boxes for non-compliant or missing declarations.
      - Compact text labels, compliance badges, and statutory violation citations.
    """

    COLOR_COMPLIANT = (0, 200, 0)       # Green (BGR)
    COLOR_VIOLATION = (0, 0, 230)       # Red (BGR)
    COLOR_MISSING = (0, 100, 255)       # Orange (BGR) for missing fields
    COLOR_PDP_OUTLINE = (255, 140, 0)   # Deep Cyan / Blue (BGR)
    COLOR_TEXT = (255, 255, 255)        # White
    COLOR_BG_DARK = (20, 20, 20)        # Dark Gray
    COLOR_BG_SEMI = (40, 40, 40)        # Semi-dark Gray

    # Short display labels for each field
    FIELD_LABELS = {
        "manufacturer_details": "Manufacturer",
        "generic_name": "Product Name",
        "net_quantity": "Net Qty",
        "mfg_date": "Mfg Date",
        "mrp": "MRP",
        "usp": "USP",
        "customer_care": "Customer Care",
        "country_of_origin": "Country of Origin",
    }

    def annotate(self, image: np.ndarray, ocr_data: Dict[str, Any], inspection_report: Dict[str, Any],
                 pdp_meta: Optional[Dict[str, Any]] = None, font_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Draws visual annotations, bounding boxes, overlay header, violation badges, and missing field indicators.
        """
        annotated = image.copy()
        h, w = annotated.shape[:2]

        fields = ocr_data.get("fields", {})
        compliant_set = set(inspection_report.get("compliant_fields", []))
        non_compliant_set = set(inspection_report.get("non_compliant_fields", []))
        violations = inspection_report.get("violations", [])

        # Map field to short violation title and ensure non_compliant_set is updated
        field_violations = {}
        for v in violations:
            fk = v.get("field")
            if fk == "font_height":
                fk = "net_quantity"
                non_compliant_set.add("net_quantity")
                compliant_set.discard("net_quantity")
            if fk and fk not in field_violations:
                field_violations[fk] = v.get("title", "Violation")

        # Adaptive font scale based on image resolution
        base_scale = max(0.35, min(0.55, w / 1600.0))
        label_thickness = max(1, int(base_scale * 2.5))
        box_thickness_ok = max(2, int(base_scale * 4))
        box_thickness_bad = max(3, int(base_scale * 6))

        # 1. Draw PDP boundary outline if detected
        if pdp_meta and pdp_meta.get("detected_contour") and pdp_meta.get("corners"):
            corners = np.array(pdp_meta["corners"], dtype=np.int32)
            cv2.polylines(annotated, [corners], isClosed=True, color=self.COLOR_PDP_OUTLINE, thickness=2)

        # 2. Draw Bounding Boxes for detected fields
        drawn_labels = []  # Track label positions to avoid overlaps
        for field_key, fdata in fields.items():
            bbox = fdata.get("bbox_pixel")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox
            # Clamp to image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            if x2 <= x1 or y2 <= y1:
                continue

            # Field is OK only if it has zero violations and is in compliant_set
            is_ok = (field_key in compliant_set) and (field_key not in non_compliant_set) and (field_key not in field_violations)
            color = self.COLOR_COMPLIANT if is_ok else self.COLOR_VIOLATION
            thickness = box_thickness_ok if is_ok else box_thickness_bad

            # Draw bounding box rectangle
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Build compact label
            short_label = self.FIELD_LABELS.get(field_key, field_key.replace('_', ' ').title())
            if is_ok:
                label_text = f"[OK] {short_label}"
            else:
                viol_title = field_violations.get(field_key, "Violation Detected")
                if len(viol_title) > 45:
                    viol_title = viol_title[:42] + "..."
                label_text = f"[VIOLATION] {short_label}: {viol_title}"

            # Compute text size
            (text_w, text_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, base_scale, label_thickness)

            # Smart label placement:
            # In table rows like MRP & USP, rows are packed tightly. Placing badge to the left
            # keeps the text clean and avoids obscuring adjacent declarations.
            if field_key in ["mrp", "usp"] and x1 > text_w + 16:
                banner_x1 = x1 - text_w - 12
                banner_y1 = y1 + max(0, (y2 - y1 - text_h) // 2) - 2
                banner_x2 = x1 - 4
                banner_y2 = banner_y1 + text_h + 6
                text_x = banner_x1 + 4
                text_y = banner_y2 - 3
            else:
                # Position label above the box, shifting down if it would go off-screen
                label_y = y1 - 6
                if label_y - text_h < 80:  # Below the header banner
                    label_y = y2 + text_h + 8  # Put below the box instead

                # Avoid label-label overlaps by shifting down
                for (lx, ly, lw, lh) in drawn_labels:
                    if abs(label_y - ly) < text_h + 4 and abs(x1 - lx) < max(text_w, lw):
                        label_y = ly + lh + 6

                banner_x1 = x1
                banner_y1 = label_y - text_h - 4
                banner_x2 = x1 + text_w + 10
                banner_y2 = label_y + 4
                text_x = x1 + 5
                text_y = label_y

            # Draw label background
            cv2.rectangle(annotated, (banner_x1, banner_y1), (banner_x2, banner_y2), color, -1)
            cv2.putText(annotated, label_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, base_scale, self.COLOR_TEXT, label_thickness, cv2.LINE_AA)

            drawn_labels.append((banner_x1, banner_y1, text_w, text_h))

        # 3. Draw Missing Field Indicators (fields not detected at all)
        all_field_keys = set(self.FIELD_LABELS.keys())
        detected_fields = set(f for f, d in fields.items() if d.get("present"))
        missing_fields = all_field_keys - detected_fields

        if missing_fields:
            panel_y = h - 30 * len(missing_fields) - 20
            overlay = annotated.copy()
            cv2.rectangle(overlay, (5, panel_y - 10), (w // 2, h - 5), self.COLOR_BG_DARK, -1)
            cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

            for idx, fk in enumerate(sorted(missing_fields)):
                label = self.FIELD_LABELS.get(fk, fk)
                text = f"[MISSING] {label} - Not Detected on Package"
                ty = panel_y + idx * 28 + 15
                cv2.putText(annotated, text, (15, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, base_scale * 0.9, self.COLOR_MISSING, label_thickness, cv2.LINE_AA)

        # 4. Draw Header Dashboard Banner
        self._draw_header_banner(annotated, inspection_report, font_info)

        return annotated

    def _draw_header_banner(self, img: np.ndarray, report: Dict[str, Any], font_info: Optional[Dict[str, Any]]):
        h, w = img.shape[:2]
        banner_h = 70
        overlay = img.copy()

        cv2.rectangle(overlay, (0, 0), (w, banner_h), self.COLOR_BG_DARK, -1)
        alpha = 0.88
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

        score = report.get("compliance_score", 0)
        status = report.get("status", "UNKNOWN")
        is_ok = report.get("is_compliant", False)
        status_color = self.COLOR_COMPLIANT if is_ok else self.COLOR_VIOLATION
        n_violations = len(report.get("violations", []))

        # Title
        cv2.putText(img, "DoCA Legal Metrology Packaging Inspector - Module 2", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # Compliance Score + Status
        score_text = f"Score: {score}/100 | {status} | Violations: {n_violations}"
        cv2.putText(img, score_text, (10, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 2, cv2.LINE_AA)

        # Font Calibration metric
        if font_info:
            font_text = f"Font: {font_info.get('measured_font_height_mm')}mm (Min: {font_info.get('statutory_min_height_mm')}mm)"
            (tw, _), _ = cv2.getTextSize(font_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.putText(img, font_text, (w - tw - 15, 62),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (190, 190, 190), 1, cv2.LINE_AA)

    def save_annotated_image(self, image: np.ndarray, output_path: str):
        """Saves annotated image to disk with UTF-8 / Windows path support."""
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            is_success, buffer = cv2.imencode(".png", image)
            if is_success:
                with open(output_path, "wb") as f:
                    f.write(buffer.tobytes())
                print(f"[VisualAnnotator] Saved annotated inspection image to: {output_path}")
                return
        except Exception as e:
            print(f"[VisualAnnotator] Notice on file stream write: {e}. Falling back to OpenCV imwrite.")

        try:
            cv2.imwrite(output_path, image)
            print(f"[VisualAnnotator] Saved annotated inspection image via OpenCV to: {output_path}")
        except Exception as e:
            print(f"[VisualAnnotator] Error saving image: {e}")
