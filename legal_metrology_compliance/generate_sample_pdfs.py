import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_sample_pdfs(input_dir):
    os.makedirs(input_dir, exist_ok=True)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.navy)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Heading2'], fontSize=12, leading=16, alignment=1, textColor=colors.dimgray)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.darkred)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14)

    # 1. Base Rules 2011 PDF
    pdf1_path = os.path.join(input_dir, "Legal_Metrology_Rules_2011.pdf")
    doc1 = SimpleDocTemplate(pdf1_path, pagesize=letter)
    story1 = []
    
    story1.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION", subtitle_style))
    story1.append(Paragraph("(Department of Consumer Affairs)", subtitle_style))
    story1.append(Spacer(1, 10))
    story1.append(Paragraph("THE LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", title_style))
    story1.append(Paragraph("G.S.R. 202(E) — Notification dated 7th March, 2011", subtitle_style))
    story1.append(HRFlowable(width="100%", thickness=1, color=colors.navy, spaceAfter=15, spaceBefore=10))

    story1.append(Paragraph("Rule 1. Short Title and Commencement", heading_style))
    story1.append(Paragraph("(1) These rules may be called the Legal Metrology (Packaged Commodities) Rules, 2011.<br/>(2) They shall come into force on the 1st day of April, 2011.", body_style))
    story1.append(Spacer(1, 10))

    story1.append(Paragraph("Rule 6. Declarations to be made on every package", heading_style))
    story1.append(Paragraph("Every package shall bear thereon the following mandatory declarations:<br/>"
                            "(a) Name and address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer.<br/>"
                            "(b) Common or generic names of the commodity contained in the package.<br/>"
                            "(c) Net quantity, in terms of standard unit of weight or measure or number.<br/>"
                            "(d) Month and year in which the commodity is manufactured or packed.<br/>"
                            "(e) Maximum Retail Price (MRP) inclusive of all taxes in the format: Maximum Retail Price Rs. XX.XX or MRP Rs. XX.XX (inclusive of all taxes).<br/>"
                            "(f) Name, address, telephone number, and e-mail address of the person or office who can be contacted in case of consumer complaints.", body_style))
    story1.append(Spacer(1, 10))

    story1.append(Paragraph("Rule 7. Minimum Height of Numerals and Letters", heading_style))
    story1.append(Paragraph("The height of any numeral and letter in the declaration shall not be less than the minimum height specified in Table 1 below based on Principal Display Panel (PDP) area:", body_style))
    story1.append(Spacer(1, 5))

    table_data = [
        ["Area of PDP (cm²)", "Min Height (Normal) (mm)", "Min Height (Net Qty/MRP) (mm)"],
        ["Area <= 50", "1.0 mm", "1.5 mm"],
        ["50 < Area <= 100", "1.5 mm", "2.0 mm"],
        ["100 < Area <= 500", "2.5 mm", "4.0 mm"],
        ["Area > 500", "4.0 mm", "6.0 mm"]
    ]
    t1 = Table(table_data, colWidths=[150, 160, 160])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story1.append(t1)
    story1.append(Spacer(1, 10))

    story1.append(Paragraph("Rule 11. Symbols for Units", heading_style))
    story1.append(Paragraph("Units of weight, measure or number shall be expressed in standard legal units standard symbols: 'g' for gram, 'kg' for kilogram, 'ml' for millilitre, 'l' or 'L' for litre, 'm' for metre, 'N' for number. Non-standard symbols such as 'gms', 'gm', 'ML', 'KG.' are prohibited.", body_style))
    
    doc1.build(story1)
    print(f"Generated sample baseline PDF: {pdf1_path}")

    # 2. Amendment 2021 PDF
    pdf2_path = os.path.join(input_dir, "Amendment_2021_USP.pdf")
    doc2 = SimpleDocTemplate(pdf2_path, pagesize=letter)
    story2 = []

    story2.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION", subtitle_style))
    story2.append(Paragraph("NOTIFICATION — G.S.R. 779(E)", title_style))
    story2.append(Paragraph("New Delhi, the 2nd November, 2021", subtitle_style))
    story2.append(HRFlowable(width="100%", thickness=1, color=colors.darkred, spaceAfter=15, spaceBefore=10))

    story2.append(Paragraph("AMENDMENT TO THE LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", heading_style))
    story2.append(Paragraph("In exercise of the powers conferred by section 52 of the Legal Metrology Act, 2009, the Central Government hereby makes the following rules to amend the Legal Metrology (Packaged Commodities) Rules, 2011, namely:", body_style))
    story2.append(Spacer(1, 10))

    story2.append(Paragraph("1. Short Title and Commencement", heading_style))
    story2.append(Paragraph("(1) These rules may be called the Legal Metrology (Packaged Commodities) Amendment Rules, 2021.<br/>(2) They shall come into force on the 1st day of April, 2022.", body_style))
    story2.append(Spacer(1, 10))

    story2.append(Paragraph("2. Amendment of Rule 6", heading_style))
    story2.append(Paragraph("In the Legal Metrology (Packaged Commodities) Rules, 2011, in Rule 6, in sub-rule (1):<br/><br/>"
                            "<b>(i) Clause (e) shall be substituted by the following:</b><br/>"
                            "'(e) Maximum Retail Price (MRP) inclusive of all taxes in Indian Rupees Rs. XX.XX or ₹ XX.XX (inclusive of all taxes).'<br/><br/>"
                            "<b>(ii) After Clause (e), the following new Clause (ea) shall be inserted, namely:</b><br/>"
                            "'(ea) Unit Sale Price (USP) declared as: <br/>"
                            "  - ₹ per gram for commodities where net quantity is greater than 1 gram but less than 1 kg;<br/>"
                            "  - ₹ per kilogram for commodities where net quantity is 1 kg or more;<br/>"
                            "  - ₹ per millilitre for liquid commodities where net quantity is greater than 1 ml but less than 1 litre;<br/>"
                            "  - ₹ per litre for liquid commodities where net quantity is 1 litre or more.'<br/><br/>"
                            "<b>(iii) After Clause (f), the following Clause (g) shall be inserted for imported goods:</b><br/>"
                            "'(g) Country of Origin of the commodity shall be explicitly declared on the principal display panel for all imported packages.'", body_style))
    
    doc2.build(story2)
    print(f"Generated sample amendment PDF: {pdf2_path}")

if __name__ == "__main__":
    input_directory = os.path.join(os.path.dirname(__file__), "input_pdfs")
    create_sample_pdfs(input_directory)
