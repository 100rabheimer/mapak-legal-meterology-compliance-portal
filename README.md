# Legal Metrology Compliance Portal
## Automated AI Packaging Enforcement System — Department of Consumer Affairs (DoCA)

<div align="center">

![Legal Metrology](https://img.shields.io/badge/Ministry_of_Consumer_Affairs-Govt._of_India-FF6B35?style=for-the-badge&logo=india&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**SIH 2024 Problem Statement #26034 — Smart India Hackathon**

*An end-to-end, production-grade AI enforcement portal for automated legal metrology compliance verification of pre-packaged commodities under the Legal Metrology Act, 2009 and Packaged Commodities Rules, 2011.*

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Module Documentation](#module-documentation)
- [API Reference](#api-reference)
- [Default Credentials](#default-credentials)
- [Screenshots](#screenshots)
- [Contributing](#contributing)

---

## 🎯 Overview

The **Legal Metrology Compliance Portal** is a 3-module, production-grade automated inspection system designed for Legal Metrology Enforcement Officers (LMEOs) under the Department of Consumer Affairs (DoCA), Government of India.

It automates the labour-intensive process of manually inspecting pre-packaged commodity labels for statutory violations under:
- **Legal Metrology Act, 2009**
- **Legal Metrology (Packaged Commodities) Rules, 2011**
- **Rule 6(1)** – Mandatory declarations
- **Rule 7** – Minimum numeral font height
- **Rule 11** – Prohibited unit symbols (e.g., "gms", "GMS")

An enforcement officer can simply **upload 1–4 packaging label photos**, and the AI pipeline will:
1. Extract all mandatory declarations via Gemini Vision AI OCR
2. Measure numeral font heights using optical calibration
3. Cross-reference against a structured Legal Knowledge Base
4. Generate court-ready **Show-Cause Notices** or **Compliance Certificates** as PDFs
5. Persist all records to a relational database with full audit trails

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MAPAK COMPLIANCE PORTAL                          │
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐   ┌───────────────┐  │
│  │   MODULE 1       │    │   MODULE 2       │   │   MODULE 3    │  │
│  │  Legal KB Engine │───▶│  Vision AI       │──▶│  FastAPI +    │  │
│  │                  │    │  Pipeline        │   │  Dashboard UI │  │
│  │ • Rules Parser   │    │ • ImageProcessor │   │ • RBAC Auth   │  │
│  │ • PDF Scraper    │    │ • FontCalibrator │   │ • SQLite ORM  │  │
│  │ • KB JSON Store  │    │ • OCR Extractor  │   │ • PDF Notice  │  │
│  │                  │    │ • Pkg Inspector  │   │   Generator   │  │
│  │                  │    │ • VisualAnnotator│   │ • Analytics   │  │
│  └──────────────────┘    └──────────────────┘   └───────────────┘  │
│                                                         ▲           │
│                                          ┌──────────────┘           │
│                                          │                          │
│                              ┌─────────────────────┐               │
│                              │  REACT UI (Module 4) │               │
│                              │  • Officer Dashboard │               │
│                              │  • Admin Portal      │               │
│                              │  • Vision AI Canvas  │               │
│                              │  • Multi-Image Scans │               │
│                              │  • Analytics Charts  │               │
│                              └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 5-Stage AI Inspection Pipeline

```
[1] ImageProcessor       → PDP boundary detection, deskewing, surface area (cm²)
       ↓
[2] FontCalibrator       → Barcode-derived mm/px scale ratio, Rule 7 verification
       ↓
[3] OCRExtractor         → Gemini 3.5 Flash Vision AI, multilingual field extraction + bounding boxes
       ↓
[4] PackagingInspector   → Module 1 Rules KB cross-reference, violation scoring
       ↓
[5] VisualAnnotator      → OpenCV pixel-accurate bounding box annotation + compliance colour coding
```

---

## ✨ Features

### 👮 Officer Panel
- **Multi-Image Upload**: Upload 1–4 packaging scan images (drag & drop, file picker, or live camera)
- **AI Vision Canvas**: Side-by-side annotated image with pixel-accurate OpenCV bounding boxes
- **Original / Annotated Toggle**: Switch between raw scan and AI-annotated view
- **Extracted Declarations Table**: All 8 mandatory fields with OCR confidence scores
- **Compliance Result Scorecard**: 0–100% score with statutory violation breakdown
- **PDF Show-Cause Notice / Certificate**: One-click court-ready PDF generation and direct download
- **My Inspections History**: Full audit trail with status, score, and document access

### 👑 Admin Panel
- **Real-Time Dashboard**: Live metrics — total scans, compliance rate, violations, active officers
- **Officer Management**: Create, update, deactivate enforcement officer accounts (RBAC)
- **Analytics Page**: Dark-slate themed charts — violation frequency, trend analysis, zone-wise stats
- **Full Inspection Registry**: Complete database view with search and filter

### 🔐 Security
- **JWT Bearer Token Authentication** — RS256 signed
- **Role-Based Access Control (RBAC)** — Officer vs. Admin roles
- **Offline Fallback Mode** — Demo credentials work without backend for UI testing

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript 5, Vite, TailwindCSS |
| **Backend API** | FastAPI 0.115, Uvicorn, SQLAlchemy ORM |
| **Database** | SQLite (dev) / PostgreSQL-compatible (prod) |
| **AI / Vision** | Google Gemini 3.5 Flash Vision API, OpenCV 4, Tesseract |
| **PDF Generation** | ReportLab |
| **Auth** | JWT (PyJWT), bcrypt password hashing |
| **Module 1** | pdfplumber, Camelot, spaCy NLP, JSON KB |

---

## 📁 Project Structure

```
Mapak/
├── legal_metrology_compliance/          # Module 1: Legal Knowledge Base Engine
│   ├── src/
│   │   ├── pdf_parser.py               # Gazette PDF scraper & table extractor
│   │   ├── rule_extractor.py           # NLP-based rule clause parser
│   │   ├── knowledge_base_builder.py   # Structured KB JSON builder
│   │   └── rule_matcher.py             # Rule-to-declaration matcher
│   ├── output/
│   │   └── rules_knowledge_base.json   # Compiled statutory rules KB
│   ├── main.py
│   └── requirements.txt
│
├── legal_metrology_module2/             # Module 2: Vision AI Inspection Pipeline
│   ├── src/
│   │   ├── image_processor.py          # PDP detection, deskewing, surface area
│   │   ├── font_calibrator.py          # Barcode scale ratio, Rule 7 verification
│   │   ├── ocr_extractor.py            # Gemini Vision AI + bounding box extraction
│   │   ├── packaging_inspector.py      # Compliance engine (Module 1 integration)
│   │   └── visual_annotator.py         # OpenCV bounding box painter
│   ├── main.py
│   └── requirements.txt
│
├── legal_metrology_module3/             # Module 3: FastAPI Backend + Database
│   ├── app/
│   │   ├── api.py                      # All REST endpoints + multi-image upload
│   │   ├── auth.py                     # JWT auth, RBAC middleware
│   │   ├── database_orm.py             # SQLAlchemy ORM models + seeder
│   │   └── models.py                   # Pydantic request/response schemas
│   ├── src/
│   │   ├── pipeline_bridge.py          # Module 2 integration bridge
│   │   ├── notice_generator.py         # ReportLab PDF notice/certificate generator
│   │   └── utils.py                    # Shared utilities
│   ├── output/                         # Runtime: DB, annotated images, PDFs
│   ├── main.py
│   └── requirements.txt
│
├── legal-metrology-compliance-ui/       # Module 4: React Officer Dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── OfficerDashboardPage.tsx
│   │   │   ├── NewInspectionPage.tsx   # Multi-image drag & drop upload
│   │   │   ├── ReviewPage.tsx          # AI Vision Canvas + panel tabs
│   │   │   ├── ResultPage.tsx          # Compliance scorecard + PDF download
│   │   │   ├── ReportsPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── MyInspectionsPage.tsx
│   │   │   └── AdminDashboardPage.tsx
│   │   ├── services/
│   │   │   ├── apiClient.ts            # FastAPI integration + auth
│   │   │   ├── visionAiService.ts      # Frontend inspection pipeline model
│   │   │   └── legalNoticeGenerator.ts
│   │   └── components/
│   ├── package.json
│   └── vite.config.ts
│
└── run_system.py                        # One-click full system launcher
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Google Gemini API Key** (Gemini 3.5 Flash Vision)
- **Tesseract OCR** (optional, fallback)

### 1. Clone the Repository

```bash
git clone https://github.com/100rabheimer/mapak-legal-meterology-compliance-portal.git
cd mapak-legal-meterology-compliance-portal
```

### 2. Set Up Module 1 — Legal Knowledge Base

```bash
cd legal_metrology_compliance
pip install -r requirements.txt
python main.py   # Builds rules_knowledge_base.json
```

### 3. Set Up Module 2 — Vision AI Pipeline

```bash
cd ../legal_metrology_module2
pip install -r requirements.txt
# Configure .env (copy from .env.example)
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 4. Set Up Module 3 — FastAPI Backend

```bash
cd ../legal_metrology_module3
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start the API server
python main.py --serve
# Server runs at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 5. Set Up Module 4 — React UI

```bash
cd ../legal-metrology-compliance-ui
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000

npm run dev
# UI runs at http://localhost:5173
```

### 6. One-Click Launch (All Modules)

```bash
cd ..
python run_system.py
```

---

## 📖 Module Documentation

### Module 1 — Legal Knowledge Base Engine

Scrapes and structures the Gazette notifications and statutory rules into a machine-readable JSON knowledge base.

```bash
python main.py --build    # Build/rebuild the KB from PDFs
python scan_package.py    # Test a single package scan against KB
```

**Output**: `output/rules_knowledge_base.json` — structured rules with clause IDs, field names, violation descriptions, penalties, and remedies.

---

### Module 2 — Vision AI Inspection Pipeline

Runs the 5-stage inspection pipeline on packaging images.

```bash
# Single image scan
python main.py --image path/to/label.jpg --category FOOD_SNACKS

# Output: annotated PNG + JSON report
```

**Categories supported**: `UNIVERSAL`, `FOOD_SNACKS`, `BEVERAGES`, `GARMENTS`, `COSMETICS`, `ELECTRONICS`, `PHARMACEUTICALS`

---

### Module 3 — FastAPI Backend

```bash
python main.py --serve    # Start production server
```

**Key Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | JWT authentication |
| `POST` | `/api/v1/inspections` | Run AI inspection (supports 1–4 images) |
| `GET`  | `/api/v1/inspections` | List all inspection records |
| `GET`  | `/api/v1/inspections/{id}` | Get inspection details + panels |
| `GET`  | `/api/v1/analytics/overview` | Real-time compliance analytics |
| `GET`  | `/api/v1/reports` | List generated legal notices |
| `GET`  | `/api/notices/{filename}` | Download PDF notice |
| `GET`  | `/api/annotated/{filename}` | Serve annotated image |
| `POST` | `/api/v1/officers` | Create officer account (Admin) |
| `GET`  | `/api/v1/officers` | List all officers (Admin) |
| `GET`  | `/api/health` | Server health check |

---

## 🔑 Default Credentials

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Enforcement Officer** | `officer@doca.gov.in` | `officer123` | Dashboard, Inspections, Reports, Analytics |
| **Administrator** | `admin@doca.gov.in` | `admin123` | Full access + Officer Management |

> ⚠️ **Change these credentials** before deploying to production. See `database_orm.py` → `seed_default_data()`.

---

## 🌐 API Reference

Full interactive Swagger documentation available at:
```
http://localhost:8000/docs
```

### Multi-Image Inspection Request

```bash
curl -X POST http://localhost:8000/api/v1/inspections \
  -H "Authorization: Bearer <token>" \
  -F "files=@front_label.jpg" \
  -F "files=@back_label.jpg" \
  -F "files=@side_label.jpg" \
  -F "product_name=Herbal Shampoo 180ml" \
  -F "company_name=GreenCare Pvt. Ltd." \
  -F "category=UNIVERSAL"
```

### Response Structure

```json
{
  "inspection_id": "INS-2026-A1B2C3",
  "status": "NON_COMPLIANT",
  "is_compliant": false,
  "compliance_score": 55,
  "violations": [
    {
      "clause": "Rule 11",
      "title": "Illegal Unit Symbol",
      "severity": "MAJOR",
      "description": "Prohibited symbol 'gms' used instead of 'g'",
      "remedy": "Replace with SI standard unit symbol 'g'"
    }
  ],
  "panels": [
    {
      "panel_id": "panel_1",
      "panel_name": "Front PDP",
      "annotated_image_url": "/api/annotated/annotated_front_xyz.png",
      "original_image_url": "/api/uploads/front_xyz.jpg"
    }
  ],
  "notice": {
    "notice_number": "DOCA/LM/ENF/2026/09-1234",
    "notice_url": "/api/notices/Legal_Notice_DOCA_LM_ENF_2026_09-1234.pdf"
  }
}
```

---

## 🧪 Testing with Sample Packages

The system includes 3 pre-loaded sample test cases:

```bash
# Test via API
curl -X POST http://localhost:8000/api/v1/inspections \
  -H "Authorization: Bearer <token>" \
  -F "sample_id=sample_non_compliant"   # or sample_compliant / sample_garment
```

Or use the **"Use Sample Package"** button in the UI dashboard.

---

## 📊 Real-Time Analytics

The analytics dashboard shows:
- Total inspections vs. compliance pass rate (live from DB)
- Top statutory violations by frequency
- Trend chart — compliance rate over time
- Zone-wise enforcement statistics

All data is **100% real-time from the SQLite database** — zero hardcoded values.

---

## 🔒 Environment Variables

### Module 3 (`.env`)

```env
GEMINI_API_KEY=your_gemini_api_key
MODULE2_PATH=../legal_metrology_module2
RULES_KB_PATH=../legal_metrology_compliance/output/rules_knowledge_base.json
SECRET_KEY=your_jwt_secret_key_min_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### React UI (`.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- **Smart India Hackathon 2024** — Problem Statement #26034
- **Ministry of Consumer Affairs, Food & Public Distribution, Govt. of India**
- **Department of Consumer Affairs (DoCA)** — Legal Metrology Division
- **Google Gemini Vision API** — Multilingual OCR backbone
- **ReportLab** — Court-ready PDF generation

---

<div align="center">

**Built with ❤️ for the Department of Consumer Affairs, Government of India**

*Protecting Consumer Rights through AI-Powered Enforcement*

</div>
