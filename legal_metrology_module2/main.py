import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Reconfigure stdout to UTF-8 for Windows console Unicode compatibility (e.g. ₹ symbol)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure local src package imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.image_processor import ImageProcessor
from src.ocr_extractor import OCRExtractor
from src.font_calibrator import FontCalibrator
from src.packaging_inspector import PackagingInspector
from src.visual_annotator import VisualAnnotator
from src.sample_generator import SamplePackageGenerator

load_dotenv()

def run_pipeline(image_path: str, category: str = "UNIVERSAL", rules_kb_path: str = None) -> dict:
    """
    Executes complete Module 2 Legal Metrology Packaging Inspection Pipeline.
    """
    print(f"\n==========================================================================")
    print(f"   DoCA LEGAL METROLOGY PACKAGING COMPLIANCE INSPECTOR (MODULE 2)")
    print(f"==========================================================================")
    print(f"[*] Input Packaging Image: {image_path}")

    # Stage 1: Image Processing & PDP Detection
    img_processor = ImageProcessor()
    raw_image = img_processor.load_image(image_path)
    pdp_image, pdp_meta = img_processor.detect_pdp(raw_image)

    # Calculate scale ratio k (mm / pixel)
    font_calibrator = FontCalibrator()
    scale_k = font_calibrator.compute_scale_ratio(pdp_image)
    
    # Calculate PDP Surface Area in cm^2
    pdp_pixel_area = pdp_meta["pixel_area"]
    pdp_area_cm2 = img_processor.calculate_surface_area_cm2(pdp_pixel_area, scale_k)
    pdp_meta["pdp_area_cm2"] = pdp_area_cm2

    print(f"[+] PDP Panel Detected | Area: {pdp_area_cm2} cm^2 | Scale Ratio k: {scale_k:.4f} mm/px")

    # Stage 2: Multilingual OCR & Field Extraction
    ocr_extractor = OCRExtractor()
    ocr_data = ocr_extractor.extract_declarations(pdp_image)

    print(f"[+] Multilingual OCR Extraction Completed ({len(ocr_data.get('fields', {}))} declaration fields evaluated)")

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

    h_px, h_mm = font_calibrator.measure_numeral_height(net_qty_crop, scale_k)
    # If glyph contour thresholding yielded 0, derive from detected bounding box height
    if h_mm <= 0.0 and net_qty_bbox and len(net_qty_bbox) == 4:
        bbox_h = abs(net_qty_bbox[3] - net_qty_bbox[1])
        if bbox_h > 0:
            h_px = round(bbox_h * 0.75, 2)
            h_mm = round(h_px * scale_k, 2)

    font_verification = font_calibrator.verify_rule_7_font_compliance(pdp_area_cm2, h_mm)

    print(f"[+] Numeral Font Height Measured: {h_mm} mm (Statutory Rule 7 Minimum Required: {font_verification['statutory_min_height_mm']} mm)")

    # Stage 4: Automated Compliance Verification Engine
    inspector = PackagingInspector(rules_kb_path=rules_kb_path)
    inspection_report = inspector.inspect(ocr_data, font_verification, category=category)

    # Stage 5: Visual Bounding Box Annotation
    annotator = VisualAnnotator()
    annotated_image = annotator.annotate(
        image=pdp_image,
        ocr_data=ocr_data,
        inspection_report=inspection_report,
        pdp_meta=pdp_meta,
        font_info=font_verification
    )

    # Save output artifacts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    clean_path = image_path.strip().strip('"').strip("'")
    raw_name = os.path.splitext(os.path.basename(clean_path))[0] or "package"
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_name)
    
    annotated_out_path = os.path.join(output_dir, f"annotated_{safe_name}.png")
    report_out_path = os.path.join(output_dir, f"report_{safe_name}.json")

    annotator.save_annotated_image(annotated_image, annotated_out_path)

    with open(report_out_path, "w", encoding="utf-8") as f:
        json.dump(inspection_report, f, indent=2)

    print(f"[+] Audit Inspection Report Saved: {report_out_path}")
    print(f"[+] Visual Bounding Box Image Saved: {annotated_out_path}")

    # Print Summary to Console
    print(f"\n--------------------------------------------------------------------------")
    print(f"                       INSPECTION SUMMARY RESULT                          ")
    print(f"--------------------------------------------------------------------------")
    print(f" Status:             {inspection_report['status']}")
    print(f" Compliance Score:   {inspection_report['compliance_score']} / 100")
    print(f" Violations Found:   {len(inspection_report['violations'])}")
    print(f"--------------------------------------------------------------------------")

    if inspection_report['violations']:
        print("\n[!] STATUTORY LEGAL VIOLATIONS DETECTED:")
        for idx, v in enumerate(inspection_report['violations'], 1):
            print(f"  {idx}. [{v['severity']}] {v['title']}")
            print(f"     Clause:  {v['clause']}")
            print(f"     Details: {v['description']}")
            print(f"     Remedy:  {v['remedy']}\n")
    else:
        print("\n[✓] 100% COMPLIANT PACKAGE. All mandatory declarations verified.")

    print(f"==========================================================================\n")
    return inspection_report

def main():
    parser = argparse.ArgumentParser(description="DoCA Legal Metrology Packaging Inspector - Module 2")
    parser.add_argument("--image", type=str, help="Path to packaging panel image")
    parser.add_argument("--category", type=str, default="UNIVERSAL", help="Commodity category tag")
    parser.add_argument("--rules-kb", type=str, help="Path to rules_knowledge_base.json")
    parser.add_argument("--generate-samples", action="store_true", help="Generate synthetic test packaging images and run test suite")

    args = parser.parse_args()

    if args.generate_samples or not args.image:
        print("[*] Generating synthetic packaging panel test images (Non-Compliant & Compliant samples)...")
        gen = SamplePackageGenerator()
        non_comp_path, comp_path = gen.generate_all()
        
        print("\n---> RUNNING TEST CASE 1: NON-COMPLIANT PACKAGE")
        run_pipeline(non_comp_path, category=args.category, rules_kb_path=args.rules_kb)

        print("\n---> RUNNING TEST CASE 2: COMPLIANT PACKAGE")
        run_pipeline(comp_path, category=args.category, rules_kb_path=args.rules_kb)
    else:
        run_pipeline(args.image, category=args.category, rules_kb_path=args.rules_kb)

if __name__ == "__main__":
    main()
