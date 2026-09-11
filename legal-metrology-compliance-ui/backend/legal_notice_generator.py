"""
Module 3: ReportLab Legal Notice & Seizure Memorandum Generator
Generates court-admissible vector PDFs under Sections 15, 36(1), and 51 of the Legal Metrology Act, 2009.
Designed for DoCA (Department of Consumer Affairs, Ministry of Consumer Affairs, Govt of India) - SIH 26034.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

def generate_show_cause_notice_pdf(
    output_filename: str,
    inspection_number: str,
    product_name: str,
    company_name: str,
    violations: list,
    compliance_score: int
):
    """
    Generates a court-admissible Show-Cause Notice & Seizure Memorandum PDF.
    """
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#991b1b')
    )

    header_style = ParagraphStyle(
        'GoIHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3a8a')
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#1f2937')
    )

    bold_body = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Header
    story.append(Paragraph("GOVERNMENT OF INDIA", header_style))
    story.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION", ParagraphStyle('SubHeader', parent=header_style, fontSize=8, textColor=colors.HexColor('#334155'))))
    story.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION", ParagraphStyle('SubHeader2', parent=header_style, fontSize=9, textColor=colors.HexColor('#0f172a'))))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#991b1b'), spaceAfter=15))

    # Document Title
    notice_no = f"SCN/DoCA/LM/2026/{inspection_number.replace('INS-', '')}"
    today_str = datetime.now().strftime("%d %B %Y")

    story.append(Paragraph("FORMAL SHOW-CAUSE NOTICE & SEIZURE MEMORANDUM", title_style))
    story.append(Paragraph(f"<b>Issued under Sections 15, 36(1) and 51 of the Legal Metrology Act, 2009</b>", ParagraphStyle('Sub', parent=title_style, fontSize=8, textColor=colors.HexColor('#475569'), spaceAfter=10)))
    story.append(Paragraph(f"<b>Notice Ref No:</b> {notice_no} | <b>Date:</b> {today_str}", ParagraphStyle('Ref', parent=body_style, alignment=TA_CENTER, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 12))

    # Offender & Commodity Details Table
    offender_data = [
        [Paragraph("<b>To (Offender / Manufacturer):</b>", bold_body), Paragraph(company_name, body_style)],
        [Paragraph("<b>Inspected Commodity:</b>", bold_body), Paragraph(product_name, body_style)],
        [Paragraph("<b>Inspection Ref No:</b>", bold_body), Paragraph(inspection_number, body_style)],
        [Paragraph("<b>Overall Compliance Score:</b>", bold_body), Paragraph(f"<font color='#991b1b'><b>{compliance_score}% (NON-COMPLIANT)</b></font>", body_style)],
    ]
    t_offender = Table(offender_data, colWidths=[150, 370])
    t_offender.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef2f2')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#fca5a5')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_offender)
    story.append(Spacer(1, 12))

    # Recital
    story.append(Paragraph(
        f"WHEREAS an inspection of the pre-packaged commodity <b>\"{product_name}\"</b> was conducted under Section 15 of the Legal Metrology Act, 2009. Automated optical inspection and rule verification against Module 1 Rules Knowledge Base established the following statutory violations:",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Violations Table
    v_table_data = [
        [Paragraph("<b>#</b>", bold_body), Paragraph("<b>Statutory Citation</b>", bold_body), Paragraph("<b>Nature of Violation</b>", bold_body), Paragraph("<b>Observed Defect</b>", bold_body)]
    ]

    for idx, v in enumerate(violations, 1):
        v_table_data.append([
            Paragraph(str(idx), body_style),
            Paragraph(v.get('statutorySection', 'Section 36(1)'), bold_body),
            Paragraph(v.get('title', 'Declaration Defect'), body_style),
            Paragraph(f"<font color='#991b1b'>{v.get('observedValue', 'Defective')}</font>", body_style)
        ])

    t_violations = Table(v_table_data, colWidths=[25, 125, 235, 135])
    t_violations.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fee2e2')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#991b1b')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#fca5a5')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_violations)
    story.append(Spacer(1, 12))

    # Penalty Matrix Block
    penalty_text = """
    <b>STATUTORY PENALTY MATRIX — SECTION 36(1) LEGAL METROLOGY ACT, 2009:</b><br/>
    • <b>First Offence:</b> Fine extending up to <b>₹25,000</b> (Rupees Twenty-Five Thousand).<br/>
    • <b>Second Offence:</b> Fine extending up to <b>₹50,000</b> (Rupees Fifty Thousand).<br/>
    • <b>Subsequent Offences:</b> Fine up to <b>₹1,00,000</b> or <b>Imprisonment up to 1 Year</b>, or both.
    """
    p_box = Table([[Paragraph(penalty_text, body_style)]], colWidths=[520])
    p_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff5f5')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#dc2626')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(p_box)
    story.append(Spacer(1, 12))

    # Mandatory Directive
    story.append(Paragraph(
        "<b>NOW THEREFORE</b>, take notice that you are hereby directed to <u>SHOW CAUSE</u> in writing within <b>SEVEN (7) DAYS</b> from the date of receipt of this notice why prosecution proceedings under Section 36(1) of the Legal Metrology Act, 2009 should not be initiated against your firm. Failure to respond within 7 days shall result in immediate seizure of non-compliant stock and filing of formal court complaint.",
        ParagraphStyle('Directive', parent=body_style, fontName='Helvetica', textColor=colors.HexColor('#991b1b'))
    ))
    story.append(Spacer(1, 25))

    # Signature Block
    sig_data = [
        [Paragraph("Digital Signature Hash: 0x9D42...F881<br/>Verified by DoCA AI Engine v3.8", ParagraphStyle('SigSub', parent=body_style, fontSize=7, textColor=colors.HexColor('#64748b'))),
         Paragraph("<b>Authorized Enforcement Officer</b><br/>Legal Metrology Department<br/>Government of India", ParagraphStyle('SigRight', parent=body_style, alignment=TA_RIGHT))]
    ]
    t_sig = Table(sig_data, colWidths=[260, 260])
    t_sig.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    story.append(KeepTogether(t_sig))

    doc.build(story)
    return output_filename

if __name__ == "__main__":
    sample_violations = [
        {
            "statutorySection": "Section 36(1) read with Rule 11",
            "title": "Rule 11 Violation: Illegal Unit Symbol 'gms'",
            "observedValue": "180 gms"
        },
        {
            "statutorySection": "Rule 6(1)(e)",
            "title": "Rule 6(1)(e) Violation: Missing mandatory tax phrase 'incl. of all taxes'",
            "observedValue": "MRP ₹199.00"
        }
    ]
    out = generate_show_cause_notice_pdf("Sample_Show_Cause_Notice.pdf", "INS-2026-00147", "Herbal Shampoo 180 ml", "GreenCare Pvt. Ltd.", sample_violations, 74)
    print(f"Generated court-admissible PDF: {out}")
