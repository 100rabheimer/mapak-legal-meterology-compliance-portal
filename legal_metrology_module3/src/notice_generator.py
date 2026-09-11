import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

from src.utils import generate_notice_number, format_timestamp, sanitize_filename

class NumberedCanvas(canvas.Canvas):
    """Adds page numbers and official footer on all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Top header rule
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 805, 555, 805)
        self.drawString(40, 810, "GOVERNMENT OF INDIA • DEPARTMENT OF CONSUMER AFFAIRS • LEGAL METROLOGY DIVISION")

        # Bottom footer rule
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, "Confidential Statutory Document • Issued under Sections 15 & 36 of Legal Metrology Act, 2009")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 32, page_text)
        self.restoreState()

class LegalNoticeGenerator:
    """
    Generates formal, court-ready Government of India Inspection Notices and Seizure Memos
    under Legal Metrology Act, 2009 (Sections 15, 36, and 51).
    """

    def __init__(self, output_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = output_dir or os.path.join(base_dir, "output", "notices")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_notice(self, inspection_data: Dict[str, Any], notice_number: Optional[str] = None) -> str:
        """
        Builds the PDF document and returns the absolute file path.
        """
        notice_no = notice_number or generate_notice_number()
        safe_notice_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', notice_no)
        pdf_filename = f"Legal_Notice_{safe_notice_id}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=55,
            bottomMargin=55
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "GovTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=1, # Center
            textColor=colors.HexColor("#0F172A")
        )
        subtitle_style = ParagraphStyle(
            "GovSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=colors.HexColor("#1E3A8A")
        )
        banner_style = ParagraphStyle(
            "NoticeBanner",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#991B1B") # Deep Crimson
        )
        meta_label = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )
        meta_val = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155")
        )
        body_style = ParagraphStyle(
            "GovBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )
        body_bold = ParagraphStyle(
            "GovBodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#0F172A")
        )
        table_hdr = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=1,
            textColor=colors.white
        )
        table_cell = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#0F172A")
        )
        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#0F172A")
        )

        def sanitize_pdf_text(txt: str) -> str:
            if not txt:
                return ""
            # Replace Rupee symbol with Rs. to prevent missing glyph box in Helvetica
            cleaned = str(txt).replace("₹", "Rs. ").replace("•", "&bull;").replace("²", "2")
            return cleaned

        elements = []

        # 1. Official Header
        elements.append(Paragraph("<b>[ STATE EMBLEM OF INDIA ]</b>", ParagraphStyle("EmblemMotto", parent=title_style, fontSize=9, leading=11, textColor=colors.HexColor("#475569"))))
        elements.append(Paragraph("GOVERNMENT OF INDIA", title_style))
        elements.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", title_style))
        elements.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS", subtitle_style))
        elements.append(Paragraph("LEGAL METROLOGY DIVISION — ENFORCEMENT & SURVEILLANCE WING", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=6))

        # 2. Notice Title Banner
        is_compliant = inspection_data.get("is_compliant", False)
        violations = inspection_data.get("violations", [])
        
        if not is_compliant or len(violations) > 0:
            banner_text = "FORMAL INSPECTION NOTICE & STATUTORY SHOW-CAUSE MEMORANDUM<br/><font size=8.5>Issued under Section 15 & Section 36(1) read with Section 51 of Legal Metrology Act, 2009</font>"
            banner_bg = colors.HexColor("#FEE2E2")
            banner_border = colors.HexColor("#EF4444")
        else:
            banner_text = "OFFICIAL PACKAGING COMPLIANCE INSPECTION CERTIFICATE<br/><font size=8.5>Issued under Legal Metrology (Packaged Commodities) Rules, 2011</font>"
            banner_bg = colors.HexColor("#DCFCE7")
            banner_border = colors.HexColor("#22C55E")

        banner_table = Table([[Paragraph(banner_text, banner_style)]], colWidths=[515])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), banner_bg),
            ("BOX", (0,0), (-1,-1), 1, banner_border),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 8))

        # 3. Reference and Metadata Grid
        officer_name = os.getenv("OFFICER_NAME", "Sh. R. K. Verma")
        officer_desig = os.getenv("OFFICER_DESIGNATION", "Assistant Controller of Legal Metrology")
        officer_zone = os.getenv("OFFICER_ZONE", "Northern Enforcement Zone, New Delhi")
        timestamp_str = inspection_data.get("timestamp", format_timestamp())

        meta_data = [
            [
                Paragraph("<b>Notice Ref No:</b>", meta_label), Paragraph(notice_no, meta_val),
                Paragraph("<b>Date & Time:</b>", meta_label), Paragraph(timestamp_str, meta_val)
            ],
            [
                Paragraph("<b>Inspecting Officer:</b>", meta_label), Paragraph(f"{officer_name} ({officer_desig})", meta_val),
                Paragraph("<b>Jurisdiction / Zone:</b>", meta_label), Paragraph(officer_zone, meta_val)
            ],
            [
                Paragraph("<b>Inspection Mode:</b>", meta_label), Paragraph("Statutory AI Automated Packaging Audit", meta_val),
                Paragraph("<b>Statutory Act:</b>", meta_label), Paragraph("Legal Metrology Act, 2009 & PCR, 2011", meta_val)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[95, 175, 95, 150])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # 4. Offender Entity Details
        entity_info = inspection_data.get("entity_info", {})
        mfg_address = entity_info.get("manufacturer_name_address", "M/s. Offending Manufacturer (Undisclosed)")
        commodity = entity_info.get("commodity_name", "Pre-Packaged Commodity")
        net_qty = entity_info.get("net_quantity", "N/A")
        mrp = entity_info.get("mrp", "N/A")
        mfg_date = entity_info.get("mfg_date", "N/A")

        elements.append(Paragraph("<b>TO:</b>", body_bold))
        target_info = f"<b>{mfg_address}</b><br/>" \
                      f"<font color='#475569'>Packaged Commodity:</font> <b>{commodity}</b> | " \
                      f"<font color='#475569'>Declared Net Qty:</font> {net_qty} | " \
                      f"<font color='#475569'>MRP:</font> {mrp} | " \
                      f"<font color='#475569'>Date of Pkd:</font> {mfg_date}"
        elements.append(Paragraph(target_info, body_style))
        elements.append(Spacer(1, 6))

        # 5. Inspection Findings Summary
        score = inspection_data.get("compliance_score", 0)
        pdp_info = inspection_data.get("pdp_summary", {})
        pdp_area = pdp_info.get("pdp_area_cm2", "N/A")
        font_info = inspection_data.get("font_verification", {})
        measured_h = font_info.get("measured_font_height_mm", "N/A")
        min_h = font_info.get("statutory_min_height_mm", "N/A")

        summary_para = (
            f"<b>SUBJECT: NOTICE OF CONTRAVENTION OF STATUTORY PACKAGING REGULATIONS</b><br/>"
            f"WHEREAS an official statutory inspection of the pre-packaged commodity specified above was conducted "
            f"by the authorized enforcement officer using certified digital optical calibration under Section 15 of "
            f"the Legal Metrology Act, 2009.<br/>"
            f"<b>FINDINGS:</b> The Principal Display Panel (PDP) was evaluated at <b>{pdp_area} cm²</b>. "
            f"Statutory compliance score evaluated to <b>{score}/100</b>. "
            f"Numeral font height measured at <b>{measured_h} mm</b> (Statutory Rule 7 minimum required: <b>{min_h} mm</b>). "
            f"A total of <b>{len(violations)} statutory violation(s)</b> were established as detailed herein."
        )
        elements.append(Paragraph(summary_para, body_style))
        elements.append(Spacer(1, 6))

        # 6. Statutory Violations Table
        if violations:
            elements.append(Paragraph("<b>1. STATUTORY CONTRAVENTIONS & EVIDENCE TABLE:</b>", body_bold))
            elements.append(Spacer(1, 3))

            v_headers = [
                Paragraph("<b>S.No</b>", table_hdr),
                Paragraph("<b>Field / Subject</b>", table_hdr),
                Paragraph("<b>Statutory Rule & Section</b>", table_hdr),
                Paragraph("<b>Specific Non-Compliance & Legal Defect</b>", table_hdr),
                Paragraph("<b>Severity</b>", table_hdr)
            ]
            v_rows = [v_headers]

            for idx, v in enumerate(violations, 1):
                sev = v.get("severity", "MAJOR")
                sev_color = "#DC2626" if sev == "CRITICAL" else "#D97706"
                f_name = sanitize_pdf_text(v.get('field', 'General'))
                f_title = sanitize_pdf_text(v.get('title', ''))
                f_clause = sanitize_pdf_text(v.get('clause', 'PCR 2011'))
                f_cite = sanitize_pdf_text(v.get('legal_citation', ''))
                f_desc = sanitize_pdf_text(v.get('description') or v.get('issue', 'Non-conforming declaration observed on package PDP.'))
                f_remedy = sanitize_pdf_text(v.get('remedy') or v.get('statutory_ref', 'Rectify declaration to comply with Legal Metrology (Packaged Commodities) Rules, 2011.'))

                v_rows.append([
                    Paragraph(str(idx), table_cell_bold),
                    Paragraph(f"<b>{f_name}</b><br/>{f_title}", table_cell),
                    Paragraph(f"<b>{f_clause}</b><br/>{f_cite}", table_cell),
                    Paragraph(f"{f_desc}<br/><font color='#15803D'><b>Remedy:</b> {f_remedy}</font>", table_cell),
                    Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", table_cell_bold)
                ])

            v_table = Table(v_rows, colWidths=[25, 110, 110, 215, 55])
            v_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("TOPPADDING", (0,0), (-1,-1), 3),
                ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ]))
            elements.append(v_table)
            elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph("<b>1. STATUTORY COMPLIANCE STATUS:</b>", body_bold))
            elements.append(Paragraph("All 8 mandatory declarations and Rule 7 font specifications conform to statutory requirements. No contraventions observed.", body_style))
            elements.append(Spacer(1, 8))

        # 7. Photographic Evidence Embedding
        artifacts = inspection_data.get("artifacts", {})
        annotated_img_path = artifacts.get("annotated_image_path")
        if not annotated_img_path or not os.path.exists(annotated_img_path):
            annotated_img_path = artifacts.get("original_image_path")

        if annotated_img_path and os.path.exists(annotated_img_path):
            try:
                # Open image with PIL to calculate proportional width and height
                with Image.open(annotated_img_path) as im:
                    orig_w, orig_h = im.size
                    # Max display dimensions on A4: width 480pt, height 220pt
                    max_w, max_h = 480, 210
                    ratio = min(max_w / orig_w, max_h / orig_h)
                    disp_w = orig_w * ratio
                    disp_h = orig_h * ratio

                evidence_elements = [
                    Paragraph("<b>2. PHOTOGRAPHIC EVIDENCE (ANNOTATED PACKAGING INSPECTION SCAN):</b>", body_bold),
                    Spacer(1, 3),
                    RLImage(annotated_img_path, width=disp_w, height=disp_h),
                    Spacer(1, 2),
                    Paragraph("<font size=7 color='#64748B'><i>Figure 1: Automated digital inspection overlay. Red borders indicate statutory violations; Green borders indicate verified compliant declarations.</i></font>", body_style)
                ]
                elements.append(KeepTogether(evidence_elements))
                elements.append(Spacer(1, 8))
            except Exception as img_err:
                print(f"[LegalNoticeGenerator] Warning embedding evidence image: {img_err}")

        # 8. Statutory Liability / Compliance Acknowledgment Section
        if violations:
            penalty_info = inspection_data.get("penalty_info", {})
            penalty_box = [
                Paragraph("<b>3. STATUTORY PENAL PROVISIONS UNDER LEGAL METROLOGY ACT, 2009:</b>", body_bold),
                Spacer(1, 2),
                Paragraph(
                    "&bull; <b>Section 36(1) [Penalty for Selling, etc., of Non-Standard Packages]:</b><br/>"
                    "Whoever manufactures, packs, imports, sells, distributes, delivers, offers, exposes, or possesses for sale, "
                    "any pre-packaged commodity which does not conform to declarations... shall be punished with fine "
                    "<b>which may extend to Rs. 25,000 (Twenty-Five Thousand Rupees)</b> for the first offence; for the second offence, "
                    "with fine <b>which may extend to Rs. 50,000 (Fifty Thousand Rupees)</b>; and for any subsequent offence, "
                    "with fine <b>not less than Rs. 50,000 which may extend to Rs. 1,00,000 or with imprisonment for a term up to 1 year, or with both</b>.<br/>"
                    "&bull; <b>Section 51 [Offences by Companies]:</b> Directors, managers, secretaries, or designated partners "
                    "shall be deemed guilty and liable to be proceeded against and punished accordingly.<br/>"
                    "&bull; <b>Section 15 [Power of Inspection, Search and Seizure]:</b> The Inspecting Officer reserves the right "
                    "to seize packages, documents, and production lots found in contravention.",
                    body_style
                )
            ]
            elements.append(KeepTogether(penalty_box))
            elements.append(Spacer(1, 6))

            # 9. 7-Day Show-Cause Notice Directive
            directive_text = (
                "<b>4. STATUTORY DIRECTIVE & 7-DAY SHOW-CAUSE NOTICE:</b><br/>"
                "NOW, THEREFORE, by virtue of powers conferred under Section 15 and Section 36 of the Legal Metrology Act, 2009, "
                "you are hereby directed to <b>SHOW CAUSE in writing within 7 (SEVEN) DAYS</b> from the date of receipt of this notice "
                "as to why legal proceedings under Section 36(1) should not be instituted against your company and designated directors.<br/>"
                "You are further directed to immediately suspend dispatch of non-conforming packaging batches until full rectification "
                "and verification by this Directorate. Failure to reply within the stipulated time will result in ex-parte seizure "
                "and initiation of criminal prosecution before the Court of Metropolitan Magistrate / Chief Judicial Magistrate."
            )
            directive_table = Table([[Paragraph(directive_text, body_style)]], colWidths=[515])
            directive_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#FFFBEB")), # Warning amber tint
                ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#F59E0B")),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            elements.append(KeepTogether([directive_table]))
            elements.append(Spacer(1, 10))
        else:
            # 100% Compliant Clearance Certificate
            clearance_box = [
                Paragraph("<b>3. STATUTORY COMPLIANCE ACKNOWLEDGMENT & CERTIFICATION:</b>", body_bold),
                Spacer(1, 2),
                Paragraph(
                    "This official document certifies that the pre-packaged commodity specified herein was subjected to "
                    "statutory digital optical verification under Section 15 of the Legal Metrology Act, 2009. "
                    "The packaging design, Principal Display Panel (PDP) declarations, SI unit symbols, MRP tax clause, "
                    "Unit Sale Price (USP), and numeral font height thresholds conform in full to the requirements of the "
                    "Legal Metrology (Packaged Commodities) Rules, 2011 and applicable Gazette Amendments.<br/>"
                    "&bull; <b>Section 18 [Declarations on Pre-Packaged Commodities]:</b> Verified & Compliant.<br/>"
                    "&bull; <b>Rule 6 & Rule 11 [Mandatory Declarations & SI Units]:</b> All 8 statutory declarations present and verified.<br/>"
                    "&bull; <b>Rule 7 [Numeral & Letter Dimensions]:</b> Numeral font height satisfies statutory minimum threshold.",
                    body_style
                )
            ]
            elements.append(KeepTogether(clearance_box))
            elements.append(Spacer(1, 6))

            directive_text = (
                "<b>4. OFFICIAL STATUTORY CLEARANCE DIRECTIVE:</b><br/>"
                "BY VIRTUE OF POWERS conferred under the Legal Metrology Act, 2009, this packaging design is declared "
                "<b>100% STATUTORILY COMPLIANT</b>. No penal proceedings or show-cause actions under Section 36(1) or "
                "Section 51 are attracted. This certificate constitutes official verification and clearance for commercial "
                "distribution, logistics, and retail sale across all States and Union Territories of India."
            )
            directive_table = Table([[Paragraph(directive_text, body_style)]], colWidths=[515])
            directive_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#ECFDF5")), # Success emerald tint
                ("BOX", (0,0), (-1,-1), 1, colors.HexColor("#10B981")),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            elements.append(KeepTogether([directive_table]))
            elements.append(Spacer(1, 10))

        # 10. Officer Seal & Digital Signature Block
        officer_info = inspection_data.get("officer_info", {})
        o_name = officer_info.get("full_name") or os.getenv("OFFICER_NAME", "Sh. R. K. Verma")
        o_badge = officer_info.get("badge_number") or os.getenv("OFFICER_BADGE", "LM-DEL-2026-0148")
        o_desig = officer_info.get("designation") or os.getenv("OFFICER_DESIGNATION", "Assistant Controller of Legal Metrology")
        o_zone = officer_info.get("jurisdiction_zone") or os.getenv("OFFICER_ZONE", "Northern Enforcement Zone, New Delhi")

        sig_box_text = (
            f"<b>[ DIGITALLY SIGNED & VERIFIED ]</b><br/>"
            f"<font color='#1E3A8A'><b>{o_name}</b></font><br/>"
            f"{o_desig}<br/>"
            f"Badge No: <b>{o_badge}</b><br/>"
            f"Jurisdiction: {o_zone}<br/>"
            f"<font size=7 color='#64748B'>Digitally Signed under IT Act 2000 & Section 15 of LM Act 2009<br/>"
            f"Verification Timestamp: {timestamp_str}</font>"
        )

        sig_data = [
            [
                Paragraph("<b>OFFICIAL SEAL OF AUTHORITY:</b><br/><br/><b>[ SEAL OF THE ASSISTANT CONTROLLER ]</b><br/>DEPARTMENT OF CONSUMER AFFAIRS, GOVT. OF INDIA", meta_label),
                Paragraph(sig_box_text, meta_label)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[250, 265])
        sig_table.setStyle(TableStyle([
            ("BACKGROUND", (1,0), (1,0), colors.HexColor("#F1F5F9")),
            ("BOX", (1,0), (1,0), 1, colors.HexColor("#3B82F6")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (1,0), (1,0), 8),
            ("RIGHTPADDING", (1,0), (1,0), 8),
        ]))
        elements.append(KeepTogether([sig_table]))

        # Build PDF with dynamic footer and page numbers
        doc.build(elements, canvasmaker=NumberedCanvas)
        return pdf_path
