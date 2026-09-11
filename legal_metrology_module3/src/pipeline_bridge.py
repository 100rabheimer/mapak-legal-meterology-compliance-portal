import os
import sys
import json
import re
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

# Load Module 3 environment variables
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(base_dir)
load_dotenv(os.path.join(base_dir, ".env"))

# Resolve Module 2 path dynamically
env_module2_path = os.getenv("MODULE2_PATH")
if env_module2_path and os.path.exists(os.path.join(env_module2_path, "src")):
    module2_path = env_module2_path
else:
    module2_path = os.path.join(workspace_root, "legal_metrology_module2")

module2_src = os.path.join(module2_path, "src")
if os.path.exists(module2_src) and module2_src not in sys.path:
    sys.path.insert(0, module2_src)

from src.utils import sanitize_filename, calculate_statutory_penalty, extract_entity_info, format_timestamp

# Import Module 2 inspection components
try:
    from image_processor import ImageProcessor
    from ocr_extractor import OCRExtractor
    from font_calibrator import FontCalibrator
    from packaging_inspector import PackagingInspector
    from visual_annotator import VisualAnnotator
except ImportError as e:
    raise ImportError(f"Failed to import Module 2 components from {module2_src}: {e}")

class InspectionPipelineBridge:
    """
    Bridge service connecting Module 3 Dashboard to Module 2 AI Inspection Pipeline
    and Module 1 Legal Knowledge Base.
    """

    def __init__(self, rules_kb_path: Optional[str] = None):
        self.base_dir = base_dir
        
        env_rules_path = rules_kb_path or os.getenv("RULES_KB_PATH")
        if env_rules_path and os.path.exists(env_rules_path):
            self.rules_kb_path = env_rules_path
        else:
            self.rules_kb_path = os.path.join(workspace_root, "legal_metrology_compliance", "output", "rules_knowledge_base.json")

        self.img_processor = ImageProcessor()
        self.font_calibrator = FontCalibrator()
        self.ocr_extractor = OCRExtractor()
        self.inspector = PackagingInspector(rules_kb_path=self.rules_kb_path)
        self.annotator = VisualAnnotator()

        self.uploads_dir = os.path.join(self.base_dir, "output", "uploads")
        self.annotated_dir = os.path.join(self.base_dir, "output", "annotated")
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.annotated_dir, exist_ok=True)

    def run_inspection(self, image_path: str, category: str = "UNIVERSAL") -> Dict[str, Any]:
        """
        Runs the complete end-to-end Legal Metrology inspection on a package scan.
        Generates annotated image, violation scorecard, statutory penalties, and full audit payload.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Inspection input image not found: {image_path}")

        clean_name = sanitize_filename(image_path)
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        annotated_filename = f"annotated_{clean_name}_{timestamp_slug}.png"
        annotated_out_path = os.path.join(self.annotated_dir, annotated_filename)

        # Stage 1: Image Processing & PDP Detection
        raw_image = self.img_processor.load_image(image_path)
        pdp_image, pdp_meta = self.img_processor.detect_pdp(raw_image)

        # Scale ratio k (mm / pixel)
        scale_k = self.font_calibrator.compute_scale_ratio(pdp_image)
        pdp_pixel_area = pdp_meta.get("pixel_area", raw_image.shape[0] * raw_image.shape[1])
        pdp_area_cm2 = self.img_processor.calculate_surface_area_cm2(pdp_pixel_area, scale_k)
        pdp_meta["pdp_area_cm2"] = pdp_area_cm2
        pdp_meta["scale_ratio_k"] = round(scale_k, 4)

        # Stage 2: Multilingual OCR & Declaration Extraction
        ocr_data = self.ocr_extractor.extract_declarations(pdp_image)

        # Stage 3: Numeral Font Height Calibration & Rule 7 Verification
        net_qty_crop = None
        net_qty_bbox = ocr_data.get("fields", {}).get("net_quantity", {}).get("bbox_pixel")
        if not net_qty_bbox or len(net_qty_bbox) != 4:
            net_qty_bbox = ocr_data.get("fields", {}).get("mrp", {}).get("bbox_pixel")

        if net_qty_bbox and len(net_qty_bbox) == 4:
            x1, y1, x2, y2 = net_qty_bbox
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            if y_max > y_min and x_max > x_min:
                net_qty_crop = pdp_image[y_min:y_max, x_min:x_max]

        h_px, h_mm = self.font_calibrator.measure_numeral_height(net_qty_crop, scale_k)
        if h_mm <= 0.0 and net_qty_bbox and len(net_qty_bbox) == 4:
            bbox_h = abs(net_qty_bbox[3] - net_qty_bbox[1])
            if bbox_h > 0:
                h_px = round(bbox_h * 0.75, 2)
                h_mm = round(h_px * scale_k, 2)

        font_verification = self.font_calibrator.verify_rule_7_font_compliance(pdp_area_cm2, h_mm)

        # Stage 4: Automated Compliance Verification Engine
        inspection_report = self.inspector.inspect(ocr_data, font_verification, category=category)

        # Stage 5: Visual Bounding Box Annotation
        annotated_image = self.annotator.annotate(
            image=pdp_image,
            ocr_data=ocr_data,
            inspection_report=inspection_report,
            pdp_meta=pdp_meta,
            font_info=font_verification
        )

        # Save annotated image
        self.annotator.save_annotated_image(annotated_image, annotated_out_path)

        # Stage 6: Enrich with Legal Notice & Officer Dashboard Metadata
        entity_info = extract_entity_info(ocr_data)
        penalty_info = calculate_statutory_penalty(inspection_report.get("violations", []))

        result = {
            "status": inspection_report.get("status", "UNKNOWN"),
            "is_compliant": inspection_report.get("is_compliant", False),
            "compliance_score": inspection_report.get("compliance_score", 0),
            "category": category,
            "timestamp": format_timestamp(),
            "summary": inspection_report.get("summary", {}),
            "compliant_fields": inspection_report.get("compliant_fields", []),
            "non_compliant_fields": inspection_report.get("non_compliant_fields", []),
            "violations": inspection_report.get("violations", []),
            "entity_info": entity_info,
            "penalty_info": penalty_info,
            "font_verification": font_verification,
            "pdp_summary": {
                "pdp_area_cm2": pdp_area_cm2,
                "scale_k": round(scale_k, 4),
                "image_dims": [raw_image.shape[1], raw_image.shape[0]]
            },
            "artifacts": {
                "original_image_path": image_path,
                "original_image_filename": os.path.basename(image_path),
                "annotated_image_path": annotated_out_path,
                "annotated_image_filename": annotated_filename,
                "annotated_image_url": f"/api/annotated/{annotated_filename}",
                "original_image_url": f"/api/uploads/{os.path.basename(image_path)}"
            },
            "ocr_raw": {
                "fields": ocr_data.get("fields", {}),
                "raw_text": ocr_data.get("raw_ocr_text", "")
            },
            "rule_engine_metadata": inspection_report.get("rule_engine_metadata", {})
        }

        return result

    def run_multi_inspection(self, image_paths: List[str], category: str = "UNIVERSAL") -> Dict[str, Any]:
        """
        Processes multiple packaging label scans (e.g. 1 to 4 images: Front PDP, Back Panel, Side Label, Price Tag).
        Generates individual annotated images and panel records for EVERY uploaded image.
        """
        if not image_paths:
            raise ValueError("No image paths provided for inspection.")

        panel_results = []
        all_violations = []
        all_compliant = set()
        all_non_compliant = set()
        merged_entity_info = {}

        panel_names = ["Front PDP", "Back Panel", "Side Label", "Outer Carton / Tag"]

        for idx, img_path in enumerate(image_paths):
            p_name = panel_names[idx] if idx < len(panel_names) else f"Packaging Scan #{idx + 1}"
            try:
                single_res = self.run_inspection(img_path, category=category)
                single_res["panel_name"] = p_name
                panel_results.append(single_res)

                # Merge violations
                for v in single_res.get("violations", []):
                    if v not in all_violations:
                        all_violations.append(v)

                all_compliant.update(single_res.get("compliant_fields", []))
                all_non_compliant.update(single_res.get("non_compliant_fields", []))

                # Merge entity info
                for k, val in single_res.get("entity_info", {}).items():
                    if val and val != "N/A" and val != "Undisclosed":
                        merged_entity_info[k] = val
            except Exception as err:
                print(f"[InspectionPipelineBridge] Error processing panel image {img_path}: {err}")

        if not panel_results:
            raise RuntimeError("Failed to process any of the provided packaging scan images.")

        primary = panel_results[0]
        is_compliant = len(all_violations) == 0
        comp_score = max(0, 100 - len(all_violations) * 15)

        # Build panels payload
        panels_payload = []
        for idx, pr in enumerate(panel_results):
            art = pr.get("artifacts", {})
            panels_payload.append({
                "panel_id": f"panel_{idx+1}",
                "panel_name": pr.get("panel_name", f"Scan #{idx+1}"),
                "original_image_url": art.get("original_image_url", ""),
                "annotated_image_url": art.get("annotated_image_url", ""),
                "pdp_area_cm2": pr.get("pdp_summary", {}).get("pdp_area_cm2", 85.5),
                "scale_k": pr.get("pdp_summary", {}).get("scale_k", 0.125),
                "violations": pr.get("violations", []),
                "compliant_fields": pr.get("compliant_fields", [])
            })

        final_result = {
            "status": "COMPLIANT" if is_compliant else "NON_COMPLIANT",
            "is_compliant": is_compliant,
            "compliance_score": comp_score,
            "category": category,
            "timestamp": format_timestamp(),
            "summary": {
                "total_mandatory_fields_checked": 8,
                "compliant_fields_count": len(all_compliant),
                "non_compliant_fields_count": len(all_non_compliant),
                "total_violations_found": len(all_violations),
            },
            "compliant_fields": list(all_compliant),
            "non_compliant_fields": list(all_non_compliant),
            "violations": all_violations,
            "entity_info": merged_entity_info if merged_entity_info else primary.get("entity_info", {}),
            "penalty_info": calculate_statutory_penalty(all_violations),
            "font_verification": primary.get("font_verification"),
            "pdp_summary": primary.get("pdp_summary"),
            "artifacts": primary.get("artifacts", {}),
            "panels": panels_payload
        }

        return final_result

