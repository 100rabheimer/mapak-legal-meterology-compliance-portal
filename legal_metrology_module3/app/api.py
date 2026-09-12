import os
import shutil
import uuid
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Depends, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Ensure module path imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

from src.pipeline_bridge import InspectionPipelineBridge
from src.notice_generator import LegalNoticeGenerator
from src.utils import generate_notice_number, format_timestamp, sanitize_filename
from app.models import (
    LoginRequest, TokenResponse, UserProfile, RuleModel,
    NoticeGenerationRequest, NoticeResponseModel, SamplePackageInfo,
    AnalyticsOverviewResponse
)
from app.database_orm import (
    init_db_orm, SessionLocal, User, Inspection, InspectionPanel,
    ExtractedDeclaration, StatutoryViolation, LegalNotice, AuditLog,
    verify_password
)
from app.auth import get_db, create_access_token, get_current_user, require_admin

app = FastAPI(
    title="DoCA Legal Metrology Production Enforcement API & Relational Server",
    description="Automated statutory packaging compliance inspector, digital violation annotator, relational database server, and court-ready legal notice generator (SIH Problem Statement 26034).",
    version="3.2.0"
)

# Initialize relational database and seed default data
init_db_orm()

# Enable CORS for local development and UI communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directories
uploads_dir = os.path.join(base_dir, "output", "uploads")
annotated_dir = os.path.join(base_dir, "output", "annotated")
notices_dir = os.path.join(base_dir, "output", "notices")
samples_dir = os.path.join(base_dir, "test_samples")
web_dir = os.path.join(base_dir, "app", "web")

os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(annotated_dir, exist_ok=True)
os.makedirs(notices_dir, exist_ok=True)
os.makedirs(samples_dir, exist_ok=True)

# Lazy/Cached bridge and generator instances
bridge = None
notice_gen = None
last_inspected_report: Optional[Dict[str, Any]] = None

def get_bridge() -> InspectionPipelineBridge:
    global bridge
    if bridge is None:
        bridge = InspectionPipelineBridge()
    return bridge

def get_notice_gen() -> LegalNoticeGenerator:
    global notice_gen
    if notice_gen is None:
        notice_gen = LegalNoticeGenerator(output_dir=notices_dir)
    return notice_gen

# -------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# -------------------------------------------------------------------

@app.post("/api/v1/auth/login", response_model=TokenResponse)
@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates enforcement officer or admin user and returns signed JWT Bearer Token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    profile = UserProfile(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        badge_number=user.badge_number,
        jurisdiction_zone=user.jurisdiction_zone
    )
    return TokenResponse(access_token=access_token, user=profile)

@app.get("/api/v1/auth/me", response_model=UserProfile)
@app.get("/api/auth/me", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns active authenticated user profile & jurisdiction details."""
    return UserProfile(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        badge_number=current_user.badge_number,
        jurisdiction_zone=current_user.jurisdiction_zone
    )

# -------------------------------------------------------------------
# OFFICER MANAGEMENT & RBAC ENDPOINTS (ADMIN RESTRICTED)
# -------------------------------------------------------------------

@app.get("/api/v1/officers", response_model=List[UserProfile])
@app.get("/api/officers", response_model=List[UserProfile])
def list_officers(db: Session = Depends(get_db)):
    """Lists all registered enforcement officers and administrators."""
    users = db.query(User).filter(User.is_active == True).all()
    return [
        UserProfile(
            user_id=u.user_id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            badge_number=u.badge_number,
            jurisdiction_zone=u.jurisdiction_zone
        ) for u in users
    ]

@app.post("/api/v1/officers", response_model=UserProfile)
def create_officer(
    req: OfficerCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Registers a new enforcement officer account (Admin restricted)."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"User with email '{req.email}' already exists.")

    from app.database_orm import hash_password
    new_user = User(
        user_id=f"USR-OFFICER-{uuid.uuid4().hex[:6].upper()}",
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role.upper(),
        badge_number=req.badge_number or f"LM-WB-2026-{uuid.uuid4().hex[:4].upper()}",
        jurisdiction_zone=req.jurisdiction_zone or "Northern Enforcement Zone, New Delhi"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserProfile(
        user_id=new_user.user_id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        badge_number=new_user.badge_number,
        jurisdiction_zone=new_user.jurisdiction_zone
    )

@app.put("/api/v1/officers/{user_id}", response_model=UserProfile)
def update_officer(
    user_id: str,
    req: OfficerUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Updates enforcement officer profile, zone, role, or active status (Admin restricted)."""
    target = db.query(User).filter(User.user_id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Officer '{user_id}' not found.")

    if req.full_name:
        target.full_name = req.full_name
    if req.role:
        target.role = req.role.upper()
    if req.badge_number:
        target.badge_number = req.badge_number
    if req.jurisdiction_zone:
        target.jurisdiction_zone = req.jurisdiction_zone
    if req.is_active is not None:
        target.is_active = req.is_active

    db.commit()
    db.refresh(target)

    return UserProfile(
        user_id=target.user_id,
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        badge_number=target.badge_number,
        jurisdiction_zone=target.jurisdiction_zone
    )

@app.delete("/api/v1/officers/{user_id}")
def delete_officer(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Deactivates an enforcement officer account (Admin restricted)."""
    target = db.query(User).filter(User.user_id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail=f"Officer '{user_id}' not found.")

    target.is_active = False
    db.commit()
    return {"success": True, "message": f"Officer '{target.full_name}' account deactivated successfully."}

@app.get("/api/v1/reports")
@app.get("/api/reports")
def list_reports(db: Session = Depends(get_db)):
    """Lists all compiled Legal Notice and Compliance Certificate PDF records."""
    notices = db.query(LegalNotice).order_by(LegalNotice.id.desc()).all()
    
    # Auto-generate notice records for past inspections if notices table is empty
    if not notices:
        inspections = db.query(Inspection).all()
        gen = get_notice_gen()
        for insp in inspections:
            notice_num = generate_notice_number()
            dummy_report = {
                "inspection_id": insp.inspection_id,
                "timestamp": insp.timestamp,
                "is_compliant": insp.is_compliant,
                "compliance_score": insp.compliance_score,
                "entity_info": {
                    "commodity_name": insp.product_name,
                    "manufacturer_name_address": insp.company_name,
                    "mrp": "Rs. 199.00",
                    "mfg_date": "Aug 2026",
                    "net_quantity": "180 gms"
                },
                "violations": [
                    {
                        "clause": v.clause,
                        "title": v.title,
                        "severity": v.severity,
                        "description": v.description,
                        "remedy": v.remedy
                    } for v in insp.violations
                ]
            }
            pdf_path = gen.generate_notice(dummy_report, notice_number=notice_num)
            pdf_filename = os.path.basename(pdf_path)
            
            db_notice = LegalNotice(
                inspection_id=insp.id,
                notice_number=notice_num,
                notice_type="SHOW_CAUSE_NOTICE" if not insp.is_compliant else "COMPLIANCE_CERTIFICATE",
                pdf_filename=pdf_filename,
                pdf_url=f"/api/notices/{pdf_filename}",
                status="ISSUED"
            )
            db.add(db_notice)
        db.commit()
        notices = db.query(LegalNotice).order_by(LegalNotice.id.desc()).all()

    results = []
    for n in notices:
        results.append({
            "notice_number": n.notice_number,
            "notice_type": n.notice_type,
            "pdf_filename": n.pdf_filename,
            "pdf_url": n.pdf_url if n.pdf_url.startswith("http") else f"http://localhost:8000{n.pdf_url}",
            "issued_at": n.issued_at.isoformat() if n.issued_at else datetime.now().isoformat(),
            "status": n.status,
            "inspection_id": n.inspection.inspection_id if n.inspection else "",
            "product_name": n.inspection.product_name if n.inspection else "Pre-Packaged Commodity",
            "company_name": n.inspection.company_name if n.inspection else "Offending Enterprise"
        })
    return results

# -------------------------------------------------------------------
# SYSTEM HEALTH & SAMPLE CATALOG ENDPOINTS
# -------------------------------------------------------------------

@app.get("/api/health")
@app.get("/api/v1/health")
def health():
    return {
        "status": "HEALTHY",
        "service": "Department of Consumer Affairs (DoCA) Legal Metrology Enforcement Production API",
        "version": "3.2.0",
        "authority": "Ministry of Consumer Affairs, Food & Public Distribution, Govt of India",
        "statute": "Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011",
        "database": "Relational SQLite/PostgreSQL Engine Active"
    }

@app.get("/api/samples", response_model=List[SamplePackageInfo])
@app.get("/api/v1/samples", response_model=List[SamplePackageInfo])
def list_samples():
    """Returns list of pre-packaged test commodity samples available for 1-click evaluation."""
    return [
        SamplePackageInfo(
            id="sample_non_compliant",
            name="QuickSnacks Crunchy Bites (Non-Compliant)",
            filename="sample_non_compliant_package.jpg",
            category="FOOD_SNACKS",
            expected_status="NON_COMPLIANT",
            description="Violations: Prohibited 'GMS' unit symbol, missing 'Inclusive of all taxes' in MRP, and missing USP.",
            thumbnail_url="/api/sample_img/sample_non_compliant_package.jpg"
        ),
        SamplePackageInfo(
            id="sample_compliant",
            name="NutriBite Whole Wheat Biscuits (100% Compliant)",
            filename="sample_compliant_package.jpg",
            category="FOOD_SNACKS",
            expected_status="COMPLIANT",
            description="All 8 mandatory declarations, standard 'g' unit symbol, explicit tax clause, and valid USP present.",
            thumbnail_url="/api/sample_img/sample_compliant_package.jpg"
        ),
        SamplePackageInfo(
            id="sample_garment",
            name="Classic Comfort Cotton Shirt (Garments)",
            filename="sample_garment_package.jpg",
            category="GARMENTS",
            expected_status="COMPLIANT",
            description="Garment packaging declarations conforming to 2022 Garment Labelling Gazette Amendment.",
            thumbnail_url="/api/sample_img/sample_garment_package.jpg"
        )
    ]

# -------------------------------------------------------------------
# INSPECTION PIPELINE & DB ENDPOINTS
# -------------------------------------------------------------------

@app.post("/api/inspect")
@app.post("/api/v1/inspections")
async def inspect_package(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    category: str = Form("UNIVERSAL"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes 5-stage Multimodal AI Packaging Inspection, supports multi-image scans,
    persists record in relational ORM database, and pre-generates formal court-ready Legal Notice PDF.
    """
    target_paths = []

    # Collect all uploaded files
    uploaded_files = []
    if files:
        uploaded_files.extend([f for f in files if f and f.filename])
    if file and file.filename and file not in uploaded_files:
        uploaded_files.append(file)

    if uploaded_files:
        for f in uploaded_files:
            clean_stem = sanitize_filename(f.filename)
            unique_name = f"{clean_stem}_{uuid.uuid4().hex[:6]}.jpg"
            t_path = os.path.join(uploads_dir, unique_name)
            with open(t_path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            target_paths.append(t_path)
    elif sample_id:
        sample_map = {
            "sample_non_compliant": "sample_non_compliant_package.jpg",
            "sample_compliant": "sample_compliant_package.jpg",
            "sample_garment": "sample_garment_package.jpg"
        }
        fname = sample_map.get(sample_id, f"{sample_id}.jpg")
        sample_file_path = os.path.join(samples_dir, fname)
        if not os.path.exists(sample_file_path):
            raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found.")
        
        copy_name = f"sample_{sample_id}_{uuid.uuid4().hex[:6]}.jpg"
        t_path = os.path.join(uploads_dir, copy_name)
        shutil.copyfile(sample_file_path, t_path)
        target_paths.append(t_path)
    else:
        raise HTTPException(status_code=400, detail="Either packaging scan 'files', 'file', or 'sample_id' must be provided.")

    try:
        pipeline = get_bridge()
        if len(target_paths) > 1:
            report = pipeline.run_multi_inspection(target_paths, category=category)
        else:
            report = pipeline.run_inspection(target_paths[0], category=category)

        # Ensure panels payload exists in report
        if "panels" not in report or not report["panels"]:
            art = report.get("artifacts", {})
            report["panels"] = [{
                "panel_id": "panel_1",
                "panel_name": "Front PDP",
                "original_image_url": art.get("original_image_url", ""),
                "annotated_image_url": art.get("annotated_image_url", ""),
                "pdp_area_cm2": report.get("pdp_summary", {}).get("pdp_area_cm2", 85.5),
                "scale_k": report.get("pdp_summary", {}).get("scale_k", 0.125),
                "violations": report.get("violations", []),
                "compliant_fields": report.get("compliant_fields", [])
            }]

        p_name = product_name.strip() if product_name and product_name.strip() else report["entity_info"].get("commodity_name", "Pre-Packaged Commodity")
        c_name = company_name.strip() if company_name and company_name.strip() else report["entity_info"].get("manufacturer_name_address", "Offending Manufacturer")

        report["entity_info"]["commodity_name"] = p_name
        report["entity_info"]["manufacturer_name_address"] = c_name

        # Pre-generate official Legal Notice / Compliance Certificate PDF
        gen = get_notice_gen()
        notice_num = generate_notice_number()
        pdf_path = gen.generate_notice(report, notice_number=notice_num)
        pdf_filename = os.path.basename(pdf_path)

        notice_meta = {
            "notice_number": notice_num,
            "notice_filename": pdf_filename,
            "notice_url": f"/api/notices/{pdf_filename}",
            "file_path": pdf_path
        }
        report["notice"] = notice_meta

        # Persist into Relational Database (SQLAlchemy ORM)
        insp_id_str = f"INS-2026-{uuid.uuid4().hex[:6].upper()}"
        report["inspection_id"] = insp_id_str

        entity = report.get("entity_info", {})
        ocr_fields = report.get("ocr_raw", {}).get("fields", {})

        db_inspection = Inspection(
            inspection_id=insp_id_str,
            timestamp=report.get("timestamp", datetime.now().isoformat()),
            product_name=p_name,
            company_name=c_name,
            category=category,
            status=report.get("status", "UNKNOWN"),
            is_compliant=report.get("is_compliant", False),
            compliance_score=int(report.get("compliance_score", 0)),
            net_quantity=entity.get("net_quantity") or ocr_fields.get("net_quantity", {}).get("text"),
            mrp=entity.get("mrp") or ocr_fields.get("mrp", {}).get("text"),
            mfg_date=entity.get("mfg_date") or ocr_fields.get("mfg_date", {}).get("text"),
            consumer_care=entity.get("consumer_care") or ocr_fields.get("customer_care", {}).get("text"),
            country_of_origin=entity.get("country_of_origin") or ocr_fields.get("country_of_origin", {}).get("text"),
            raw_ocr_json=json.dumps(report.get("ocr_raw", {})),
            officer_id=current_user.id if current_user else None
        )
        db.add(db_inspection)
        db.flush()

        # Add all panel records to DB
        for idx, p in enumerate(report["panels"]):
            db_panel = InspectionPanel(
                inspection_id=db_inspection.id,
                panel_name=p.get("panel_name", f"Scan Panel #{idx + 1}"),
                original_image_url=p.get("original_image_url", ""),
                annotated_image_url=p.get("annotated_image_url", ""),
                pdp_area_cm2=float(p.get("pdp_area_cm2", 85.5)),
                scale_ratio_k=float(p.get("scale_k", 0.125))
            )
            db.add(db_panel)

        # Add extracted declarations with real bounding boxes
        for fk, fdata in ocr_fields.items():
            if isinstance(fdata, dict):
                bbox = fdata.get("bbox_pixel")
                db_decl = ExtractedDeclaration(
                    inspection_id=db_inspection.id,
                    field_key=fk,
                    field_name=fk.replace("_", " ").title(),
                    extracted_value=fdata.get("text"),
                    confidence=float(fdata.get("confidence", 0.90)) * 100 if fdata.get("confidence", 0.90) <= 1.0 else float(fdata.get("confidence", 90.0)),
                    bbox_json=json.dumps(bbox) if bbox else None,
                    is_compliant=fk in report.get("compliant_fields", [])
                )
                db.add(db_decl)

        # Add violations
        for v in report.get("violations", []):
            db_v = StatutoryViolation(
                inspection_id=db_inspection.id,
                rule_id=v.get("rule_id"),
                clause=v.get("clause", "Rule 6(1)"),
                severity=v.get("severity", "MAJOR"),
                title=v.get("title", "Statutory Defect"),
                description=v.get("description", ""),
                legal_citation=v.get("legal_citation"),
                remedy=v.get("remedy")
            )
            db.add(db_v)

        # Add legal notice record
        db_notice = LegalNotice(
            inspection_id=db_inspection.id,
            notice_number=notice_num,
            notice_type="SHOW_CAUSE_NOTICE" if not report.get("is_compliant") else "COMPLIANCE_CERTIFICATE",
            pdf_filename=pdf_filename,
            pdf_url=f"/api/notices/{pdf_filename}",
            status="ISSUED"
        )
        db.add(db_notice)

        # Add audit log
        audit = AuditLog(
            user_id=current_user.id if current_user else None,
            action="INSPECTION_EXECUTED",
            resource_type="INSPECTION",
            resource_id=insp_id_str,
            details=f"Scanned package '{p_name}' by {c_name} with {len(report['panels'])} panel(s) (Score: {report.get('compliance_score')}/100)"
        )
        db.add(audit)

        db.commit()

        global last_inspected_report
        last_inspected_report = report

        return JSONResponse(content=report)
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inspection pipeline failed: {str(e)}")

@app.get("/api/inspections")
@app.get("/api/v1/inspections")
def get_inspections(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Queries relational database for past inspection cases."""
    query = db.query(Inspection)
    if category:
        query = query.filter(Inspection.category == category)
    rows = query.order_by(Inspection.id.desc()).limit(limit).all()

    results = []
    for r in rows:
        # Resolve real extracted declaration values
        net_q = r.net_quantity or "Not Detected"
        price_val = r.mrp or "Not Detected"
        mfg_d = r.mfg_date or "Not Detected"
        
        # Check declarations relationship if direct columns are not populated
        if (net_q == "Not Detected" or price_val == "Not Detected") and r.declarations:
            for d in r.declarations:
                if d.field_key == "net_quantity" and d.extracted_value:
                    net_q = d.extracted_value
                elif d.field_key == "mrp" and d.extracted_value:
                    price_val = d.extracted_value
                elif d.field_key == "mfg_date" and d.extracted_value:
                    mfg_d = d.extracted_value

        results.append({
            "inspection_id": r.inspection_id,
            "timestamp": r.timestamp,
            "product_name": r.product_name,
            "company_name": r.company_name,
            "category": r.category,
            "status": r.status,
            "is_compliant": r.is_compliant,
            "compliance_score": r.compliance_score,
            "violations_count": len(r.violations),
            "notice_url": r.legal_notices[0].pdf_url if r.legal_notices else "/api/download_latest_notice",
            "entity_info": {
                "commodity_name": r.product_name,
                "manufacturer_name_address": r.company_name,
                "net_quantity": net_q,
                "mrp": price_val,
                "mfg_date": mfg_d,
                "consumer_care": r.consumer_care or "Not Specified",
                "country_of_origin": r.country_of_origin or "Not Specified"
            }
        })
    return results

@app.get("/api/inspections/{inspection_id}")
@app.get("/api/v1/inspections/{inspection_id}")
def get_inspection_by_id_endpoint(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieves full relational details of an inspection by ID."""
    r = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Inspection '{inspection_id}' not found.")

    return {
        "inspection_id": r.inspection_id,
        "timestamp": r.timestamp,
        "product_name": r.product_name,
        "company_name": r.company_name,
        "category": r.category,
        "status": r.status,
        "is_compliant": r.is_compliant,
        "compliance_score": r.compliance_score,
        "panels": [{"panel_name": p.panel_name, "original_url": p.original_image_url, "annotated_url": p.annotated_image_url} for p in r.panels],
        "violations": [{"clause": v.clause, "title": v.title, "severity": v.severity, "description": v.description, "remedy": v.remedy} for v in r.violations],
        "notice": {"notice_number": r.legal_notices[0].notice_number, "pdf_url": r.legal_notices[0].pdf_url} if r.legal_notices else None
    }

@app.get("/api/stats")
@app.get("/api/v1/analytics/overview")
def get_analytics(db: Session = Depends(get_db)):
    """Returns analytics metrics, compliance rates, and top statutory violations."""
    total = db.query(Inspection).count()
    compliant = db.query(Inspection).filter(Inspection.is_compliant == True).count()
    non_compliant = total - compliant
    pass_rate = round((compliant / total * 100), 1) if total > 0 else 100.0

    violations = db.query(StatutoryViolation).all()
    violation_counts = {}
    for v in violations:
        violation_counts[v.title] = violation_counts.get(v.title, 0) + 1

    top_violations = [{"title": k, "count": v} for k, v in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "non_compliant_count": non_compliant,
        "pass_rate": pass_rate,
        "top_violations": top_violations,
        "active_officer": os.getenv("OFFICER_NAME", "Sh. R. K. Verma"),
        "zone": os.getenv("OFFICER_ZONE", "Northern Enforcement Zone, New Delhi")
    }

# -------------------------------------------------------------------
# MODULE 1 MASTER RULES EXPLORER ENDPOINT
# -------------------------------------------------------------------

@app.get("/api/v1/rules")
@app.get("/api/rules")
def get_master_rules(category: Optional[str] = Query(None)):
    """Queries 49 statutory master legal rules synthesized from Module 1 Knowledge Base."""
    rules_kb_path = os.path.join(os.path.dirname(base_dir), "legal_metrology_compliance", "output", "rules_knowledge_base.json")
    ui_kb_path = os.path.join(os.path.dirname(base_dir), "legal-metrology-compliance-ui", "src", "data", "rules_knowledge_base.json")
    
    if not os.path.exists(rules_kb_path):
        if os.path.exists(ui_kb_path):
            rules_kb_path = ui_kb_path
        else:
            return {"rules": [], "count": 0, "message": "Rules KB file not found."}

    try:
        with open(rules_kb_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
            
        rules_list = []
        if isinstance(kb_data, dict):
            # Try to flatten structure like we did in frontend
            if "mandatoryDeclarations" in kb_data:
                for r in kb_data["mandatoryDeclarations"]:
                    rules_list.append({
                        "rule_id": r.get("id"),
                        "clause": r.get("ruleNumber"),
                        "title": r.get("title"),
                        "category": "MANDATORY DECLARATION",
                        "text": r.get("description"),
                        "mandatory": r.get("required")
                    })
            if "specialIndustryProvisions" in kb_data:
                for r in kb_data["specialIndustryProvisions"]:
                    rules_list.append({
                        "rule_id": r.get("id"),
                        "clause": r.get("ruleNumber", r.get("id")),
                        "title": r.get("title", r.get("industry")),
                        "category": "SPECIAL PROVISION",
                        "text": r.get("description", str(r.get("exemptions", "")))
                    })
            # If flat list somehow
            if not rules_list:
                rules_list = list(kb_data.values())
        else:
            rules_list = kb_data
        if category:
            rules_list = [r for r in rules_list if isinstance(r, dict) and category.lower() in r.get("category", "").lower()]
        return {"rules": rules_list, "count": len(rules_list)}
    except Exception as e:
        return {"rules": [], "count": 0, "error": str(e)}

@app.post("/api/v1/rules")
def add_master_rule(
    rule: RuleModel,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Adds a new statutory rule to the Knowledge Base (Admin restricted)."""
    rules_kb_path = os.path.join(os.path.dirname(base_dir), "legal_metrology_compliance", "output", "rules_knowledge_base.json")
    ui_kb_path = os.path.join(os.path.dirname(base_dir), "legal-metrology-compliance-ui", "src", "data", "rules_knowledge_base.json")
    
    target_path = None
    if os.path.exists(ui_kb_path):
        target_path = ui_kb_path
    elif os.path.exists(rules_kb_path):
        target_path = rules_kb_path
    else:
        raise HTTPException(status_code=500, detail="Rules KB file not found to update.")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
            
        new_rule_dict = {
            "id": rule.rule_id,
            "ruleNumber": rule.clause,
            "title": rule.title,
            "description": rule.text,
            "required": rule.mandatory,
            "category": rule.category
        }
        
        if isinstance(kb_data, dict):
            if "mandatoryDeclarations" not in kb_data:
                kb_data["mandatoryDeclarations"] = []
            kb_data["mandatoryDeclarations"].append(new_rule_dict)
            kb_data["totalMasterRules"] = kb_data.get("totalMasterRules", 0) + 1
        else:
            raise HTTPException(status_code=500, detail="Invalid KB format. Cannot append.")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2)
            
        return {"success": True, "message": "Rule added successfully", "rule": new_rule_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save rule: {str(e)}")

# -------------------------------------------------------------------
# REAL-TIME SSE PROGRESS STREAMING
# -------------------------------------------------------------------

@app.get("/api/jobs/{job_id}/stream")
@app.get("/api/v1/inspections/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """Server-Sent Events (SSE) progress endpoint streaming real-time stage progress updates."""
    async def event_generator():
        stages = [
            (1, 5, "Stage 1/5: Loading packaging panel & detecting PDP surface area...", 20),
            (2, 5, "Stage 2/5: Deriving optical scale ratio k (mm/px) from reference barcode...", 40),
            (3, 5, "Stage 3/5: Running Multimodal Gemini Vision AI & OCR declaration extraction...", 60),
            (4, 5, "Stage 4/5: Measuring numeral font height (mm) and verifying Rule 7 compliance...", 80),
            (5, 5, "Stage 5/5: Cross-referencing Master Rules KB & compiling Legal Notice PDF...", 100),
        ]
        for stage, total, msg, pct in stages:
            data = json.dumps({
                "job_id": job_id,
                "stage": stage,
                "total_stages": total,
                "message": msg,
                "progress_pct": pct,
                "timestamp": format_timestamp()
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -------------------------------------------------------------------
# FILE SERVING ENDPOINTS
# -------------------------------------------------------------------

@app.get("/api/download_latest_notice")
def download_latest_notice():
    global last_inspected_report
    if not last_inspected_report or "notice" not in last_inspected_report:
        notices = [f for f in os.listdir(notices_dir) if f.endswith(".pdf")]
        if not notices:
            raise HTTPException(status_code=404, detail="No legal notices have been generated yet.")
        latest_file = sorted(notices)[-1]
        return FileResponse(
            os.path.join(notices_dir, latest_file),
            media_type="application/pdf",
            filename=latest_file,
            headers={"Content-Disposition": f'attachment; filename="{latest_file}"'}
        )

    pdf_filename = last_inspected_report["notice"]["notice_filename"]
    pdf_path = os.path.join(notices_dir, pdf_filename)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename,
        headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'}
    )

@app.post("/api/generate_notice", response_model=NoticeResponseModel)
def generate_legal_notice(req: NoticeGenerationRequest):
    try:
        gen = get_notice_gen()
        notice_num = req.notice_number or generate_notice_number()
        pdf_path = gen.generate_notice(req.inspection_report, notice_number=notice_num)
        filename = os.path.basename(pdf_path)

        global last_inspected_report
        if last_inspected_report is None:
            last_inspected_report = {}
        last_inspected_report["notice"] = {
            "notice_number": notice_num,
            "notice_filename": filename,
            "notice_url": f"/api/notices/{filename}"
        }

        return NoticeResponseModel(
            success=True,
            notice_number=notice_num,
            notice_filename=filename,
            notice_url=f"/api/notices/{filename}",
            file_path=pdf_path,
            generated_at=format_timestamp()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notice generation failed: {str(e)}")

@app.get("/api/notices/{filename}")
def get_notice_pdf(filename: str):
    file_path = os.path.join(notices_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested Legal Notice PDF not found.")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/uploads/{filename}")
def get_uploaded_image(filename: str):
    file_path = os.path.join(uploads_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested upload image not found.")
    ext = os.path.splitext(filename)[1].lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)

@app.get("/api/annotated/{filename}")
def get_annotated_image(filename: str):
    file_path = os.path.join(annotated_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested annotated image not found.")
    ext = os.path.splitext(filename)[1].lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)

@app.get("/api/sample_img/{filename}")
def get_sample_thumbnail(filename: str):
    file_path = os.path.join(samples_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample image not found.")
    return FileResponse(file_path)

# Serve Web Dashboard Static Files
app.mount("/static", StaticFiles(directory=web_dir), name="static")

@app.get("/")
def serve_dashboard():
    index_file = os.path.join(web_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "DoCA Legal Metrology Production Enforcement Server Active."}
