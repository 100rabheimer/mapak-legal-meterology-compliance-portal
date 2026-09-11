import os
import sys
import argparse
import json
import uvicorn
from dotenv import load_dotenv

# Ensure local directories and UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

sys.path.insert(0, base_dir)

from src.pipeline_bridge import InspectionPipelineBridge
from src.notice_generator import LegalNoticeGenerator
from src.utils import generate_notice_number

def run_test_suite():
    """
    Executes automated end-to-end test of the inspection pipeline and legal notice generation.
    """
    print("\n==========================================================================")
    print("   DoCA LEGAL METROLOGY MODULE 3: AUTOMATED TEST & VERIFICATION SUITE")
    print("==========================================================================")

    bridge = InspectionPipelineBridge()
    notice_gen = LegalNoticeGenerator()

    # Test Case 1: Non-Compliant Package Sample
    non_comp_sample = os.path.join(base_dir, "test_samples", "sample_non_compliant_package.jpg")
    print(f"\n[*] [TEST 1/2] Evaluating Non-Compliant Package: {non_comp_sample}")
    report_non_comp = bridge.run_inspection(non_comp_sample, category="FOOD_SNACKS")

    print(f"    - Status:           {report_non_comp['status']}")
    print(f"    - Compliance Score: {report_non_comp['compliance_score']} / 100")
    print(f"    - Violations Found: {len(report_non_comp['violations'])}")
    for idx, v in enumerate(report_non_comp['violations'], 1):
        print(f"      {idx}. [{v.get('severity')}] {v.get('clause')}: {v.get('title')}")

    # Generate Legal Notice PDF for Non-Compliant Package
    print(f"[*] Generating Court-Ready Legal Notice PDF under Sections 15, 36 & 51...")
    notice_pdf_path = notice_gen.generate_notice(report_non_comp)
    print(f"    [✓] Notice Generated Successfully: {notice_pdf_path}")
    assert os.path.exists(notice_pdf_path), "Generated notice PDF does not exist!"
    assert os.path.getsize(notice_pdf_path) > 1000, "Notice PDF file size is unexpectedly small!"

    # Test Case 2: Compliant Package Sample
    comp_sample = os.path.join(base_dir, "test_samples", "sample_compliant_package.jpg")
    print(f"\n[*] [TEST 2/2] Evaluating Compliant Package: {comp_sample}")
    report_comp = bridge.run_inspection(comp_sample, category="FOOD_SNACKS")

    print(f"    - Status:           {report_comp['status']}")
    print(f"    - Compliance Score: {report_comp['compliance_score']} / 100")
    print(f"    - Violations Found: {len(report_comp['violations'])}")

    print(f"[*] Generating Compliance Certificate PDF for Compliant Package...")
    cert_pdf_path = notice_gen.generate_notice(report_comp)
    print(f"    [✓] Certificate Generated Successfully: {cert_pdf_path}")
    assert os.path.exists(cert_pdf_path), "Generated certificate PDF does not exist!"

    print("\n==========================================================================")
    print("   [SUCCESS] ALL MODULE 3 INTEGRATION AND GENERATION TESTS PASSED 100%!")
    print("==========================================================================\n")

def run_cli_inspection(image_path: str, category: str = "UNIVERSAL", generate_notice: bool = True):
    """
    Runs direct command-line inspection on a user-provided image.
    """
    bridge = InspectionPipelineBridge()
    notice_gen = LegalNoticeGenerator()

    print(f"[*] Inspecting packaging image: {image_path} (Category: {category})")
    report = bridge.run_inspection(image_path, category=category)

    print(f"\n=== INSPECTION REPORT ===")
    print(f"Status:           {report['status']}")
    print(f"Compliance Score: {report['compliance_score']} / 100")
    print(f"Violations:       {len(report['violations'])}")
    print(f"Annotated Image:  {report['artifacts']['annotated_image_path']}")

    if generate_notice:
        pdf_path = notice_gen.generate_notice(report)
        print(f"Notice PDF:       {pdf_path}")

    return report

def main():
    parser = argparse.ArgumentParser(description="DoCA Legal Metrology Officer Dashboard & Notice Generator (Module 3)")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI Officer Dashboard Server")
    parser.add_argument("--test", action="store_true", help="Run automated test suite on sample packages")
    parser.add_argument("--image", type=str, help="Path to packaging image for direct CLI inspection")
    parser.add_argument("--category", type=str, default="UNIVERSAL", help="Commodity category")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "127.0.0.1"), help="Server host")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8000)), help="Server port")

    args = parser.parse_args()

    if args.test:
        run_test_suite()
    elif args.image:
        run_cli_inspection(args.image, category=args.category)
    else:
        # Default action: start dashboard server
        print("\n" + "="*70)
        print("  DEPARTMENT OF CONSUMER AFFAIRS • LEGAL METROLOGY DIVISION")
        print("  ENFORCEMENT OFFICER DASHBOARD & NOTICE GENERATION SERVER")
        print("="*70)
        print(f"  [+] Server running at: http://{args.host}:{args.port}")
        print(f"  [+] API Documentation: http://{args.host}:{args.port}/docs")
        print("="*70 + "\n")
        uvicorn.run("app.api:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
