import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class MachineSchemaGenerator:
    def __init__(self, output_json_path, output_pdf_path):
        self.output_json_path = output_json_path
        self.output_pdf_path = output_pdf_path
        self.styles = getSampleStyleSheet()

    def generate_schema(self, consolidated_rules):
        # 1. Export JSON Schema for Module 2 AI consumption
        machine_json = {
            "metadata": {
                "system": "Legal Metrology Compliance Rule Engine",
                "version": "2026.1",
                "authority": "Department of Consumer Affairs (DoCA)",
                "rules_baseline": "Legal Metrology (Packaged Commodities) Rules, 2011 + Gazette Amendments"
            },
            "rules": consolidated_rules
        }

        with open(self.output_json_path, "w", encoding="utf-8") as f:
            json.dump(machine_json, f, indent=2)
        print(f"Generated Machine JSON Rules Engine DB: {self.output_json_path}")

        # 2. Export Machine PDF Specification for Auditing
        doc = SimpleDocTemplate(self.output_pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []

        title_style = ParagraphStyle('MTitle', parent=self.styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#6B46C1'))
        subtitle_style = ParagraphStyle('MSubTitle', parent=self.styles['Heading2'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor('#4A5568'))
        heading_style = ParagraphStyle('MHeading', parent=self.styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#4C51BF'))
        body_style = ParagraphStyle('MBody', parent=self.styles['Normal'], fontSize=9, leading=12, fontName='Courier')

        story.append(Paragraph("MACHINE-READABLE SPECIFICATION: LEGAL METROLOGY COMPLIANCE ENGINE", title_style))
        story.append(Paragraph("Automated Verification Schema & Regex Knowledge Base for Vision/OCR Validation (Module 2)", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6B46C1'), spaceAfter=12, spaceBefore=8))

        story.append(Paragraph("System Machine Schema Overview", heading_style))
        story.append(Paragraph("This PDF defines the exact data model, field keys, and regular expression patterns used by Module 2 Vision AI to validate commodity packaging labels automatically.", ParagraphStyle('Norm', parent=self.styles['Normal'], fontSize=9.5, leading=13)))
        story.append(Spacer(1, 10))

        table_data = [["Rule ID", "Mandatory Field Key", "Status", "Extraction Regex Pattern"]]
        
        for rule_id, rule_info in consolidated_rules.items():
            regex_str = "\nOR\n".join(rule_info.get("regex_patterns", ["N/A (Structural Table)"]))
            table_data.append([
                rule_id,
                rule_info.get("clause", rule_id),
                rule_info.get("status", "ACTIVE"),
                Paragraph(f"<font fontName='Courier' size=7.5>{regex_str}</font>", ParagraphStyle('CourierStyle', parent=self.styles['Normal']))
            ])

        t = Table(table_data, colWidths=[90, 110, 85, 255])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4C51BF')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')])
        ]))
        story.append(t)

        doc.build(story)
        print(f"Generated Machine PDF Specification: {self.output_pdf_path}")
