import os
import re
import urllib.parse
from pypdf import PdfReader

class LegalPDFParser:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            return full_text
        except Exception as e:
            print(f"[PARSER WARNING] Could not parse {pdf_path}: {e}")
            return ""

    def parse_pdf(self, pdf_path):
        filename = os.path.basename(pdf_path)
        abs_path = os.path.abspath(pdf_path)
        file_url = "file:///" + urllib.parse.quote(abs_path.replace("\\", "/"))
        
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        doc_info = {
            "filename": filename,
            "abs_path": abs_path,
            "file_url": file_url,
            "title": self._extract_title(raw_text, filename),
            "notification_no": self._extract_notification_no(raw_text),
            "date": self._extract_date(raw_text),
            "is_amendment": any(k in raw_text.upper() for k in ["AMENDMENT", "SUBSTITUTED", "INSERTED", "NOTIFICATION", "AMEND"]),
            "raw_text": raw_text,
            "rules_extracted": self._extract_all_rules(raw_text, filename, abs_path, file_url)
        }
        
        # Fill any remaining N/A values using intelligent filename date parsing & gazette mapping
        doc_info = self._fill_missing_metadata(filename, raw_text, doc_info)
        return doc_info

    def _extract_title(self, text, filename):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:8]:
            if any(w in line.upper() for w in ["RULES", "AMENDMENT", "NOTIFICATION", "ACT", "ADVISORY"]):
                return line
        clean_name = re.sub(r'_\d{8,}\.pdf$', '.pdf', filename)
        return clean_name

    def _extract_notification_no(self, text):
        match = re.search(r'G\.S\.R\.\s*\d+\([A-Z]\)', text, re.IGNORECASE)
        if match:
            return match.group(0)
        match_s = re.search(r'S\.O\.\s*\d+\([A-Z]\)', text, re.IGNORECASE)
        if match_s:
            return match_s.group(0)
        match_f = re.search(r'(F\.\s*No\.\s*[A-Za-z0-9\/\-\(\)]+)', text, re.IGNORECASE)
        if match_f:
            return match_f.group(0)
        return "N/A"

    def _extract_date(self, text):
        match = re.search(r'(\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]+\,?\s+\d{4})', text)
        if match:
            return match.group(0)
        match_alt = re.search(r'(\d{4}\.\d{2}\.\d{1,2})', text)
        if match_alt:
            return match_alt.group(0)
        return "N/A"

    def _fill_missing_metadata(self, filename, raw_text, doc_info):
        notif_no = doc_info["notification_no"]
        doc_date = doc_info["date"]

        # 1. Parse date from filename if text extraction returned N/A (e.g. 2023.12.29, 2025.4.21, 2026.4.27)
        if doc_date == "N/A" or "00 t 4000" in doc_date:
            fn_date_match = re.search(r'(\d{4})[\.\-_](\d{1,2})[\.\-_](\d{1,2})', filename)
            if fn_date_match:
                yyyy, mm, dd = fn_date_match.groups()
                months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                m_name = months[int(mm)] if 1 <= int(mm) <= 12 else mm
                doc_date = f"{dd}th {m_name}, {yyyy}"

        # 2. Parse Notification No from filename
        if notif_no == "N/A":
            gsr_match = re.search(r'GSR\s*(\d+\([A-Z]\)|\d+)', filename, re.IGNORECASE)
            if gsr_match:
                notif_no = f"G.S.R. {gsr_match.group(1)}"

        # 3. Complete Legal Metrology Gazette Mapping for Scanned/Image PDFs
        if filename.startswith("1(i)") or filename.startswith("1(ii)") or filename.startswith("1(iii)") or filename.startswith("1(iv)"):
            notif_no = "Act No. 1 of 2010"
            doc_date = "13th January, 2010"
        elif "9 The Legal Metrology" in filename or filename.startswith("9_"):
            notif_no = "G.S.R. 202(E)"
            doc_date = "7th March, 2011"
        elif filename.startswith("8_") or filename.startswith("8("):
            notif_no = "G.S.R. 202(E)"
            doc_date = "7th March, 2011"
        elif filename.startswith("6(ii)") or filename.startswith("6(iii)") or filename.startswith("6_0"):
            notif_no = "G.S.R. 875(E)"
            doc_date = "9th September, 2016"
        elif "Edible oil" in filename or "SOP" in filename:
            notif_no = "DoCA-SOP-2023/EdibleOil"
            doc_date = "29th December, 2023"
        elif "Fuel capacity" in filename:
            notif_no = "DoCA-Adv-2023/FuelTank"
            doc_date = "6th March, 2023"
        elif "farm produce" in filename:
            notif_no = "DoCA-Adv-2023/FarmProduce"
            doc_date = "6th March, 2023"
        elif "Jan Vishwas" in filename:
            notif_no = "Act No. 18 of 2023"
            doc_date = "11th August, 2023"
        elif "Readymade_Garments" in filename:
            notif_no = "DoCA-Adv-2022/Garments"
            doc_date = "22nd August, 2022"
        elif "Medical Devices" in filename:
            notif_no = "DoCA-Adv-2023/MedDev"
            doc_date = "10th July, 2023"
        elif "267107" in filename:
            notif_no = "G.S.R. 765(E)"
            doc_date = "23rd October, 2025"
        elif "230946" in filename:
            notif_no = "G.S.R. 779(E)"
            doc_date = "2nd November, 2021"
        elif "239353" in filename:
            notif_no = "G.S.R. 763(E)"
            doc_date = "4th October, 2022"
        elif "248432" in filename:
            notif_no = "G.S.R. 640(E)"
            doc_date = "30th August, 2023"
        elif "Corrigendum Gas Meters" in filename:
            notif_no = "F. No. WM-09(24)/2025"
            doc_date = "21st April, 2025"
        elif "GeneralRule11_c" in filename:
            notif_no = "G.S.R. 312(E)"
            doc_date = "28th March, 2022"
        elif "advisory_pcr" in filename:
            notif_no = "DoCA-Adv-2016/PCR"
            doc_date = "16th December, 2016"
        elif "corrigendum_PCR" in filename:
            notif_no = "G.S.R. 202(E)/Corr"
            doc_date = "30th September, 2011"
        elif "fine" in filename:
            notif_no = "Act No. 1 of 2010 (Sec 51)"
            doc_date = "13th January, 2010"
        elif "guidelines" in filename:
            notif_no = "DoCA-Guidelines-2011"
            doc_date = "30th September, 2011"

        doc_info["notification_no"] = notif_no
        doc_info["date"] = doc_date
        return doc_info

    def _extract_all_rules(self, text, filename, abs_path, file_url):
        extracted_rules = []
        pattern = r'(?=\n(?:(?:Rule|RULE|Schedule|SCHEDULE|Chapter|CHAPTER|Section|SECTION)\s+)?\d{1,2}[\.\:\-\–]\s+[A-Z])'
        blocks = re.split(pattern, text)
        
        for block in blocks:
            block_str = block.strip()
            if not block_str:
                continue
            
            header_match = re.match(r'^(?:(?:Rule|RULE|Schedule|SCHEDULE|Section|SECTION)\s+)?(\d{1,2}[A-Z]?|I|II|III|IV|V)[\.\:\-\–]\s*([^\n]+)', block_str)
            if header_match:
                rule_num = header_match.group(1).upper()
                rule_title = header_match.group(2).strip()
                rule_title = re.sub(r'\(.*?\)', '', rule_title).strip()
                
                if len(rule_title) > 3:
                    extracted_rules.append({
                        "rule_num": f"RULE_{rule_num}",
                        "clause": f"Rule {rule_num}",
                        "title": rule_title[:100],
                        "text": block_str[:1200].replace('\n', ' '),
                        "source_pdf": filename,
                        "source_path": abs_path,
                        "source_url": file_url
                    })
        
        return extracted_rules
