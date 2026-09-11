# System Architecture & Implementation Plan: Legal Metrology Compliance Platform

This document presents the detailed architectural breakdown and implementation plan for building and integrating the **Legal Metrology Compliance Platform** according to the target multi-tier architecture diagram.

```
React + TypeScript + Tailwind CSS (Frontend UI)
                 │
                 │ REST API + SSE / WebSockets
                 ▼
        FastAPI Application Layer
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
 Auth/RBAC   Inspection   Reports
 Service     Service      Service
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
 Module 1     Module 2    PostgreSQL
 Rules KB     Vision AI   + Object Storage
       │         │
       └─────────┼─────────┘
                 ▼
        Audit Logs + Evidence
```

---

## Architecture Breakdown

### 1. Presentation Tier (Frontend UI)
* **Stack**: React 19, TypeScript, Tailwind CSS v4, Zustand, React Router DOM v7.
* **Responsibilities**:
  * Dual-role workspace UI (Enforcement Officer vs. Administrator).
  * Package image upload with drag-and-drop & live preview.
  * Real-time progress updates via **Server-Sent Events (SSE)** or WebSockets during Vision AI scanning.
  * Interactive OCR label review screen with visual bounding box overlays.
  * Dynamic compliance report viewer with Pass / Warning / Violation breakdowns.

### 2. FastAPI Application Layer & Microservices
* **Stack**: Python 3.11+, FastAPI, Pydantic v2, AsyncIO, Uvicorn.
* **Services**:
  * **Auth / RBAC Service**: OAuth2 with JWT tokens (Access + Refresh), password hashing (Argon2 / Passlib), role-based middleware (`officer`, `admin`).
  * **Inspection Service**: Manages inspection creation, file uploads, SSE streaming for image processing stages, field overrides, and decision sign-offs.
  * **Reports Service**: PDF generation service (ReportLab / WeasyPrint) for official compliance certificates and violation notices.

### 3. Core Modules & Data Tier
* **Module 1: Rules Knowledge Base (Rules KB)**:
  * Declarative, versioned Legal Metrology Rules engine (Legal Metrology Act & Packaged Commodities Rules).
  * Checks mandatory declarations (MRP declaration format, Net Qty unit symbols, Manufacturer/Packer address completeness, Consumer Care details, Month/Year of packing).
* **Module 2: Vision AI Pipeline**:
  * Image preprocessing (deskewing, contrast enhancement, noise reduction).
  * OCR / Document Layout Analysis (Tesseract / PaddleOCR / Vision LLM) returning bounding boxes `(ymin, xmin, ymax, xmax)`, text strings, and confidence scores.
  * Field mapping model linking raw bounding box text to statutory fields.
* **PostgreSQL Database & Object Storage**:
  * Relational DB for users, officer profiles, inspections, extracted fields, compliance evaluations, and versioned legal rules.
  * Object Storage (AWS S3 / MinIO / Local media volume) for raw and annotated packaging images.
* **Audit Logs & Evidence Service**:
  * Tamper-evident logging tracking every officer edit, confidence override, status change, and report generation action with timestamp and officer ID.

---

## User Review Required

> [!IMPORTANT]
> **Backend Architecture Setup**: The project currently contains the React + TypeScript frontend UI. Should we set up the FastAPI backend application inside a `./backend` subfolder within this codebase, or create mock API handlers / MSW / local FastAPI service alongside the frontend?

> [!NOTE]
> **Vision AI Engine Choice**: For local development and demonstration, we can implement Module 2 using lightweight Python OCR libraries (`EasyOCR` / `pytesseract` / OpenCV) or mock Vision AI responses with real bounding boxes.

---

## Open Questions

> [!IMPORTANT]
> 1. Do you prefer setting up the FastAPI backend structure inside a `backend/` directory in this workspace?
> 2. Should we start by building the FastAPI backend endpoints + PostgreSQL schemas + SSE streaming server, or first build a mock REST + SSE server for testing the frontend integration?

---

## Proposed Changes

### Component 1: Frontend REST & SSE Integration Layer

#### [MODIFY] [package.json](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/package.json)
* Add `axios` or modern `fetch` wrappers for REST API calls.

#### [NEW] [src/services/apiClient.ts](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/src/services/apiClient.ts)
* Axios/Fetch client configured with base URL, JWT bearer token interceptors, and automatic token refresh handling.

#### [NEW] [src/services/inspectionService.ts](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/src/services/inspectionService.ts)
* Service functions to upload package images via `FormData`, initiate inspection scans, fetch extraction results, and submit officer review edits.

#### [NEW] [src/services/sseClient.ts](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/src/services/sseClient.ts)
* SSE subscriber to stream real-time Vision AI progress (e.g. `Uploading` → `Preprocessing` → `OCR Extraction` → `Rule Validation`).

---

### Component 2: FastAPI Backend Application (`/backend`)

#### [NEW] [backend/main.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/main.py)
* Main FastAPI app initialization, CORS middleware, API router registration (`/api/v1`).

#### [NEW] [backend/app/config.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/config.py)
* Pydantic settings loading environment variables (database URL, JWT secret, storage path).

#### [NEW] [backend/app/routers/auth.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/routers/auth.py)
* Endpoints for login (`/auth/login`), profile (`/auth/me`), and user token management.

#### [NEW] [backend/app/routers/inspections.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/routers/inspections.py)
* Endpoints for creating inspections, uploading images, SSE progress stream (`GET /inspections/{id}/stream`), and saving officer reviews.

#### [NEW] [backend/app/services/rules_engine.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/services/rules_engine.py)
* Module 1 (Rules KB): Evaluates extracted declarations against statutory Legal Metrology rules and calculates compliance scores.

#### [NEW] [backend/app/services/vision_ai.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/services/vision_ai.py)
* Module 2 (Vision AI): OCR and layout analysis wrapper producing bounding box coordinates, text labels, and confidence metrics.

#### [NEW] [backend/app/db/models.py](file:///c:/Users/shaur/OneDrive/Desktop/legal-metrology-compliance-ui/backend/app/db/models.py)
* SQLAlchemy/SQLModel entities for `User`, `OfficerProfile`, `Inspection`, `ExtractedDeclaration`, `ComplianceRule`, `AuditLog`.

---

## Verification Plan

### Automated Tests
- **Frontend Verification**:
  - Run `npm run dev` and test full flow from login → new inspection upload → SSE progress stream → review → compliance result.
  - Run TypeScript compile check `npx tsc --noEmit`.
- **Backend Verification**:
  - Run FastAPI server with `uvicorn backend.main:app --reload`.
  - Execute API endpoint tests using `pytest` for Auth, Inspection lifecycle, Rules KB, and Audit log persistence.

### Manual Verification
- Test SSE live progress streaming during image upload and OCR extraction.
- Verify audit log entries are generated upon officer field modification or decision approval.
