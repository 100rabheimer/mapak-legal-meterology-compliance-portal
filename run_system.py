import os
import sys
import subprocess
import time
import urllib.request
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
module1_dir = os.path.join(base_dir, "legal_metrology_compliance")
module2_dir = os.path.join(base_dir, "legal_metrology_module2")
module3_dir = os.path.join(base_dir, "legal_metrology_module3")
ui_dir = os.path.join(base_dir, "legal-metrology-compliance-ui")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def print_banner():
    print("=" * 80)
    print("      DEPARTMENT OF CONSUMER AFFAIRS • GOVERNMENT OF INDIA")
    print("      LEGAL METROLOGY AI COMPLIANCE CHECKING SYSTEM (SIH 26034)")
    print("=" * 80)

def check_rules_kb():
    rules_kb = os.path.join(module1_dir, "output", "rules_knowledge_base.json")
    if not os.path.exists(rules_kb):
        print("\n[*] Initializing Module 1 Legal Knowledge Base (rules_knowledge_base.json)...")
        res = subprocess.run([sys.executable, "main.py"], cwd=module1_dir)
        if res.returncode != 0:
            print("[!] Warning: Module 1 KB initialization returned non-zero code. Proceeding with pre-seeded fallback rules.")
    else:
        print("[✓] Module 1 Rules Knowledge Base Verified:", rules_kb)

def run_tests():
    print("\n[*] Running Module 3 End-to-End Verification Test Suite...")
    res = subprocess.run([sys.executable, "main.py", "--test"], cwd=module3_dir)
    if res.returncode == 0:
        print("[✓] All 3-Module Integration Tests Passed 100%!")
    else:
        print("[!] Warning: Module 3 test suite reported issues. Check logs.")

def start_backend_server():
    print("\n[*] Starting FastAPI Enforcement Officer Server (Module 3)...")
    print("    URL: http://127.0.0.1:8000")
    print("    API Docs: http://127.0.0.1:8000/docs")
    print("    Press Ctrl+C to terminate.")
    print("=" * 80 + "\n")
    
    subprocess.run([sys.executable, "main.py", "--serve"], cwd=module3_dir)

def main():
    print_banner()
    check_rules_kb()
    run_tests()
    start_backend_server()

if __name__ == "__main__":
    main()
