import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "output", "legal_metrology_relational.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

os.makedirs(os.path.dirname(db_path), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Helper for simple password hashing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# ORM Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="OFFICER") # OFFICER, ADMIN, SUPERVISOR
    badge_number = Column(String(50), nullable=True)
    jurisdiction_zone = Column(String(100), default="Northern Enforcement Zone, New Delhi")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inspections = relationship("Inspection", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="user")

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(50), unique=True, index=True, nullable=False)
    timestamp = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    brand_name = Column(String(100), nullable=True)
    company_name = Column(String(200), nullable=False)
    category = Column(String(50), default="UNIVERSAL")
    status = Column(String(50), nullable=False) # PASS, VIOLATION DETECTED, WARNING
    is_compliant = Column(Boolean, default=False)
    compliance_score = Column(Integer, default=0)
    
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    officer = relationship("User", back_populates="inspections")

    panels = relationship("InspectionPanel", back_populates="inspection", cascade="all, delete-orphan")
    declarations = relationship("ExtractedDeclaration", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("StatutoryViolation", back_populates="inspection", cascade="all, delete-orphan")
    legal_notices = relationship("LegalNotice", back_populates="inspection", cascade="all, delete-orphan")

class InspectionPanel(Base):
    __tablename__ = "inspection_panels"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    panel_name = Column(String(50), default="Front PDP") # Front PDP, Back Panel, Side Panel
    original_image_url = Column(Text, nullable=False)
    annotated_image_url = Column(Text, nullable=False)
    pdp_area_cm2 = Column(Float, default=85.5)
    scale_ratio_k = Column(Float, default=0.125)

    inspection = relationship("Inspection", back_populates="panels")

class ExtractedDeclaration(Base):
    __tablename__ = "extracted_declarations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    field_key = Column(String(50), nullable=False) # net_quantity, mrp, mfg_date, etc.
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=True)
    confidence = Column(Float, default=90.0)
    bbox_json = Column(Text, nullable=True) # [x1, y1, x2, y2]
    measured_font_height_mm = Column(Float, nullable=True)
    required_min_font_height_mm = Column(Float, nullable=True)
    is_compliant = Column(Boolean, default=True)
    violation_message = Column(Text, nullable=True)

    inspection = relationship("Inspection", back_populates="declarations")

class StatutoryViolation(Base):
    __tablename__ = "statutory_violations"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String(50), nullable=True) # RULE_6_1_E, RULE_11_UNITS, etc.
    clause = Column(String(100), nullable=False) # Rule 6(1)(e)
    severity = Column(String(20), default="MAJOR") # CRITICAL, MAJOR, MINOR
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    legal_citation = Column(Text, nullable=True)
    remedy = Column(Text, nullable=True)
    fine_amount_str = Column(String(100), default="Fine up to ₹25,000")

    inspection = relationship("Inspection", back_populates="violations")

class LegalNotice(Base):
    __tablename__ = "legal_notices"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    notice_number = Column(String(100), unique=True, index=True, nullable=False)
    notice_type = Column(String(50), nullable=False) # SHOW_CAUSE_NOTICE, COMPLIANCE_CERTIFICATE
    pdf_filename = Column(String(255), nullable=False)
    pdf_url = Column(Text, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="ISSUED") # ISSUED, SERVED, PENDING_REPLY

    inspection = relationship("Inspection", back_populates="legal_notices")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="audit_logs")

# Database initialization and seeder
def init_db_orm():
    Base.metadata.create_all(bind=engine)
    seed_default_data()

def seed_default_data():
    db = SessionLocal()
    try:
        # 1. Seed Officer user
        officer = db.query(User).filter(User.email == "officer@doca.gov.in").first()
        if not officer:
            officer = User(
                user_id="USR-OFFICER-001",
                email="officer@doca.gov.in",
                hashed_password=hash_password("officer123"),
                full_name="Sh. R. K. Verma",
                role="OFFICER",
                badge_number="LM-WB-2026-0148",
                jurisdiction_zone="Northern Enforcement Zone, New Delhi"
            )
            db.add(officer)

        # 2. Seed Admin user
        admin = db.query(User).filter(User.email == "admin@doca.gov.in").first()
        if not admin:
            admin = User(
                user_id="USR-ADMIN-001",
                email="admin@doca.gov.in",
                hashed_password=hash_password("admin123"),
                full_name="Director S. K. Sharma",
                role="ADMIN",
                badge_number="LM-HQ-2026-0001",
                jurisdiction_zone="Central Enforcement Headquarters, New Delhi"
            )
            db.add(admin)

        db.commit()

        # 3. Seed initial sample case if database is empty
        count = db.query(Inspection).count()
        if count == 0:
            sample_inspection = Inspection(
                inspection_id="INS-2026-00147",
                timestamp=datetime.now().isoformat(),
                product_name="Herbal Shampoo 180 ml",
                brand_name="GreenCare",
                company_name="GreenCare Pvt. Ltd.",
                category="COSMETICS",
                status="NON-COMPLIANT / VIOLATION DETECTED",
                is_compliant=False,
                compliance_score=40,
                officer_id=officer.id if officer else None
            )
            db.add(sample_inspection)
            db.flush()

            panel = InspectionPanel(
                inspection_id=sample_inspection.id,
                panel_name="Front PDP",
                original_image_url="/api/sample_img/sample_non_compliant_package.jpg",
                annotated_image_url="/api/sample_img/sample_non_compliant_package.jpg",
                pdp_area_cm2=85.5,
                scale_ratio_k=0.125
            )
            db.add(panel)

            v1 = StatutoryViolation(
                inspection_id=sample_inspection.id,
                rule_id="RULE_11_UNITS",
                clause="Rule 11 & Schedule II",
                severity="CRITICAL",
                title="Illegal Unit Symbol 'gms' Used",
                description="The declaration contains non-compliant unit symbol 'gms'. Mandatory legal symbol is 'g'.",
                legal_citation="Rule 11 & Schedule II, Legal Metrology (Packaged Commodities) Rules, 2011",
                remedy="Replace non-standard unit symbol 'gms' with standard SI symbol 'g'."
            )
            v2 = StatutoryViolation(
                inspection_id=sample_inspection.id,
                rule_id="RULE_6_1_E",
                clause="Rule 6(1)(e)",
                severity="MAJOR",
                title="Missing Mandatory Tax Phrase in MRP",
                description="The MRP declaration omits statutory phrase 'inclusive of all taxes'.",
                legal_citation="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
                remedy="Format MRP declaration as: 'MRP ₹ XX.XX (inclusive of all taxes)'."
            )
            db.add_all([v1, v2])

            notice = LegalNotice(
                inspection_id=sample_inspection.id,
                notice_number="DoCA/LM/2026/09-5035",
                notice_type="SHOW_CAUSE_NOTICE",
                pdf_filename="Legal_Notice_DoCA_LM_2026_09-5035.pdf",
                pdf_url="/api/download_latest_notice",
                status="ISSUED"
            )
            db.add(notice)
            db.commit()

            print("[+] Relational ORM Database seeded with initial users and sample inspection case.")

    except Exception as e:
        print(f"[!] Error seeding ORM database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db_orm()
