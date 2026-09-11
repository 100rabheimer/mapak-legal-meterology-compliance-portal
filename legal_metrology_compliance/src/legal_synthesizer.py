import re
from src.llm_synthesizer import LLMLegalSynthesizer

def classify_rule_category(rule_key, title, text, filename):
    title_text = (title + " " + text + " " + filename).lower()
    
    if any(w in title_text for w in ["garment", "readymade", "clothing", "textile"]):
        return "GARMENTS & TEXTILES", False
    elif any(w in title_text for w in ["edible oil", "fats", "oil"]):
        return "EDIBLE OILS & FATS", False
    elif any(w in title_text for w in ["medical device", "sphygmomanometer", "thermometer"]):
        return "MEDICAL DEVICES", False
    elif any(w in title_text for w in ["pan masala", "tobacco", "gutkha"]):
        return "PAN MASALA & TOBACCO", False
    elif any(w in title_text for w in ["e-commerce", "online", "coo filter", "import"]):
        return "E-COMMERCE & IMPORTS", False
    elif any(w in title_text for w in ["gas meter", "moisture meter", "breath analyser", "nawi", "radar", "meter"]):
        return "MEASURING INSTRUMENTS & METERS", False
    elif any(w in title_text for w in ["qr code", "digital"]):
        return "DIGITAL & QR CODE DECLARATIONS", False
    elif any(w in title_text for w in ["jan vishwas", "penalty", "compounding", "offence", "fine"]):
        return "LEGAL ENFORCEMENT & PENALTIES", False
    
    universal_keys = ["RULE_1", "RULE_2", "RULE_3", "RULE_4", "RULE_5", "RULE_6_1_A", "RULE_6_1_B", 
                      "RULE_6_1_C", "RULE_6_1_D", "RULE_6_1_E", "RULE_6_1_EA", "RULE_6_1_F", 
                      "RULE_6_1_G", "RULE_7_FONT", "RULE_8", "RULE_9", "RULE_10", "RULE_11_UNITS"]
    
    if rule_key in universal_keys or any(w in title_text for w in ["declaration", "principal display panel", "mrp", "net quantity", "unit symbol"]):
        return "UNIVERSAL (ALL PACKAGED COMMODITIES)", True

    return "GENERAL LEGAL METROLOGY PROVISION", True

class LegalSynthesizer:
    def __init__(self, api_key=None):
        self.llm = LLMLegalSynthesizer(api_key=api_key)
        
        base_pdf_url = "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/input_pdfs/9%20The%20Legal%20Metrology%20(Package%20Commodities)%20Rules%2C%202011.pdf"
        base_pdf_name = "9 The Legal Metrology (Package Commodities) Rules, 2011.pdf"

        # Initialize pre-seeded master rules with detailed origin history
        self.rules_state = {
            "RULE_1": {
                "rule_id": "RULE_1",
                "clause": "Rule 1",
                "title": "Short Title and Commencement",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": False,
                "text": "Legal Metrology (Packaged Commodities) Rules, 2011. Came into force on 1st April 2011.",
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_2": {
                "rule_id": "RULE_2",
                "clause": "Rule 2",
                "title": "Definitions (PDP, Net Qty, Pre-packed Commodity)",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": False,
                "text": "Definitions of Principal Display Panel (PDP), Net Quantity, Pre-packed Commodity, Wholesale Package, and Multi-piece Package.",
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_4": {
                "rule_id": "RULE_4",
                "clause": "Rule 4",
                "title": "Regulation of Packaging for Retail Sale",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "No person shall pre-pack or cause to be pre-packed any commodity for sale unless it bears mandatory declarations.",
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_A": {
                "rule_id": "RULE_6_1_A",
                "clause": "Rule 6(1)(a)",
                "title": "Manufacturer / Packer / Importer Details",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Name and address of the manufacturer, packer, or importer must be clearly declared on package.",
                "regex_patterns": [
                    r"(?i)(Mfd\.?\s*by|Manufactured\s*by|Packed\s*by|Imported\s*by|Marketed\s*by)\s*:?\s*([A-Za-z0-9\s\,\.\-]+)"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_B": {
                "rule_id": "RULE_6_1_B",
                "clause": "Rule 6(1)(b)",
                "title": "Generic or Common Name of Commodity",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Common or generic names of the commodity contained in the package.",
                "regex_patterns": [
                    r"(?i)(Commodity|Product|Name)\s*:?\s*([A-Za-z\s]+)"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_C": {
                "rule_id": "RULE_6_1_C",
                "clause": "Rule 6(1)(c)",
                "title": "Net Quantity Declaration",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Net quantity, in terms of standard unit of weight or measure or number.",
                "regex_patterns": [
                    r"(?i)(Net\s*(Qty|Quantity|Weight|Wt|Vol|Volume))\s*:?\s*(\d+(\.\d+)?)\s*(g|kg|ml|l|L|N|m)"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_D": {
                "rule_id": "RULE_6_1_D",
                "clause": "Rule 6(1)(d)",
                "title": "Month and Year of Manufacture / Packing",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Month and year in which the commodity is manufactured or packed.",
                "regex_patterns": [
                    r"(?i)(Mfd|Packed|Mfg|Pkd)\s*(Date|Month|&|\/)?\s*:?\s*(\d{2}[\/\-]\d{2,4}|[A-Za-z]{3}\s*\d{4})"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_E": {
                "rule_id": "RULE_6_1_E",
                "clause": "Rule 6(1)(e)",
                "title": "Maximum Retail Price (MRP)",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Maximum Retail Price (MRP) inclusive of all taxes in Indian Rupees (₹ or Rs.).",
                "regex_patterns": [
                    r"(?i)(MRP|Max\.?\s*Retail\.?\s*Price)\s*:?\s*(Rs\.?|₹)\s*(\d+(\.\d{2})?)\s*\(?\s*inclusive of all taxes\s*\)?"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_EA": {
                "rule_id": "RULE_6_1_EA",
                "clause": "Rule 6(1)(ea)",
                "title": "Unit Sale Price (USP) Declaration",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE (INSERTED 2021)",
                "effective_date": "2022-04-01",
                "mandatory": True,
                "text": "Unit Sale Price declared as ₹ per g/kg/ml/l based on package net quantity size.",
                "regex_patterns": [
                    r"(?i)(Unit\s*Sale\s*Price|USP)\s*:?\s*(Rs\.?|₹)\s*(\d+(\.\d+)?)\s*per\s*(g|kg|ml|l|L|N)"
                ],
                "source_pdf": "LM_General_Amendment_Rules2021_1732709906.pdf",
                "source_url": "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/input_pdfs/LM_General_Amendment_Rules2021_1732709906.pdf",
                "amendment_history": [
                    {"event": "INSERTED (AMENDMENT 2021)", "pdf_name": "LM_General_Amendment_Rules2021_1732709906.pdf", "pdf_url": "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/input_pdfs/LM_General_Amendment_Rules2021_1732709906.pdf", "notification_no": "G.S.R. 779(E)", "date": "02-Nov-2021"}
                ]
            },
            "RULE_6_1_F": {
                "rule_id": "RULE_6_1_F",
                "clause": "Rule 6(1)(f)",
                "title": "Consumer Care Contact Details",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Name, address, telephone number, and e-mail address for consumer complaints.",
                "regex_patterns": [
                    r"(?i)(Customer|Consumer)\s*(Care|Cell|Helpline)\s*:?\s*([A-Za-z0-9\s\,\.\@\-\+]+)"
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_6_1_G": {
                "rule_id": "RULE_6_1_G",
                "clause": "Rule 6(1)(g)",
                "title": "Country of Origin Declaration",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE (INSERTED 2021)",
                "effective_date": "2022-04-01",
                "mandatory": True,
                "text": "Country of Origin of commodity explicitly declared for all imported packages.",
                "regex_patterns": [
                    r"(?i)(Country\s*of\s*Origin|Made\s*in|Imported\s*from)\s*:?\s*([A-Za-z\s]+)"
                ],
                "source_pdf": "2026.02.13 PCR 1st COO Filter on e-commerce websites_1771231030.pdf",
                "source_url": "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/input_pdfs/2026.02.13%20PCR%201st%20COO%20Filter%20on%20e-commerce%20websites_1771231030.pdf",
                "amendment_history": [
                    {"event": "INSERTED (AMENDMENT 2021)", "pdf_name": "2026.02.13 PCR 1st COO Filter on e-commerce websites_1771231030.pdf", "pdf_url": "file:///C:/Users/Taranjeet%20Singh/Desktop/legal_metrology_compliance/input_pdfs/2026.02.13%20PCR%201st%20COO%20Filter%20on%20e-commerce%20websites_1771231030.pdf", "notification_no": "G.S.R. 779(E)", "date": "02-Nov-2021"}
                ]
            },
            "RULE_7_FONT": {
                "rule_id": "RULE_7_FONT",
                "clause": "Rule 7",
                "title": "Minimum Font Height Requirements",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Minimum height of numerals and letters based on Principal Display Panel area.",
                "thresholds": [
                    {"pdp_area_sq_cm": "<= 50", "min_normal_mm": 1.0, "min_net_qty_mrp_mm": 1.5},
                    {"pdp_area_sq_cm": "50 < area <= 100", "min_normal_mm": 1.5, "min_net_qty_mrp_mm": 2.0},
                    {"pdp_area_sq_cm": "100 < area <= 500", "min_normal_mm": 2.5, "min_net_qty_mrp_mm": 4.0},
                    {"pdp_area_sq_cm": "> 500", "min_normal_mm": 4.0, "min_net_qty_mrp_mm": 6.0}
                ],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            },
            "RULE_11_UNITS": {
                "rule_id": "RULE_11_UNITS",
                "clause": "Rule 11",
                "title": "Standard Units & Prohibited Symbols",
                "category": "UNIVERSAL (ALL PACKAGED COMMODITIES)",
                "is_universal": True,
                "status": "ACTIVE",
                "effective_date": "2011-04-01",
                "mandatory": True,
                "text": "Units of weight, measure or number shall be expressed in standard symbols: 'g', 'kg', 'ml', 'l', 'm', 'N'. Non-standard symbols such as 'gms', 'gm', 'ML', 'KG.' are prohibited.",
                "allowed_symbols": ["g", "kg", "ml", "l", "L", "m", "N"],
                "prohibited_symbols": ["gms", "gm", "ML", "KG.", "grms", "Ltr", "Ltrs"],
                "source_pdf": base_pdf_name,
                "source_url": base_pdf_url,
                "amendment_history": [
                    {"event": "ORIGIN (BASELINE 2011)", "pdf_name": base_pdf_name, "pdf_url": base_pdf_url, "notification_no": "G.S.R. 202(E)", "date": "07-Mar-2011"}
                ]
            }
        }

    def process_document(self, doc_info):
        filename = doc_info["filename"]
        file_url = doc_info["file_url"]
        notif_no = doc_info.get("notification_no", "N/A")
        doc_date = doc_info.get("date", "N/A")

        # 1. LLM Synthesis
        llm_result = self.llm.synthesize_with_llm(doc_info)
        if llm_result:
            doc_info["notification_no"] = llm_result.get("notification_no", notif_no)
            doc_info["date"] = llm_result.get("date", doc_date)
            doc_info["is_amendment"] = llm_result.get("is_amendment", doc_info["is_amendment"])
            
            for item in llm_result.get("amended_clauses", []):
                clause_key = item.get("clause", "").replace(" ", "_").upper()
                if clause_key:
                    action = item.get("action", "SUBSTITUTE")
                    cat_name, is_univ = classify_rule_category(clause_key, item.get("title", ""), item.get("summary", ""), filename)
                    
                    history_item = {
                        "event": f"AMEND ({action})",
                        "pdf_name": filename,
                        "pdf_url": file_url,
                        "notification_no": doc_info["notification_no"],
                        "date": doc_info["date"]
                    }
                    
                    if clause_key not in self.rules_state:
                        self.rules_state[clause_key] = {
                            "rule_id": clause_key,
                            "clause": item.get("clause", clause_key),
                            "title": item.get("title", "Legal Regulation"),
                            "category": cat_name,
                            "is_universal": is_univ,
                            "status": f"AMENDED ({action})",
                            "effective_date": llm_result.get("effective_date", doc_date),
                            "mandatory": True,
                            "text": item.get("summary", ""),
                            "regex_patterns": [item.get("regex_pattern")] if item.get("regex_pattern") else [],
                            "source_pdf": filename,
                            "source_url": file_url,
                            "amendment_history": [history_item]
                        }
                    else:
                        existing_pdfs = [h["pdf_name"] for h in self.rules_state[clause_key]["amendment_history"] if isinstance(h, dict)]
                        if filename not in existing_pdfs:
                            self.rules_state[clause_key]["amendment_history"].append(history_item)

        # 2. Dynamic Rule Extractor: Ingest all Rule X blocks parsed from PDF with full hyperlinked history
        for rule in doc_info.get("rules_extracted", []):
            rule_key = rule["rule_num"]
            cat_name, is_univ = classify_rule_category(rule_key, rule["title"], rule["text"], filename)
            
            history_item = {
                "event": "AMENDMENT / GAZETTE UPDATE" if doc_info["is_amendment"] else "BASELINE RULE",
                "pdf_name": filename,
                "pdf_url": file_url,
                "notification_no": notif_no,
                "date": doc_date
            }
            
            if rule_key not in self.rules_state:
                self.rules_state[rule_key] = {
                    "rule_id": rule_key,
                    "clause": rule["clause"],
                    "title": rule["title"],
                    "category": cat_name,
                    "is_universal": is_univ,
                    "status": "AMENDED" if doc_info["is_amendment"] else "ACTIVE",
                    "effective_date": doc_date,
                    "mandatory": True,
                    "text": rule["text"][:350] + "...",
                    "source_pdf": filename,
                    "source_url": file_url,
                    "amendment_history": [history_item]
                }
            else:
                if doc_info["is_amendment"]:
                    self.rules_state[rule_key]["status"] = "AMENDED / UPDATED"
                    self.rules_state[rule_key]["category"] = cat_name
                    self.rules_state[rule_key]["is_universal"] = is_univ
                    self.rules_state[rule_key]["source_pdf"] = filename
                    self.rules_state[rule_key]["source_url"] = file_url
                    
                    existing_pdfs = [h["pdf_name"] for h in self.rules_state[rule_key]["amendment_history"] if isinstance(h, dict)]
                    if filename not in existing_pdfs:
                        self.rules_state[rule_key]["amendment_history"].append(history_item)

    def get_consolidated_state(self):
        return self.rules_state
