import os
import json
import re

class PackagingComplianceInspector:
    """
    Multimodal Vision AI Packaging Compliance Inspector Engine.
    Audits extracted packaging metadata against Master Rules Knowledge Base (rules_knowledge_base.json)
    and enforces Legal Metrology (Packaged Commodities) Rules, 2011 + Gazette Amendments up to 2026.
    """

    PROHIBITED_UNIT_SYMBOLS = {
        "GMS": "g",
        "GM": "g",
        "GMS.": "g",
        "ML": "ml",
        "M.L.": "ml",
        "K.G.": "kg",
        "KG": "kg",
        "LTR": "L",
        "LTRS": "L",
        "LIT": "L",
        "LITRE": "L",
        "LITRES": "L"
    }

    def __init__(self, rules_kb_path="output/rules_knowledge_base.json"):
        self.rules_kb_path = rules_kb_path
        self.rules_kb = self._load_rules_kb()

    def _load_rules_kb(self):
        """Loads synthesized master rule base JSON."""
        if os.path.exists(self.rules_kb_path):
            try:
                with open(self.rules_kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
                    print(f"[INSPECTOR ENGINE] Loaded {len(kb.get('rules', {}))} rules from knowledge base.")
                    return kb
            except Exception as e:
                print(f"[INSPECTOR ENGINE WARNING] Error loading rules KB: {e}")
        return {"rules": {}}

    def get_rule_details(self, rule_id):
        """Retrieves rule metadata, clause, text, and PDF URL for statutory lineage linking."""
        rules = self.rules_kb.get("rules", {})
        return rules.get(rule_id, {
            "rule_id": rule_id,
            "clause": f"Rule ({rule_id})",
            "source_url": "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/output/Consolidated_Legal_Metrology_Rulebook_Human.pdf"
        })

    def audit_packaging(self, extracted_fields, pdp_info, font_audit_result=None):
        """
        Runs comprehensive 5-stage legal compliance audit on extracted packaging label data.
        """
        violations = []
        warnings = []
        passed_checks = []

        # -------------------------------------------------------------------------
        # STAGE 1: Mandatory Field Presence Audit (Rule 6(1))
        # -------------------------------------------------------------------------
        mandatory_checklist = [
            ("mfg_name_address", "Manufacturer / Packer / Importer Name & Address", "RULE_6_MFG_DETAILS", "Rule 6(1)(a)"),
            ("net_quantity", "Net Quantity Declaration", "RULE_6_NET_QTY", "Rule 6(1)(b)"),
            ("mrp", "Maximum Retail Price (MRP)", "RULE_6_MRP", "Rule 6(1)(e)"),
            ("mfg_date", "Date of Manufacture / Packaging", "RULE_6_MFG_DATE", "Rule 6(1)(d)"),
            ("country_of_origin", "Country of Origin", "RULE_6_COO", "Rule 6(1)(aa)"),
            ("consumer_care", "Consumer Care / Grievance Details", "RULE_6_CONSUMER_CARE", "Rule 6(1)(h)")
        ]

        for field_key, field_name, rule_id, clause in mandatory_checklist:
            val = extracted_fields.get(field_key)
            # Check if field is present
            is_present = False
            raw_text = ""
            bbox = [0, 0, 0, 0]

            if isinstance(val, dict):
                raw_text = val.get("raw_text") or ""
                is_present = bool(raw_text.strip())
                bbox = val.get("bbox", [0, 0, 0, 0])
            elif isinstance(val, str):
                raw_text = val
                is_present = bool(val.strip())

            rule_meta = self.get_rule_details(rule_id)

            if not is_present:
                violations.append({
                    "field": field_name,
                    "field_key": field_key,
                    "severity": "HIGH",
                    "rule_id": rule_id,
                    "clause": clause,
                    "issue": f"Missing mandatory declaration: {field_name}",
                    "statutory_ref": f"Mandatory under {clause} of Legal Metrology (Packaged Commodities) Rules, 2011",
                    "source_url": rule_meta.get("source_url"),
                    "bbox": bbox
                })
            else:
                passed_checks.append({
                    "field": field_name,
                    "field_key": field_key,
                    "rule_id": rule_id,
                    "raw_text": raw_text,
                    "bbox": bbox
                })

        # -------------------------------------------------------------------------
        # STAGE 2: Prohibited Unit Symbol Audit (Rule 13)
        # -------------------------------------------------------------------------
        net_qty_info = extracted_fields.get("net_quantity", {})
        if isinstance(net_qty_info, dict):
            net_qty_text = str(net_qty_info.get("raw_text") or "")
            net_qty_bbox = net_qty_info.get("bbox", [0, 0, 0, 0])
        else:
            net_qty_text = str(net_qty_info or "")
            net_qty_bbox = [0, 0, 0, 0]

        rule_13_meta = self.get_rule_details("RULE_13")

        for prohibited, correct in self.PROHIBITED_UNIT_SYMBOLS.items():
            pattern = rf'\b{re.escape(prohibited)}\b'
            if net_qty_text and re.search(pattern, net_qty_text, re.IGNORECASE):
                violations.append({
                    "field": "Net Quantity Unit Symbol",
                    "field_key": "net_quantity",
                    "severity": "HIGH",
                    "rule_id": "RULE_13",
                    "clause": "Rule 13",
                    "issue": f"Prohibited unit symbol '{prohibited}' used in Net Qty declaration '{net_qty_text}'. Mandatory standard symbol is '{correct}'.",
                    "statutory_ref": f"Rule 13: Standard units of weight & measure (Use '{correct}' instead of '{prohibited}')",
                    "source_url": rule_13_meta.get("source_url"),
                    "bbox": net_qty_bbox
                })
                break

        # -------------------------------------------------------------------------
        # STAGE 3: MRP Formatting & Unit Sale Price (USP) Audit (Rule 6(1)(e) & Rule 6(1)(ea))
        # -------------------------------------------------------------------------
        mrp_info = extracted_fields.get("mrp", {})
        mrp_text = mrp_info.get("raw_text", "") if isinstance(mrp_info, dict) else str(mrp_info or "")
        mrp_bbox = mrp_info.get("bbox", [0, 0, 0, 0]) if isinstance(mrp_info, dict) else [0, 0, 0, 0]

        if mrp_text:
            if not ("incl" in mrp_text.lower() and "tax" in mrp_text.lower()):
                violations.append({
                    "field": "MRP Tax Inclusion Declaration",
                    "field_key": "mrp",
                    "severity": "MEDIUM",
                    "rule_id": "RULE_6_MRP",
                    "clause": "Rule 6(1)(e)",
                    "issue": f"MRP declaration '{mrp_text}' missing mandatory phrase '(Inclusive of all taxes)'.",
                    "statutory_ref": "Rule 6(1)(e): Price declaration must explicitly state 'Inclusive of all taxes'",
                    "source_url": self.get_rule_details("RULE_6_MRP").get("source_url"),
                    "bbox": mrp_bbox
                })

        # Unit Sale Price (USP) audit (Rule 6(1)(ea))
        usp_info = extracted_fields.get("unit_sale_price", {})
        usp_present = False
        usp_bbox = [0, 0, 0, 0]
        if isinstance(usp_info, dict):
            usp_present = usp_info.get("present") or bool(usp_info.get("raw_text"))
            usp_bbox = usp_info.get("bbox", [0, 0, 0, 0])

        if not usp_present:
            violations.append({
                "field": "Unit Sale Price (USP)",
                "field_key": "unit_sale_price",
                "severity": "HIGH",
                "rule_id": "RULE_6_USP",
                "clause": "Rule 6(1)(ea)",
                "issue": "Missing mandatory Unit Sale Price (USP) declaration (e.g. ₹/g, ₹/ml, ₹/N). Mandatory for all pre-packaged commodities.",
                "statutory_ref": "Rule 6(1)(ea) (Amended via G.S.R. 779(E)): Unit Sale Price mandatory on all packages",
                "source_url": self.get_rule_details("RULE_6_USP").get("source_url"),
                "bbox": usp_bbox
            })

        # -------------------------------------------------------------------------
        # STAGE 4: Rule 7 Numeral Font Height Audit
        # -------------------------------------------------------------------------
        if font_audit_result:
            if not font_audit_result.get("is_compliant"):
                violations.append({
                    "field": "Numeral Font Height (Rule 7)",
                    "field_key": "font_height",
                    "severity": "HIGH",
                    "rule_id": "RULE_7_FONT",
                    "clause": "Rule 7",
                    "issue": f"Numeral height ({font_audit_result['measured_height_mm']} mm) is below statutory minimum ({font_audit_result['required_min_height_mm']} mm) for PDP area {pdp_info['pdp_area_cm2']} cm².",
                    "statutory_ref": font_audit_result["statutory_ref"],
                    "source_url": self.get_rule_details("RULE_7_FONT").get("source_url"),
                    "bbox": net_qty_bbox
                })

        # -------------------------------------------------------------------------
        # STAGE 5: Category Specific Rule Audit
        # -------------------------------------------------------------------------
        cat_info = extracted_fields.get("category_specific", {})
        category = cat_info.get("category", "GENERAL").upper()
        cat_declarations = cat_info.get("declarations", {})

        if category == "GARMENTS":
            # Garments Rule: Size in cm + Fiber composition
            if not any("size" in str(k).lower() or "chest" in str(v).lower() for k, v in cat_declarations.items()):
                warnings.append({
                    "field": "Garment Size Declaration",
                    "category": "GARMENTS",
                    "issue": "Garment packaging should specify size code and physical dimensions in cm (chest/waist) under Garment Amendment Rules."
                })
        elif category == "EDIBLE OILS":
            # Edible Oils Rule: Blend ratio
            if not any("blend" in str(k).lower() or "ratio" in str(v).lower() for k, v in cat_declarations.items()):
                warnings.append({
                    "field": "Edible Oil Multi-Source Declaration",
                    "category": "EDIBLE OILS",
                    "issue": "Blended edible vegetable oils must declare percentage by weight of each edible oil used."
                })

        # -------------------------------------------------------------------------
        # COMPLIANCE SCORE & SUMMARY
        # -------------------------------------------------------------------------
        total_checks = len(mandatory_checklist) + 3
        failed_count = len(violations)
        passed_count = len(passed_checks)
        
        compliance_score = max(0.0, round(((total_checks - failed_count) / total_checks) * 100.0, 1))
        
        status = "COMPLIANT" if failed_count == 0 else "NON_COMPLIANT"

        return {
            "status": status,
            "compliance_score": compliance_score,
            "total_checks": total_checks,
            "passed_count": passed_count,
            "violations_count": failed_count,
            "warnings_count": len(warnings),
            "violations": violations,
            "warnings": warnings,
            "passed_checks": passed_checks,
            "pdp_summary": {
                "pdp_area_cm2": pdp_info.get("pdp_area_cm2"),
                "canvas_size_px": pdp_info.get("canvas_size_px")
            }
        }
