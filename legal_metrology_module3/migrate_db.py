import os
import sqlite3
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "output", "legal_metrology_relational.db")

print(f"Checking database at: {db_path}")
if not os.path.exists(db_path):
    print("Database does not exist yet.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Inspect existing columns in inspections table
cursor.execute("PRAGMA table_info(inspections)")
cols = [row[1] for row in cursor.fetchall()]
print(f"Existing columns: {cols}")

new_cols = [
    ("net_quantity", "TEXT"),
    ("mrp", "TEXT"),
    ("mfg_date", "TEXT"),
    ("consumer_care", "TEXT"),
    ("country_of_origin", "TEXT"),
    ("raw_ocr_json", "TEXT"),
]

for col_name, col_type in new_cols:
    if col_name not in cols:
        print(f"Adding column '{col_name}' ({col_type}) to inspections table...")
        cursor.execute(f"ALTER TABLE inspections ADD COLUMN {col_name} {col_type}")

# 2. Fix timestamps that might be in DD-MM-YYYY format
cursor.execute("SELECT id, timestamp, product_name, compliance_score, is_compliant FROM inspections")
rows = cursor.fetchall()
for r in rows:
    rid, ts, pname, score, is_comp = r
    # If timestamp has "IST" or dashes, convert or provide clean ISO
    iso_ts = ts
    if "IST" in str(ts) or "-" in str(ts):
        try:
            # e.g. 12-09-2026 07:52:29 IST
            clean_ts = str(ts).replace(" IST", "").strip()
            dt = datetime.strptime(clean_ts, "%d-%m-%Y %H:%M:%S")
            iso_ts = dt.isoformat()
        except Exception:
            iso_ts = datetime.utcnow().isoformat()
    
    # Check if compliance_score is 0 or needs recalibration
    cursor.execute("SELECT count(*) FROM statutory_violations WHERE inspection_id = ?", (rid,))
    viol_count = cursor.fetchone()[0]

    # Calculate real proportional score:
    # 8 mandatory checks. If viol_count violations exist:
    recalibrated_score = score
    if score == 0 and viol_count < 8:
        # Give genuine score based on present declarations:
        compliant_declarations = max(1, 8 - viol_count)
        recalibrated_score = int(round((compliant_declarations / 8.0) * 100))

    cursor.execute("""
        UPDATE inspections 
        SET timestamp = ?, compliance_score = ?
        WHERE id = ?
    """, (iso_ts, recalibrated_score, rid))

conn.commit()
print("Database columns and inspection records successfully upgraded!")
conn.close()
