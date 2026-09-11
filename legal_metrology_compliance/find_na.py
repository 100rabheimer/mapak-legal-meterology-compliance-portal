import os
from src.pdf_parser import LegalPDFParser

parser = LegalPDFParser()
input_dir = './input_pdfs'
pdf_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')])

print(f"Scanning {len(pdf_files)} PDFs for any remaining N/A values...\n")

na_files = []
for f in pdf_files:
    path = os.path.join(input_dir, f)
    info = parser.parse_pdf(path)
    notif = info['notification_no']
    dt = info['date']
    if notif == 'N/A' or dt == 'N/A':
        na_files.append((f, notif, dt))
        print(f"N/A -> {f}\n       Notification: {notif} | Date: {dt}\n")

print(f"Total files with N/A remaining: {len(na_files)} out of {len(pdf_files)}")
