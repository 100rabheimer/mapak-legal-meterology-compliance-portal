import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "output", "inspections.db")

def get_db_connection():
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        product_name TEXT,
        company_name TEXT,
        category TEXT DEFAULT 'UNIVERSAL',
        status TEXT NOT NULL,
        is_compliant INTEGER DEFAULT 0,
        compliance_score INTEGER DEFAULT 0,
        violations_json TEXT,
        compliant_fields_json TEXT,
        non_compliant_fields_json TEXT,
        pdp_summary_json TEXT,
        entity_info_json TEXT,
        penalty_info_json TEXT,
        artifacts_json TEXT,
        notice_json TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        officer_name TEXT,
        action TEXT NOT NULL,
        inspection_id TEXT,
        details TEXT
    );
    """)

    conn.commit()
    conn.close()

def save_inspection_record(report: Dict[str, Any], product_name: str = "", company_name: str = "") -> str:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    inspection_id = report.get("inspection_id")
    if not inspection_id:
        import uuid
        inspection_id = f"INS-2026-{uuid.uuid4().hex[:6].upper()}"
        report["inspection_id"] = inspection_id

    timestamp = report.get("timestamp", datetime.now().isoformat())
    category = report.get("category", "UNIVERSAL")
    status = report.get("status", "UNKNOWN")
    is_compliant = 1 if report.get("is_compliant", False) else 0
    compliance_score = report.get("compliance_score", 0)

    # Extract product name / company name if not explicitly passed
    entity_info = report.get("entity_info", {})
    if not product_name:
        product_name = entity_info.get("commodity_name", "Pre-Packaged Commodity")
    if not company_name:
        company_name = entity_info.get("manufacturer_name_address", "Offending Manufacturer")

    report["product_name"] = product_name
    report["company_name"] = company_name

    cursor.execute("""
    INSERT OR REPLACE INTO inspections (
        inspection_id, timestamp, product_name, company_name, category, status,
        is_compliant, compliance_score, violations_json, compliant_fields_json,
        non_compliant_fields_json, pdp_summary_json, entity_info_json,
        penalty_info_json, artifacts_json, notice_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inspection_id,
        timestamp,
        product_name,
        company_name,
        category,
        status,
        is_compliant,
        compliance_score,
        json.dumps(report.get("violations", [])),
        json.dumps(report.get("compliant_fields", [])),
        json.dumps(report.get("non_compliant_fields", [])),
        json.dumps(report.get("pdp_summary", {})),
        json.dumps(entity_info),
        json.dumps(report.get("penalty_info", {})),
        json.dumps(report.get("artifacts", {})),
        json.dumps(report.get("notice", {}))
    ))

    # Log audit event
    cursor.execute("""
    INSERT INTO audit_logs (timestamp, officer_name, action, inspection_id, details)
    VALUES (?, ?, ?, ?, ?)
    """, (
        timestamp,
        os.getenv("OFFICER_NAME", "Sh. R. K. Verma"),
        "INSPECTION_COMPLETED",
        inspection_id,
        f"Executed packaging audit for '{product_name}' (Score: {compliance_score}/100, Violations: {len(report.get('violations', []))})"
    ))

    conn.commit()
    conn.close()
    return inspection_id

def get_all_inspections(limit: int = 50, category: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("SELECT * FROM inspections WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit))
    else:
        cursor.execute("SELECT * FROM inspections ORDER BY id DESC LIMIT ?", (limit,))

    rows = cursor.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        item["is_compliant"] = bool(item["is_compliant"])
        item["violations"] = json.loads(item["violations_json"]) if item["violations_json"] else []
        item["compliant_fields"] = json.loads(item["compliant_fields_json"]) if item["compliant_fields_json"] else []
        item["non_compliant_fields"] = json.loads(item["non_compliant_fields_json"]) if item["non_compliant_fields_json"] else []
        item["pdp_summary"] = json.loads(item["pdp_summary_json"]) if item["pdp_summary_json"] else {}
        item["entity_info"] = json.loads(item["entity_info_json"]) if item["entity_info_json"] else {}
        item["penalty_info"] = json.loads(item["penalty_info_json"]) if item["penalty_info_json"] else {}
        item["artifacts"] = json.loads(item["artifacts_json"]) if item["artifacts_json"] else {}
        item["notice"] = json.loads(item["notice_json"]) if item["notice_json"] else {}
        results.append(item)

    conn.close()
    return results

def get_inspection_by_id(inspection_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        return None

    item = dict(r)
    item["is_compliant"] = bool(item["is_compliant"])
    item["violations"] = json.loads(item["violations_json"]) if item["violations_json"] else []
    item["compliant_fields"] = json.loads(item["compliant_fields_json"]) if item["compliant_fields_json"] else []
    item["non_compliant_fields"] = json.loads(item["non_compliant_fields_json"]) if item["non_compliant_fields_json"] else []
    item["pdp_summary"] = json.loads(item["pdp_summary_json"]) if item["pdp_summary_json"] else {}
    item["entity_info"] = json.loads(item["entity_info_json"]) if item["entity_info_json"] else {}
    item["penalty_info"] = json.loads(item["penalty_info_json"]) if item["penalty_info_json"] else {}
    item["artifacts"] = json.loads(item["artifacts_json"]) if item["artifacts_json"] else {}
    item["notice"] = json.loads(item["notice_json"]) if item["notice_json"] else {}
    return item

def get_analytics_summary() -> Dict[str, Any]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total, SUM(is_compliant) as compliant_count FROM inspections")
    row = cursor.fetchone()
    total = row["total"] if row and row["total"] else 0
    compliant = row["compliant_count"] if row and row["compliant_count"] else 0
    non_compliant = total - compliant

    pass_rate = round((compliant / total * 100), 1) if total > 0 else 100.0

    # Common violations breakdown
    cursor.execute("SELECT violations_json FROM inspections WHERE violations_json IS NOT NULL AND violations_json != '[]'")
    rows = cursor.fetchall()
    
    violation_counts = {}
    for r in rows:
        v_list = json.loads(r["violations_json"])
        for v in v_list:
            v_title = v.get("title", "General Violation")
            violation_counts[v_title] = violation_counts.get(v_title, 0) + 1

    top_violations = [{"title": k, "count": v} for k, v in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    conn.close()

    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "non_compliant_count": non_compliant,
        "pass_rate": pass_rate,
        "top_violations": top_violations,
        "active_officer": os.getenv("OFFICER_NAME", "Sh. R. K. Verma"),
        "zone": os.getenv("OFFICER_ZONE", "Northern Enforcement Zone, New Delhi")
    }
