import os
import re
import random
from datetime import datetime
from typing import Dict, Any, List

def get_base_dir() -> str:
    """Returns root directory of Module 3."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_notice_number() -> str:
    """Generates formal Government of India Notice Reference Number."""
    now = datetime.now()
    rand_seq = f"{random.randint(1001, 9999)}"
    return f"DOCA/LM/ENF/{now.year}/{now.strftime('%m')}-{rand_seq}"

def format_timestamp() -> str:
    """Returns formatted inspection timestamp."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S IST")

def sanitize_filename(name: str) -> str:
    """Sanitizes filename for safe storage."""
    base = os.path.splitext(os.path.basename(name))[0]
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', base)
    return cleaned or "package"

def calculate_statutory_penalty(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates statutory penalty guidelines under Section 36(1) of Legal Metrology Act, 2009.
    """
    critical_count = sum(1 for v in violations if v.get("severity") == "CRITICAL")
    major_count = sum(1 for v in violations if v.get("severity") == "MAJOR")
    total_violations = len(violations)

    if total_violations == 0:
        return {
            "applicable": False,
            "statutory_section": "N/A (Fully Compliant)",
            "first_offence_max": 0,
            "second_offence_max": 0,
            "recommended_action": "No adverse action. Issue Compliance Acknowledgment.",
            "seizure_advised": False
        }

    # If critical violations exist (e.g. missing mandatory declaration, illegal units, font size)
    seizure_advised = critical_count > 0 or total_violations >= 3

    return {
        "applicable": True,
        "statutory_section": "Section 36(1) read with Section 15, Legal Metrology Act, 2009",
        "first_offence_max": 25000,
        "first_offence_str": "Up to ₹ 25,000",
        "second_offence_max": 50000,
        "second_offence_str": "Up to ₹ 50,000",
        "subsequent_offence_str": "₹ 50,000 to ₹ 1,00,000 or Imprisonment up to 1 Year, or both",
        "seizure_advised": seizure_advised,
        "recommended_action": (
            "Immediate Seizure & 7-Day Statutory Show-Cause Directive under Section 15 & Section 36(1)"
            if seizure_advised else
            "Statutory Show-Cause Directive & Mandatory Rectification within 7 Days under Section 36(1)"
        )
    }

def extract_entity_info(ocr_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts offending company/manufacturer details and commodity info from OCR data.
    """
    fields = ocr_data.get("fields", {}) if isinstance(ocr_data, dict) else {}
    
    # Extract Manufacturer
    mfg_entry = fields.get("manufacturer_details", {})
    mfg_text = mfg_entry.get("text") if isinstance(mfg_entry, dict) else None
    if not mfg_text or mfg_text.strip() == "":
        mfg_text = "M/s. Offending Manufacturer / Packer / Importer (Name unstated on package PDP)"
    
    # Extract Commodity Name
    generic_entry = fields.get("generic_name", {})
    generic_text = generic_entry.get("text") if isinstance(generic_entry, dict) else None
    if not generic_text or generic_text.strip() == "":
        generic_text = "Pre-Packaged Commodity (Unidentified Generic Name)"

    # Extract MRP & Date
    mrp_entry = fields.get("mrp", {})
    mrp_text = mrp_entry.get("text", "Not Specified") if isinstance(mrp_entry, dict) else "Not Specified"

    mfg_date_entry = fields.get("mfg_date", {})
    mfg_date_text = mfg_date_entry.get("text", "Not Specified") if isinstance(mfg_date_entry, dict) else "Not Specified"

    net_qty_entry = fields.get("net_quantity", {})
    net_qty_text = net_qty_entry.get("text", "Not Specified") if isinstance(net_qty_entry, dict) else "Not Specified"

    return {
        "manufacturer_name_address": mfg_text,
        "commodity_name": generic_text,
        "mrp": mrp_text,
        "mfg_date": mfg_date_text,
        "net_quantity": net_qty_text
    }
