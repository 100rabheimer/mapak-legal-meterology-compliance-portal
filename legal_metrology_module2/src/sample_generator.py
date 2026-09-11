import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class SamplePackageGenerator:
    """
    Generates realistic synthetic PDP packaging panel images (Compliant & Non-Compliant variants)
    for automated unit testing, visual inspection, and verification of Module 2.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(self):
        non_compliant_path = os.path.join(self.output_dir, "sample_package_non_compliant.png")
        compliant_path = os.path.join(self.output_dir, "sample_package_compliant.png")

        self._create_package_image(
            output_path=non_compliant_path,
            title="PREMIUM SNACK FOODS (NON-COMPLIANT SAMPLE)",
            net_qty="Net Qty: 500 gms",           # VIOLATION: Illegal unit symbol 'gms'
            mrp="MRP Rs. 250.00",                 # VIOLATION: Missing 'incl of all taxes' clause
            include_usp=False,                    # VIOLATION: Missing USP for > 10g
            mfg_date="Pkd: 08/2026",
            mfg_details="Mfd By: Quality Foods Pvt Ltd, Industrial Area, Plot 42, Delhi - 110042",
            customer_care="Customer Care: 1800-111-222, email: care@qualityfoods.com",
            country_of_origin="Country of Origin: India",
            font_size_px=14,                      # Small font -> font height violation
            is_compliant=False
        )

        self._create_package_image(
            output_path=compliant_path,
            title="PREMIUM SNACK FOODS (100% COMPLIANT SAMPLE)",
            net_qty="Net Qty: 500 g",             # COMPLIANT unit symbol 'g'
            mrp="MRP ₹ 250.00 (Incl. of all taxes)", # COMPLIANT MRP clause
            include_usp=True,                     # COMPLIANT USP
            mfg_date="Pkd: 08/2026",
            mfg_details="Mfd By: Quality Foods Pvt Ltd, Industrial Area, Plot 42, Delhi - 110042",
            customer_care="Consumer Care: 1800-111-222 | care@qualityfoods.com | Plot 42, Delhi",
            country_of_origin="Country of Origin: India",
            font_size_px=24,                      # Large compliant font height
            is_compliant=True
        )

        return non_compliant_path, compliant_path

    def _create_package_image(self, output_path: str, title: str, net_qty: str, mrp: str, include_usp: bool, mfg_date: str, mfg_details: str, customer_care: str, country_of_origin: str, font_size_px: int, is_compliant: bool):
        # Create canvas: 800 x 1000 pixels (simulates a standard PDP panel)
        width, height = 800, 1000
        img = Image.new("RGB", (width, height), color=(245, 245, 240))
        draw = ImageDraw.Draw(img)

        # Draw outer package border
        draw.rectangle([20, 20, width - 20, height - 20], outline=(40, 40, 40), width=4)

        # Draw Brand Header Box
        header_color = (30, 80, 150) if is_compliant else (180, 50, 40)
        draw.rectangle([30, 30, width - 30, 150], fill=header_color)

        try:
            font_title = ImageFont.truetype("arial.ttf", 26)
            font_body = ImageFont.truetype("arial.ttf", font_size_px)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((50, 60), title, fill=(255, 255, 255), font=font_title)
        draw.text((50, 100), "ROASTED ALMONDS & CASHEWS MIX", fill=(220, 220, 220), font=font_small)

        # Draw PDP Declarations Box
        pdp_y1 = 180
        pdp_y2 = height - 150
        draw.rectangle([40, pdp_y1, width - 40, pdp_y2], outline=(100, 100, 100), width=2)
        draw.text((50, pdp_y1 + 10), "[ PRINCIPAL DISPLAY PANEL - PDP ]", fill=(120, 120, 120), font=font_small)

        curr_y = pdp_y1 + 45

        # 1. Generic Name
        draw.text((60, curr_y), "Commodity: Premium Mixed Dry Fruits", fill=(20, 20, 20), font=font_body)
        curr_y += font_size_px + 20

        # 2. Net Quantity
        draw.text((60, curr_y), net_qty, fill=(10, 10, 10), font=font_body)
        curr_y += font_size_px + 20

        # 3. MRP
        draw.text((60, curr_y), mrp, fill=(10, 10, 10), font=font_body)
        curr_y += font_size_px + 20

        # 4. USP (if included)
        if include_usp:
            draw.text((60, curr_y), "USP: ₹ 0.50 / g", fill=(10, 10, 10), font=font_body)
            curr_y += font_size_px + 20

        # 5. Mfg Date
        draw.text((60, curr_y), mfg_date, fill=(20, 20, 20), font=font_body)
        curr_y += font_size_px + 20

        # 6. Country of Origin
        draw.text((60, curr_y), country_of_origin, fill=(20, 20, 20), font=font_body)
        curr_y += font_size_px + 25

        # 7. Manufacturer Details
        draw.text((60, curr_y), mfg_details, fill=(40, 40, 40), font=font_small)
        curr_y += 35

        # 8. Consumer Care Details
        draw.text((60, curr_y), customer_care, fill=(40, 40, 40), font=font_small)
        curr_y += 45

        # Draw Synthetic Barcode Anchor at bottom
        barcode_x1, barcode_y1 = 60, height - 130
        barcode_x2, barcode_y2 = 280, height - 40
        draw.rectangle([barcode_x1, barcode_y1, barcode_x2, barcode_y2], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        
        # Draw barcode vertical stripes
        stripe_x = barcode_x1 + 10
        while stripe_x < barcode_x2 - 10:
            stripe_w = np.random.choice([2, 4, 6])
            draw.rectangle([stripe_x, barcode_y1 + 5, stripe_x + stripe_w, barcode_y2 - 20], fill=(0, 0, 0))
            stripe_x += stripe_w + np.random.choice([2, 3, 5])
        
        draw.text((barcode_x1 + 15, barcode_y2 - 18), "8 901234 567890", fill=(0, 0, 0), font=font_small)

        img.save(output_path)
        print(f"[SampleGenerator] Generated sample PDP image: {output_path}")

if __name__ == "__main__":
    gen = SamplePackageGenerator()
    gen.generate_all()
