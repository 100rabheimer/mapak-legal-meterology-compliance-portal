import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_synthetic_package(filename, title, category, fields, width=800, height=1000):
    """
    Creates a realistic synthetic packaging label image with background, borders, and text fields.
    """
    # Create white canvas with a subtle border
    img = Image.new("RGB", (width, height), color=(250, 248, 245))
    draw = ImageDraw.Draw(img)
    
    # Outer box (Package PDP border)
    margin = 30
    draw.rectangle([margin, margin, width - margin, height - margin], outline=(40, 40, 40), width=4)
    
    # Header Banner
    draw.rectangle([margin + 5, margin + 5, width - margin - 5, margin + 90], fill=(24, 76, 120))
    
    # Fonts (Fall back to default if truetype unavailable)
    try:
        font_header = ImageFont.truetype("arial.ttf", 36)
        font_sub = ImageFont.truetype("arial.ttf", 22)
        font_body = ImageFont.truetype("arial.ttf", 26)
        font_bold = ImageFont.truetype("arialbd.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_header = font_sub = font_body = font_bold = font_small = ImageFont.load_default()
        
    # Draw Brand Title
    draw.text((width // 2, margin + 45), title, fill=(255, 255, 255), font=font_header, anchor="mm")
    
    # Draw Category Badge
    draw.rectangle([width - margin - 220, margin + 105, width - margin - 10, margin + 140], fill=(220, 230, 242))
    draw.text((width - margin - 115, margin + 122), category.upper(), fill=(24, 76, 120), font=font_sub, anchor="mm")
    
    y = margin + 160
    
    # Render all fields
    for label, val in fields.items():
        if label.startswith("SECTION_"):
            # Section header
            draw.line([(margin + 10, y + 10), (width - margin - 10, y + 10)], fill=(200, 200, 200), width=2)
            y += 25
            continue
            
        line_str = f"{label}: {val}"
        
        # Highlight important fields like Net Qty and MRP
        if "NET QTY" in label.upper() or "MRP" in label.upper():
            draw.rectangle([margin + 15, y - 5, width - margin - 15, y + 35], outline=(100, 100, 100), width=1)
            draw.text((margin + 25, y), line_str, fill=(10, 10, 10), font=font_bold)
            y += 45
        else:
            draw.text((margin + 25, y), line_str, fill=(30, 30, 30), font=font_body)
            y += 38

    # Draw Barcode mock block at bottom
    bc_x1, bc_y1 = margin + 40, height - margin - 120
    bc_x2, bc_y2 = margin + 280, height - margin - 30
    draw.rectangle([bc_x1, bc_y1, bc_x2, bc_y2], outline=(0, 0, 0), width=2)
    # Draw barcode vertical stripes
    for bar_x in range(bc_x1 + 10, bc_x2 - 10, 8):
        w_bar = 3 if (bar_x % 3 == 0) else 5
        draw.line([(bar_x, bc_y1 + 10), (bar_x, bc_y2 - 25)], fill=(0, 0, 0), width=w_bar)
    draw.text(((bc_x1 + bc_x2) // 2, bc_y2 - 12), "8 901234 567890", fill=(0, 0, 0), font=font_small, anchor="mm")

    # Add reference scale marker (for font calibrator verification)
    scale_x1, scale_y1 = width - margin - 200, height - margin - 60
    draw.line([(scale_x1, scale_y1), (scale_x1 + 150, scale_y1)], fill=(255, 0, 0), width=3)
    draw.line([(scale_x1, scale_y1 - 8), (scale_x1, scale_y1 + 8)], fill=(255, 0, 0), width=2)
    draw.line([(scale_x1 + 150, scale_y1 - 8), (scale_x1 + 150, scale_y1 + 8)], fill=(255, 0, 0), width=2)
    draw.text((scale_x1 + 75, scale_y1 - 15), "50 mm (Scale)", fill=(255, 0, 0), font=font_small, anchor="mm")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)
    print(f"[GEN] Created synthetic package image: {filename}")

def generate_all_samples():
    output_dir = "output/test_packages"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Compliant Package Sample
    compliant_fields = {
        "Name & Address of Manufacturer": "Apex Foods Ltd., Plot 45, Okhla Ind Area, New Delhi - 110020",
        "Generic Commodity Name": "Premium Refined Sunflower Oil",
        "NET QTY": "1 L (910 g)",
        "MRP": "Rs. 185.00 (Incl. of all taxes)",
        "Unit Sale Price (USP)": "Rs. 0.185 / ml",
        "Date of Manufacture": "08/2026",
        "Country of Origin": "India",
        "Consumer Care": "Care Manager, Apex Foods, Call: 1800-11-9999, Email: care@apexfoods.in",
        "SECTION_1": "",
        "Category Specific (Edible Oil)": "Blend of 80% Sunflower Oil & 20% Rice Bran Oil"
    }
    create_synthetic_package(
        os.path.join(output_dir, "sample_compliant_package.jpg"),
        "APEX GOLD SUNFLOWER OIL",
        "EDIBLE OILS",
        compliant_fields
    )

    # 2. Non-Compliant Package Sample (Illegal unit 'GMS', Missing USP, Missing Taxes phrase)
    non_compliant_fields = {
        "Manufacturer": "QuickSnacks Pvt Ltd, Sector 62, Noida",
        "Commodity": "Roasted Almonds",
        "NET QTY": "500 GMS",  # ILLEGAL UNIT: 'GMS' instead of 'g'
        "MRP": "Rs 350",       # MISSING 'Incl. of all taxes'
        # MISSING Unit Sale Price (USP)
        "Date of Pkd": "07/2026",
        "Country of Origin": "India",
        "Customer Care": "Email: support@quicksnacks.com" # Missing postal address & phone
    }
    create_synthetic_package(
        os.path.join(output_dir, "sample_non_compliant_package.jpg"),
        "CRUNCHY ALMONDS",
        "GENERAL",
        non_compliant_fields
    )

    # 3. Garment Sample (Category specific rules: Size, Fiber Composition)
    garment_fields = {
        "Brand": "Urban Stitcher Apparel",
        "Manufacturer": "Urban Stitcher Co., Ludhiana, Punjab - 141001",
        "Generic Name": "Men's Cotton Polo T-Shirt",
        "Size": "L (102 cm Chest)",
        "Fiber Composition": "100% Combed Organic Cotton",
        "NET QTY": "1 N (1 Piece)",
        "MRP": "Rs. 999.00 (Incl. of all taxes)",
        "Unit Sale Price (USP)": "Rs. 999.00 per N",
        "Mfg Date": "06/2026",
        "Country of Origin": "India",
        "Consumer Care": "Consumer Officer, Call: 0161-2400123, Email: help@urbanstitcher.com"
    }
    create_synthetic_package(
        os.path.join(output_dir, "sample_garment_package.jpg"),
        "URBAN STITCHER POLO",
        "GARMENTS",
        garment_fields
    )

if __name__ == "__main__":
    generate_all_samples()
