import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class PackagingInspector:
    """
    Stage 4: Automated Compliance Verification Engine.
    Cross-checks extracted declarations against Legal Metrology Rules Knowledge Base (rules_knowledge_base.json).
    """

    ALLOWED_UNITS = {
        "mass": ["g", "kg", "mg"],
        "volume": ["ml", "l", "L"],
        "length": ["m", "cm", "mm"],
        "number": ["N", "n", "u", "pc", "pcs", "units"]
    }

    ILLEGAL_UNIT_MAP = {
        "gms": "g", "gm": "g", "gms.": "g", "gm.": "g", "gram": "g", "grams": "g",
        "kilo": "kg", "kg.": "kg", "kgs": "kg", "kgs.": "kg",
        "ML": "ml", "mls": "ml", "ml.": "ml", "ltr": "l", "ltrs": "l", "lts": "l", "lit": "l", "liter": "l", "liters": "l",
        "nos": "N", "nos.": "N", "number": "N"
    }

    MANDATORY_FIELDS = [
        ("manufacturer_details", "Rule 6(1)(a)", "Name & Address of Manufacturer / Packer / Importer"),
        ("generic_name", "Rule 6(1)(b)", "Generic / Common Name of Commodity"),
        ("net_quantity", "Rule 6(1)(c) & Rule 11", "Net Quantity & Standard Unit Symbol"),
        ("mfg_date", "Rule 6(1)(d)", "Month & Year of Manufacture / Packing"),
        ("mrp", "Rule 6(1)(e)", "Maximum Retail Price (MRP ₹ XX.XX incl. of all taxes)"),
        ("usp", "Rule 6(1)(ea)", "Unit Sale Price (USP)"),
        ("customer_care", "Rule 6(1)(f)", "Consumer Care Details (Phone / Email / Address)"),
        ("country_of_origin", "Rule 6(1)(g)", "Country of Origin (for imported goods)")
    ]

    def __init__(self, rules_kb_path: Optional[str] = None):
        env_rules_path = rules_kb_path or os.getenv("RULES_KB_PATH")
        if env_rules_path and os.path.exists(env_rules_path):
            self.rules_kb_path = env_rules_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace_root = os.path.dirname(base_dir)
            self.rules_kb_path = os.path.join(workspace_root, "legal_metrology_compliance", "output", "rules_knowledge_base.json")
        self.rules_kb = self._load_rules_kb()

    def _load_rules_kb(self) -> Dict[str, Any]:
        if os.path.exists(self.rules_kb_path):
            try:
                with open(self.rules_kb_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[PackagingInspector] Warning loading rules KB: {e}")
        return {"rules": {}}

    def inspect(self, ocr_data: Dict[str, Any], font_verification: Optional[Dict[str, Any]] = None, category: str = "UNIVERSAL") -> Dict[str, Any]:
        """
        Runs comprehensive rule verification pipeline over extracted OCR data.
        Returns complete audit report with compliance score, violation breakdown, and legal citations.
        """
        fields = ocr_data.get("fields", {})
        violations = []
        compliant_fields = []
        non_compliant_fields = []

        # 1. Mandatory Field Presence Checks
        for field_key, rule_clause, description in self.MANDATORY_FIELDS:
            fdata = fields.get(field_key, {})
            text = fdata.get("text")
            is_present = fdata.get("present", False) and text is not None and len(str(text).strip()) > 0

            # Special case for Country of Origin: required if imported or ecommerce / universal rule 6(1)(g)
            if field_key == "country_of_origin" and not is_present:
                # Check if raw text hints at imported commodity or generic rule
                text_lower = ocr_data.get("raw_ocr_text", "").lower()
                if "import" in text_lower or "made in" in text_lower or "origin" in text_lower:
                    is_present = False
                else:
                    # Minor warning if omitted on domestic package
                    pass

            if not is_present and field_key != "country_of_origin":
                violations.append({
                    "rule_id": "RULE_6_MANDATORY",
                    "clause": rule_clause,
                    "field": field_key,
                    "severity": "CRITICAL",
                    "title": f"Missing Mandatory Declaration: {description}",
                    "description": f"The required declaration '{description}' under {rule_clause} was not found on the packaging PDP.",
                    "legal_citation": f"Legal Metrology (Packaged Commodities) Rules, 2011 - {rule_clause}",
                    "remedy": f"Print explicit '{description}' declaration on the Principal Display Panel."
                })
                non_compliant_fields.append(field_key)
            elif is_present:
                compliant_fields.append(field_key)

        # 2. Net Quantity & Legal Unit Symbol Verification (Rule 6(1)(c) & Rule 11)
        net_qty_data = fields.get("net_quantity", {})
        if net_qty_data.get("present") and net_qty_data.get("text"):
            net_qty_text = net_qty_data["text"]
            # Skip deep content checks if OCR couldn't actually read the text (MSER fallback)
            if "[MSER Region Detected" not in net_qty_text:
                unit_violations = self._verify_unit_symbol(net_qty_text)
                for v in unit_violations:
                    violations.append(v)
                    if "net_quantity" not in non_compliant_fields:
                        non_compliant_fields.append("net_quantity")
                    if "net_quantity" in compliant_fields:
                        compliant_fields.remove("net_quantity")

        # 3. MRP Declaration Clause Verification (Rule 6(1)(e))
        mrp_data = fields.get("mrp", {})
        if mrp_data.get("present") and mrp_data.get("text"):
            mrp_text = mrp_data["text"]
            # Skip deep content checks if OCR couldn't actually read the text (MSER fallback)
            if "[MSER Region Detected" not in mrp_text:
                mrp_violations = self._verify_mrp_format(mrp_text, ocr_data.get("raw_ocr_text", ""))
                for v in mrp_violations:
                    violations.append(v)
                    if "mrp" not in non_compliant_fields:
                        non_compliant_fields.append("mrp")
                    if "mrp" in compliant_fields:
                        compliant_fields.remove("mrp")

        # 4. Unit Sale Price (USP) Verification (Rule 6(1)(ea))
        usp_data = fields.get("usp", {})
        if not usp_data.get("present"):
            # Check if net quantity indicates > 10g or > 10ml, triggering USP requirement
            net_qty_text = net_qty_data.get("text", "")
            # Only verify USP requirement if we actually read the net quantity text
            if net_qty_text and "[MSER Region Detected" not in net_qty_text and self._requires_usp(net_qty_text):
                violations.append({
                    "rule_id": "RULE_6_1_EA_USP",
                    "clause": "Rule 6(1)(ea)",
                    "field": "usp",
                    "severity": "MAJOR",
                    "title": "Missing Unit Sale Price (USP) Declaration",
                    "description": "Unit Sale Price (USP) is mandatory for pre-packaged commodities containing > 10g or > 10ml.",
                    "legal_citation": "Rule 6(1)(ea), Legal Metrology (Packaged Commodities) Rules, 2011 (Amended 2021)",
                    "remedy": "Include USP format e.g., '₹ 0.50 / g' or '₹ 1.20 / ml' alongside MRP."
                })
                if "usp" not in non_compliant_fields:
                    non_compliant_fields.append("usp")
                if "usp" in compliant_fields:
                    compliant_fields.remove("usp")

        # 5. Rule 7 Numeral Font Size Verification
        if font_verification:
            if not font_verification.get("is_compliant"):
                violations.append({
                    "rule_id": "RULE_7_FONT",
                    "clause": "Rule 7(2)",
                    "field": "net_quantity",
                    "severity": "CRITICAL",
                    "title": f"Non-Compliant Numeral Font Height ({font_verification.get('measured_font_height_mm')}mm < {font_verification.get('statutory_min_height_mm')}mm)",
                    "description": font_verification.get("violation_details"),
                    "legal_citation": "Rule 7(2), Legal Metrology (Packaged Commodities) Rules, 2011",
                    "remedy": f"Increase numeral font height to at least {font_verification.get('statutory_min_height_mm')} mm."
                })
                if "net_quantity" not in non_compliant_fields:
                    non_compliant_fields.append("net_quantity")
                if "net_quantity" in compliant_fields:
                    compliant_fields.remove("net_quantity")

        # Calculate Compliance Score (0 - 100%)
        total_checks = len(self.MANDATORY_FIELDS) + 2  # Mandatory + Unit Symbol + Font Size
        critical_violations = [v for v in violations if v["severity"] == "CRITICAL"]
        major_violations = [v for v in violations if v["severity"] == "MAJOR"]
        
        penalty_score = (len(critical_violations) * 20) + (len(major_violations) * 10)
        compliance_score = max(0, 100 - penalty_score)
        is_fully_compliant = len(violations) == 0

        # Extract linked rule metadata from rules_knowledge_base.json if available
        rule_6_meta = self.rules_kb.get("rules", {}).get("RULE_6", {})

        return {
            "is_compliant": is_fully_compliant,
            "compliance_score": compliance_score,
            "status": "PASS" if is_fully_compliant else "NON-COMPLIANT / VIOLATION DETECTED",
            "summary": {
                "total_mandatory_fields_checked": len(self.MANDATORY_FIELDS),
                "compliant_fields_count": len(compliant_fields),
                "non_compliant_fields_count": len(non_compliant_fields),
                "total_violations_found": len(violations)
            },
            "compliant_fields": compliant_fields,
            "non_compliant_fields": non_compliant_fields,
            "violations": violations,
            "rule_engine_metadata": {
                "rules_baseline": "Legal Metrology (Packaged Commodities) Rules, 2011 + Gazette Amendments",
                "master_kb_loaded": len(self.rules_kb.get("rules", {})) > 0,
                "rule_6_source_pdf": rule_6_meta.get("source_pdf"),
                "rule_6_source_url": rule_6_meta.get("source_url")
            }
        }

    def _verify_unit_symbol(self, net_qty_text: str) -> List[Dict[str, Any]]:
        violations = []
        # Look for illegal unit strings in net_qty_text
        for illegal, legal in self.ILLEGAL_UNIT_MAP.items():
            pattern = r'\b' + re.escape(illegal) + r'\b'
            if re.search(pattern, net_qty_text, re.IGNORECASE):
                violations.append({
                    "rule_id": "RULE_11_UNITS",
                    "clause": "Rule 11 & Schedule II",
                    "field": "net_quantity",
                    "severity": "CRITICAL",
                    "title": f"Illegal Unit Symbol '{illegal}' Used",
                    "description": f"The declaration '{net_qty_text}' contains non-compliant unit symbol '{illegal}'. Mandatory legal symbol is '{legal}'.",
                    "legal_citation": "Rule 11 & Schedule II, Legal Metrology (Packaged Commodities) Rules, 2011",
                    "remedy": f"Replace non-standard unit symbol '{illegal}' with standard SI symbol '{legal}'."
                })
        return violations

    def _verify_mrp_format(self, mrp_text: str, raw_ocr_text: str = "") -> List[Dict[str, Any]]:
        violations = []
        text_lower = mrp_text.lower()
        context_lower = (mrp_text + " " + raw_ocr_text).lower()
        
        # Check for inclusive of taxes clause in MRP text or nearby packaging context
        has_tax_clause = ("incl" in context_lower or "inclusive" in context_lower) and ("tax" in context_lower)
        if not has_tax_clause:
            violations.append({
                "rule_id": "RULE_6_1_E_TAXES",
                "clause": "Rule 6(1)(e)",
                "field": "mrp",
                "severity": "MAJOR",
                "title": "Missing Mandatory 'Inclusive of all taxes' Clause in MRP",
                "description": f"The MRP declaration '{mrp_text}' omits the statutory mandatory phrase 'inclusive of all taxes'.",
                "legal_citation": "Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
                "remedy": "Format MRP declaration as: 'MRP ₹ XX.XX (inclusive of all taxes)'."
            })

        # Check currency symbol / prefix
        if not (re.search(r'(₹|rs\.?|inr)', text_lower)):
            violations.append({
                "rule_id": "RULE_6_1_E_CURRENCY",
                "clause": "Rule 6(1)(e)",
                "field": "mrp",
                "severity": "CRITICAL",
                "title": "Missing Indian Rupee Currency Symbol (₹ / Rs.) in MRP",
                "description": f"The MRP declaration '{mrp_text}' is missing currency symbol ₹ or Rs.",
                "legal_citation": "Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
                "remedy": "Prefix price with Indian Rupee symbol '₹' or 'Rs.'."
            })

        return violations

    def _requires_usp(self, net_qty_text: str) -> bool:
        """Determines if net quantity is > 10g or > 10ml requiring USP."""
        if not net_qty_text:
            return True
        match = re.search(r'([0-9.]+)\s*(g|kg|ml|l|lts|gms)', net_qty_text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            unit = match.group(2).lower()
            if unit in ["kg", "l", "lts"]:
                return True
            if unit in ["g", "gms", "ml"] and val > 10.0:
                return True
            return False
        return True
