import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def wrap_filename(filename, max_chars=25):
    """Inserts explicit <br/> tags at word boundaries or punctuation to force clean wrapping inside PDF table cells."""
    if len(filename) <= max_chars:
        return filename
    tokens = re.split(r'([_\-\.\s])', filename)
    lines = []
    current_line = ""
    for token in tokens:
        if len(current_line) + len(token) > max_chars:
            lines.append(current_line)
            current_line = token
        else:
            current_line += token
    if current_line:
        lines.append(current_line)
    return "<br/>".join(lines)

class HumanPDFGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        
        self.title_style = ParagraphStyle('DocTitle', parent=self.styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor('#002B49'))
        self.subtitle_style = ParagraphStyle('DocSubTitle', parent=self.styles['Heading2'], fontSize=11, leading=15, alignment=1, textColor=colors.HexColor('#4A5568'))
        self.section_heading = ParagraphStyle('SecHeading', parent=self.styles['Heading2'], fontSize=13, leading=17, textColor=colors.HexColor('#1A365D'), spaceBefore=14, spaceAfter=6)
        self.body_style = ParagraphStyle('BodyTextCustom', parent=self.styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#2D3748'))
        
        # Cell Wrapping Styles
        self.cell_header_style = ParagraphStyle('CellHeader', parent=self.styles['Normal'], fontSize=9, leading=11, textColor=colors.whitesmoke, fontName='Helvetica-Bold')
        self.cell_text_style = ParagraphStyle('CellText', parent=self.styles['Normal'], fontSize=8, leading=10.5, textColor=colors.HexColor('#1A202C'))
        self.cell_code_style = ParagraphStyle('CellCode', parent=self.styles['Normal'], fontSize=8, leading=10.5, fontName='Courier', textColor=colors.HexColor('#2D3748'))
        
        # Category Badges
        self.badge_active = ParagraphStyle('BadgeActive', parent=self.styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#15803D'), fontName='Helvetica-Bold')
        self.badge_amended = ParagraphStyle('BadgeAmended', parent=self.styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#B45309'), fontName='Helvetica-Bold')
        self.badge_universal = ParagraphStyle('BadgeUniversal', parent=self.styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#1D4ED8'), fontName='Helvetica-Bold')
        self.badge_category = ParagraphStyle('BadgeCategory', parent=self.styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#6B21A8'), fontName='Helvetica-Bold')

    def generate_pdf(self, consolidated_rules, doc_sources):
        # Total printable width = 612 - 72 = 540 points
        doc = SimpleDocTemplate(self.output_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []

        # --- COVER HEADER ---
        story.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION", self.subtitle_style))
        story.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION", self.subtitle_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("CONSOLIDATED CODEBOOK: LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", self.title_style))
        story.append(Paragraph("Synthesized Legal Reference Guide with Hyperlinked Lineage Timelines & Source PDFs (Updated 2026)", self.subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#002B49'), spaceAfter=12, spaceBefore=8))

        # --- EXECUTIVE SUMMARY ---
        story.append(Paragraph("Executive Summary & Legal Scope", self.section_heading))
        summary_text = (
            "This master consolidation compiles the <b>Legal Metrology (Packaged Commodities) Rules, 2011</b> "
            "along with all subsequent Gazette Amendments. Each rule features a <b>Chronological Amendment Lineage Timeline</b> "
            "with clickable direct links to every original Gazette PDF document, full commodity category classification, "
            "and universal rule identification."
        )
        story.append(Paragraph(summary_text, self.body_style))
        story.append(Spacer(1, 10))

        # --- SOURCE DOCUMENTS TABLE ---
        story.append(Paragraph("Synthesized Source Gazette Notifications", self.section_heading))
        
        doc_table_data = [[
            Paragraph("Filename / Source", self.cell_header_style),
            Paragraph("Notification No.", self.cell_header_style),
            Paragraph("Document Date", self.cell_header_style),
            Paragraph("Type / Source Link", self.cell_header_style)
        ]]
        
        for doc_info in doc_sources:
            wrapped_name = wrap_filename(doc_info["filename"], max_chars=26)
            wrapped_notif = wrap_filename(doc_info["notification_no"], max_chars=16)
            
            link_html = f'<a href="{doc_info["file_url"]}"><font color="#2563EB"><u>View Source PDF</u></font></a>'
            
            doc_table_data.append([
                Paragraph(wrapped_name, self.cell_text_style),
                Paragraph(wrapped_notif, self.cell_text_style),
                Paragraph(doc_info["date"], self.cell_text_style),
                Paragraph(f"{'Gazette Amendment' if doc_info['is_amendment'] else 'Base Gazette Rule'}<br/>{link_html}", self.cell_text_style)
            ])
            
        t_sources = Table(doc_table_data, colWidths=[200, 105, 105, 130])
        t_sources.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')])
        ]))
        story.append(t_sources)
        story.append(Spacer(1, 14))

        # --- CONSOLIDATED RULES TABLE WITH TIMELINES & PDF LINKS ---
        story.append(Paragraph("Consolidated Master Rules with Hyperlinked Amendment History", self.section_heading))
        
        rules_table_data = [[
            Paragraph("Clause ID", self.cell_header_style),
            Paragraph("Rule Requirement & Hyperlinked Amendment History", self.cell_header_style),
            Paragraph("Category Scope", self.cell_header_style),
            Paragraph("Status & Date", self.cell_header_style)
        ]]
        
        for rule_id, rule_data in consolidated_rules.items():
            status_text = rule_data["status"]
            status_paragraph = Paragraph(f"<b>[{status_text}]</b><br/><font size=7.5 color='#4A5568'>Effective: {rule_data.get('effective_date', '2011-04-01')}</font>", 
                                         self.badge_amended if "AMENDED" in status_text or "INSERTED" in status_text else self.badge_active)
            
            clause_str = rule_data.get('clause', rule_id)
            title_str = rule_data.get('title', rule_id)
            text_str = rule_data.get('text', '')
            
            source_pdf_name = rule_data.get('source_pdf', 'Original Gazette')
            source_url = rule_data.get('source_url', '#')
            
            source_link_html = f'<a href="{source_url}"><font color="#2563EB"><b>📄 Primary Source: {source_pdf_name}</b></font></a>'
            
            rule_detail = f"<b>{clause_str} - {title_str}</b><br/>{text_str}<br/>{source_link_html}"
            
            # Format Hyperlinked Chronological History Timeline (Capped to 4 key entries per cell to prevent page overflow)
            history_items = rule_data.get("amendment_history", [])
            if history_items:
                rule_detail += "<br/><br/><font size=7.5 color='#1A365D'><b>📜 Statutory History Lineage:</b></font><br/>"
                display_items = history_items[:4]
                for item in display_items:
                    if isinstance(item, dict):
                        event = item.get("event", "UPDATE")
                        pdf_name = item.get("pdf_name", "Source Document")
                        pdf_url = item.get("pdf_url", "#")
                        notif = item.get("notification_no", "")
                        
                        wrapped_pdf = wrap_filename(pdf_name, max_chars=30)
                        link_tag = f'<a href="{pdf_url}"><font color="#2563EB"><u>{wrapped_pdf}</u></font></a>'
                        
                        rule_detail += f"<font size=7 color='#2D3748'>• <b>[{event}]</b> via {link_tag} ({notif})</font><br/>"
                    else:
                        rule_detail += f"<font size=7 color='#718096'>• {item}</font><br/>"
                
                if len(history_items) > 4:
                    rule_detail += f"<font size=7 color='#718096'><i>...and {len(history_items) - 4} more gazette amendments (see JSON DB for full list)</i></font><br/>"

            is_univ = rule_data.get('is_universal', True)
            cat_name = rule_data.get('category', 'UNIVERSAL (ALL PACKAGED COMMODITIES)')
            
            cat_badge = Paragraph(f"<b>[UNIVERSAL RULE]</b><br/><font size=7 color='#4B5563'>Applicable to all commodities</font>", self.badge_universal) if is_univ else Paragraph(f"<b>[{cat_name}]</b>", self.badge_category)
            
            rules_table_data.append([
                Paragraph(rule_id, self.cell_code_style),
                Paragraph(rule_detail, self.cell_text_style),
                cat_badge,
                status_paragraph
            ])

        t_rules = Table(rules_table_data, colWidths=[80, 255, 110, 95])
        t_rules.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#EDF2F7')])
        ]))
        story.append(t_rules)
        story.append(Spacer(1, 14))

        # --- FONT SIZE TABLE ---
        story.append(Paragraph("Rule 7: Prescribed Minimum Font Height Matrix", self.section_heading))
        font_table_data = [[
            Paragraph("Area of PDP (cm²)", self.cell_header_style),
            Paragraph("Min Height (Normal Numerals)", self.cell_header_style),
            Paragraph("Min Height (Net Qty / MRP)", self.cell_header_style)
        ]]
        for row in consolidated_rules["RULE_7_FONT"]["thresholds"]:
            font_table_data.append([
                Paragraph(row["pdp_area_sq_cm"], self.cell_text_style),
                Paragraph(f"{row['min_normal_mm']} mm", self.cell_text_style),
                Paragraph(f"{row['min_net_qty_mrp_mm']} mm", self.cell_text_style)
            ])
            
        t_font = Table(font_table_data, colWidths=[180, 180, 180])
        t_font.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C5282')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(t_font)
        story.append(Spacer(1, 16))

        # --- GLOSSARY & LEGEND SECTION (EXPLAINING ALL LEGAL STATUS TERMS) ---
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#002B49'), spaceAfter=10, spaceBefore=10))
        story.append(Paragraph("Glossary & Legend: Legal Status Terms Explained", self.section_heading))
        
        glossary_text = (
            "<b>1. ACTIVE (BASELINE):</b> Represents a legal rule originating from the baseline <i>Legal Metrology (Packaged Commodities) Rules, 2011</i>. "
            "It remains in full legal effect unless explicitly amended or substituted.<br/><br/>"
            "<b>2. AMENDED / SUBSTITUTED:</b> Indicates that the central government published a Gazette Notification replacing the original clause text with updated statutory requirements. "
            "The substituted text in this codebook represents the legally binding rule.<br/><br/>"
            "<b>3. INSERTED / ADDED:</b> Refers to a brand-new statutory mandate introduced via amendment after 2011 (e.g., Unit Sale Price in 2021, Country of Origin for imports).<br/><br/>"
            "<b>4. OMITTED / REPEALED:</b> Signifies that a specific clause or sub-rule was deleted by gazette notification. Enforcement officials should no longer treat omitted rules as grounds for non-compliance.<br/><br/>"
            "<b>5. UNIVERSAL RULE:</b> A mandatory legal requirement applicable to <b>every packaged commodity</b> sold, distributed, or imported in India, regardless of product category.<br/><br/>"
            "<b>6. CATEGORY-SPECIFIC RULE:</b> Special legal provisions tailored for specific product classes (e.g., Garments, Edible Oils, E-commerce Platforms, Medical Devices, Pan Masala)."
        )
        story.append(Paragraph(glossary_text, ParagraphStyle('GlossText', parent=self.styles['Normal'], fontSize=8.5, leading=12.5, textColor=colors.HexColor('#1A202C'))))

        doc.build(story)
        print(f"Generated Enhanced Human PDF with Capped Row Height & PDF Links: {self.output_path}")
