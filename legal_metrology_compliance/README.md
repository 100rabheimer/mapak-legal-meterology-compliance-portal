# Legal Metrology Compliance Checking System (Module 1)
**SIH Problem Statement ID: 26034**  
*Department of Consumer Affairs (DoCA) — Ministry of Consumer Affairs, Food & Public Distribution*

---

##  Overview

This is **Module 1** of the Legal Metrology Compliance Checking System. It ingests the baseline *Legal Metrology (Packaged Commodities) Rules, 2011* PDF along with subsequent Gazette Amendment PDFs, parses legal clause directives (*substituted*, *inserted*, *omitted*), and automatically synthesizes two outputs:

1. **Human-Readable Master Rulebook PDF (`Consolidated_Legal_Metrology_Rulebook_Human.pdf`):**  
   Designed for inspection officials. Displays legal clause history, active status badges (`[ACTIVE]`, `[AMENDED]`, `[INSERTED]`), and font size tables.

2. **Machine-Readable Rules Engine Database (`rules_knowledge_base.json` & `Machine_Rules_Specification.pdf`):**  
   Structured rules schema containing field keys, extraction regex patterns, unit symbol constraints, and font height thresholds to be consumed directly by **Module 2 (Vision AI Engine)**.

---

## 📁 Project Structure

```
legal_metrology_compliance/
├── input_pdfs/                        # Place your Legal Metrology PDFs here
│   ├── Legal_Metrology_Rules_2011.pdf # (Generated sample baseline rulebook)
│   └── Amendment_2021_USP.pdf         # (Generated sample gazette amendment)
├── output/                            # Generated consolidated artifacts
│   ├── Consolidated_Legal_Metrology_Rulebook_Human.pdf
│   ├── Machine_Rules_Specification.pdf
│   └── rules_knowledge_base.json
├── src/
│   ├── __init__.py
│   ├── pdf_parser.py                  # Extracts text, section titles & metadata from PDFs
│   ├── legal_synthesizer.py           # Merges baseline rules with amendments (tracked state)
│   ├── human_pdf_generator.py         # Generates government-style PDF report using ReportLab
│   └── machine_schema_generator.py    # Exports machine-readable JSON & spec PDF
├── generate_sample_pdfs.py            # Generates realistic PDF inputs for testing
├── main.py                            # Execution script
└── requirements.txt                   # Dependencies (pypdf, reportlab, fpdf2, pydantic)
```

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Generate Sample Legal PDFs
If you want to test with realistic mock legal PDFs:
```bash
python generate_sample_pdfs.py
```

### 3. Run the PDF Consolidation Engine
```bash
python main.py
```

### 4. Custom Input / Output Directories
You can drop any real PDF files into `./input_pdfs` and run:
```bash
python main.py --input_dir "C:\path\to\your\pdfs" --output_dir "./output"
```

---

## 📊 Next Steps: Connecting to Module 2 (Vision AI Engine)

Module 2 reads `output/rules_knowledge_base.json` directly to validate scanned product packaging images:
* **Mandatory Field Detection:** Compares extracted OCR text against `regex_patterns`.
* **Prohibited Unit Check:** Flags symbols like `gms`, `ML`, `KG.` against `prohibited_symbols`.
* **Font Height Validation:** Verifies numeral height ($mm$) against `RULE_7_FONT` thresholds.
