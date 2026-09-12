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
        panel_names = ["Front PDP", "Back Panel", "Side Label", "Outer Carton / Tag"]

        for idx, img_path in enumerate(image_paths):
            p_name = panel_names[idx] if idx < len(panel_names) else f"Packaging Scan #{idx + 1}"
            try:
                single_res = self.run_inspection(img_path, category=category)
                single_res["panel_name"] = p_name
                panel_results.append(single_res)

                # Collect all raw violations from all panels
                for v in single_res.get("violations", []):
                    all_violations.append(v)
            except Exception as err:
                print(f"[InspectionPipelineBridge] Error processing panel image {img_path}: {err}")

        if not panel_results:
            raise RuntimeError("Failed to process any of the provided packaging scan images.")

        primary = panel_results[0]

        # Merge extracted OCR fields across ALL scanned panels
        merged_fields = {}
        merged_raw_text = []
        merged_entity_info = {}

        for pr in panel_results:
            # Aggregate entity info
            for k, val in pr.get("entity_info", {}).items():
                if val and val not in ["Not Specified", "N/A", "Undisclosed", "Pre-Packaged Commodity (Unidentified Generic Name)"]:
                    merged_entity_info[k] = val
                elif k not in merged_entity_info:
                    merged_entity_info[k] = val

            # Aggregate OCR fields and bounding boxes
            ocr_f = pr.get("ocr_raw", {}).get("fields", {})
            for fk, fdata in ocr_f.items():
                if fdata.get("present") and fdata.get("text"):
                    if fk not in merged_fields or not merged_fields[fk].get("present"):
                        merged_fields[fk] = fdata
                    elif not merged_fields[fk].get("bbox_pixel") and fdata.get("bbox_pixel"):
                        merged_fields[fk]["bbox_pixel"] = fdata.get("bbox_pixel")
                elif fk not in merged_fields:
                    merged_fields[fk] = fdata

            raw_t = pr.get("ocr_raw", {}).get("raw_text")
            if raw_t:
                merged_raw_text.append(raw_t)

        # Fallback missing entity info from merged_fields text
        if "generic_name" in merged_fields and merged_fields["generic_name"].get("text"):
            merged_entity_info["commodity_name"] = merged_fields["generic_name"]["text"]
        if "manufacturer_details" in merged_fields and merged_fields["manufacturer_details"].get("text"):
            merged_entity_info["manufacturer_name_address"] = merged_fields["manufacturer_details"]["text"]
        if "net_quantity" in merged_fields and merged_fields["net_quantity"].get("text"):
            merged_entity_info["net_quantity"] = merged_fields["net_quantity"]["text"]
        if "mrp" in merged_fields and merged_fields["mrp"].get("text"):
            merged_entity_info["mrp"] = merged_fields["mrp"]["text"]
        if "mfg_date" in merged_fields and merged_fields["mfg_date"].get("text"):
            merged_entity_info["mfg_date"] = merged_fields["mfg_date"]["text"]

        # Cross-panel Violation Reconciliation:
        # A mandatory field is NOT missing if it was detected on ANY panel!
        reconciled_violations = []
        for v in all_violations:
            fk = v.get("field")
            # If it was flagged as missing mandatory declaration, check if present on another panel
            if v.get("rule_id") == "RULE_6_MANDATORY":
                if fk in merged_fields and merged_fields[fk].get("present") and merged_fields[fk].get("text"):
                    continue  # Found on another packaging panel!

            # Avoid duplicate violation entries in report
            if not any(rv.get("rule_id") == v.get("rule_id") and rv.get("field") == v.get("field") and rv.get("title") == v.get("title") for rv in reconciled_violations):
                reconciled_violations.append(v)

        MANDATORY_KEYS = [
            "manufacturer_details", "generic_name", "net_quantity", "mfg_date",
            "mrp", "usp", "customer_care", "country_of_origin"
        ]

        all_compliant_fields = []
        all_non_compliant_fields = []

        for mk in MANDATORY_KEYS:
            has_viol = any(rv.get("field") == mk for rv in reconciled_violations)
            is_present = merged_fields.get(mk, {}).get("present", False) and bool(merged_fields.get(mk, {}).get("text"))
            if is_present and not has_viol:
                all_compliant_fields.append(mk)
            else:
                all_non_compliant_fields.append(mk)

        # Accurate Dynamic Compliance Score based on verified declarations
        total_mandatory = len(MANDATORY_KEYS)
        compliant_count = len(all_compliant_fields)
        statutory_defects = [v for v in reconciled_violations if v.get("rule_id") in ["RULE_11_UNITS", "RULE_7_FONT", "RULE_6_1_E_TAXES", "RULE_6_1_E_CURRENCY"]]
        defect_penalty = len(statutory_defects) * 5.0

        base_score = (compliant_count / float(total_mandatory)) * 100.0
        comp_score = max(0, min(100, int(round(base_score - defect_penalty))))
        if len(reconciled_violations) == 0:
            comp_score = 100
        elif comp_score >= 100:
            comp_score = 95
        is_compliant = len(reconciled_violations) == 0

        # Build panels payload with fields and bounding boxes
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
                "compliant_fields": pr.get("compliant_fields", []),
                "fields": pr.get("ocr_raw", {}).get("fields", {})
            })

        final_result = {
            "status": "PASS" if is_compliant else "NON-COMPLIANT / VIOLATION DETECTED",
            "is_compliant": is_compliant,
            "compliance_score": comp_score,
            "category": category,
            "timestamp": format_timestamp(),
            "summary": {
                "total_mandatory_fields_checked": total_mandatory,
                "compliant_fields_count": len(all_compliant_fields),
                "non_compliant_fields_count": len(all_non_compliant_fields),
                "total_violations_found": len(reconciled_violations),
            },
            "compliant_fields": all_compliant_fields,
            "non_compliant_fields": all_non_compliant_fields,
            "violations": reconciled_violations,
            "entity_info": merged_entity_info if merged_entity_info else primary.get("entity_info", {}),
            "penalty_info": calculate_statutory_penalty(reconciled_violations),
            "font_verification": primary.get("font_verification"),
            "pdp_summary": primary.get("pdp_summary"),
            "artifacts": primary.get("artifacts", {}),
            "panels": panels_payload,
            "ocr_raw": {
                "fields": merged_fields,
                "raw_text": "\n".join(merged_raw_text)
            }
        }

        return final_result

