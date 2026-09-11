import os
import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.image_processor import PDPImageProcessor
from src.ocr_extractor import MultilingualOCRExtractor
from src.font_calibrator import FontHeightCalibrator
from src.packaging_inspector import PackagingComplianceInspector
from src.visual_annotator import VisualBoundingBoxAnnotator

def inspect_packaging_image(image_path, output_dir="output"):
    """
    Full Module 2 Multimodal Vision AI Packaging Inspection Pipeline.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    print("\n" + "=" * 80)
    print("   MODULE 2: MULTIMODAL VISION AI & PACKAGING COMPLIANCE INSPECTOR")
    print("=" * 80)
    print(f"Target Packaging Image: {image_path}\n")

    # -------------------------------------------------------------------------
    # STEP 1: Preprocessing & PDP Boundary Detection
    # -------------------------------------------------------------------------
    print("[STEP 1/5] Preprocessing & PDP Boundary Detection...")
    img_processor = PDPImageProcessor()
    pdp_info = img_processor.process_pipeline(image_path)
    print(f"  -> Skew Correction Angle: {pdp_info.get('skew_angle', 0.0):.2f}°")
    print(f"  -> Surface PDP Area:       {pdp_info['pdp_area_cm2']} cm²")
    print(f"  -> Estimated Dimensions:   {pdp_info['pdp_size_cm'][0]} cm x {pdp_info['pdp_size_cm'][1]} cm")

    # -------------------------------------------------------------------------
    # STEP 2: Multilingual Packaging OCR & Field Extraction
    # -------------------------------------------------------------------------
    print("\n[STEP 2/5] Multilingual OCR & Vision Field Extraction...")
    ocr_extractor = MultilingualOCRExtractor()
    extracted_fields = ocr_extractor.extract(image_path)
    
    print(f"  -> Extracted Commodity: {extracted_fields.get('commodity_name')}")
    print(f"  -> Extracted Net Qty:  {extracted_fields.get('net_quantity', {}).get('raw_text') if isinstance(extracted_fields.get('net_quantity'), dict) else extracted_fields.get('net_quantity')}")
    print(f"  -> Extracted MRP:      {extracted_fields.get('mrp', {}).get('raw_text') if isinstance(extracted_fields.get('mrp'), dict) else extracted_fields.get('mrp')}")

    # -------------------------------------------------------------------------
    # STEP 3: Numeral Font Height Calibration (Rule 7)
    # -------------------------------------------------------------------------
    print("\n[STEP 3/5] Physical Numeral Font Height Calibration...")
    calibrator = FontHeightCalibrator()
    net_qty_bbox = [500, 100, 560, 900]
    if isinstance(extracted_fields.get("net_quantity"), dict):
        net_qty_bbox = extracted_fields["net_quantity"].get("bbox", net_qty_bbox)

    font_audit = calibrator.audit_font_height(
        image_np=pdp_info["processed_image"],
        field_bbox=net_qty_bbox,
        pdp_area_cm2=pdp_info["pdp_area_cm2"],
        field_name="Net Quantity Numeral",
        pdp_info=pdp_info
    )
    print(f"  -> Measured Numeral Height: {font_audit['measured_height_mm']} mm")
    print(f"  -> Required Rule 7 Height:  {font_audit['required_min_height_mm']} mm")
    print(f"  -> Rule 7 Font Status:      {'PASS' if font_audit['is_compliant'] else 'FAIL'}")

    # -------------------------------------------------------------------------
    # STEP 4: Legal Metrology Compliance Verification Audit Engine
    # -------------------------------------------------------------------------
    print("\n[STEP 4/5] Legal Compliance Verification Audit against Rules Knowledge Base...")
    inspector = PackagingComplianceInspector(rules_kb_path=os.path.join(os.path.dirname(__file__), "output", "rules_knowledge_base.json"))
    audit_report = inspector.audit_packaging(extracted_fields, pdp_info, font_audit_result=font_audit)

    print("\n" + "-" * 70)
    print(f"   INSPECTION AUDIT SUMMARY: [{audit_report['status']}]")
    print(f"   Overall Compliance Score: {audit_report['compliance_score']}%")
    print(f"   Passed Checks: {audit_report['passed_count']} | Rule Violations: {audit_report['violations_count']}")
    print("-" * 70)

    if audit_report["violations"]:
        print("\n[!] DETECTED RULE VIOLATIONS:")
        for idx, v in enumerate(audit_report["violations"], 1):
            print(f"  {idx}. [{v['rule_id']}] {v['field']}: {v['issue']}")
            print(f"     Statutory Ref: {v['statutory_ref']}")
            if v.get('source_url'):
                print(f"     Gazette Link:  {v['source_url']}")
            print()

    # Save structured audit JSON
    json_report_path = os.path.join(output_dir, f"inspection_report_{base_name}.json")
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)
    print(f"[REPORT] Saved JSON Audit Report: {json_report_path}")

    # -------------------------------------------------------------------------
    # STEP 5: Visual Bounding Box Annotation (Green/Red Bboxes)
    # -------------------------------------------------------------------------
    print("\n[STEP 5/5] Rendering Visual Bounding Box Overlay...")
    annotator = VisualBoundingBoxAnnotator()
    annotated_img_path = os.path.join(output_dir, f"annotated_{base_name}.jpg")
    annotator.annotate(pdp_info["processed_image"], audit_report, annotated_img_path)

    print("\n" + "=" * 80)
    print("                 MODULE 2 INSPECTION COMPLETED!")
    print("=" * 80)
    print(f" 1. Annotated Visual Image:  {annotated_img_path}")
    print(f" 2. Inspection Report JSON:  {json_report_path}")
    print("=" * 80 + "\n")
    
    return audit_report, annotated_img_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Legal Metrology Packaging Inspection CLI")
    parser.add_argument("--image", default="output/test_packages/sample_non_compliant_package.jpg", help="Path to input package label image")
    parser.add_argument("--output_dir", default="output", help="Directory for output files")
    args = parser.parse_args()

    inspect_packaging_image(args.image, args.output_dir)
