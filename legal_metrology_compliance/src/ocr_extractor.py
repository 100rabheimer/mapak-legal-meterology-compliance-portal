import os
import cv2
import json
import re
import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class MultilingualOCRExtractor:
    """
    Multilingual Packaging OCR & Field Extractor.
    Combines Gemini Multimodal Vision AI (`gemini-3.6-flash`, `gemini-flash-latest`)
    with a local text region detector & regex heuristic parser fallback.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("[OCR ENGINE] Successfully initialized Gemini Multimodal Vision Client!")
            except Exception as e:
                print(f"[OCR ENGINE NOTICE] Gemini client initialization error: {e}")

    def extract_with_gemini_vision(self, image_path):
        """
        Uses Gemini Multimodal Vision AI to perform OCR and structured extraction of Legal Metrology fields,
        including normalized bounding box coordinates [ymin, xmin, ymax, xmax] (0-1000 scale).
        """
        if not self.client:
            return None

        try:
            pil_img = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"[OCR ENGINE NOTICE] Failed to open image for Gemini Vision: {e}")
            return None

        prompt = """
        You are an expert Legal Metrology Packaging Inspector for the Department of Consumer Affairs (DoCA), India.
        Analyze this product packaging label image and extract all statutory text declarations under Legal Metrology (Packaged Commodities) Rules, 2011.

        Extract the following mandatory fields in pure JSON format:
        {
          "commodity_name": "Generic name of commodity",
          "mfg_name_address": "Name and complete address of Manufacturer / Packer / Importer",
          "net_quantity": {
             "raw_text": "Exact text declaration e.g. 'NET QTY: 1 L (910 g)' or '500 GMS'",
             "value": 500,
             "unit": "GMS",
             "bbox": [ymin, xmin, ymax, xmax]  (0 to 1000 scale)
          },
          "mrp": {
             "raw_text": "Exact text e.g. 'MRP: Rs. 185.00 (Incl. of all taxes)'",
             "value": 185.0,
             "includes_taxes": true,
             "currency_symbol": "Rs.",
             "bbox": [ymin, xmin, ymax, xmax]
          },
          "unit_sale_price": {
             "raw_text": "Exact USP text e.g. 'Rs. 0.185 / ml' or null if missing",
             "present": true/false,
             "bbox": [ymin, xmin, ymax, xmax]
          },
          "mfg_date": {
             "raw_text": "Date of manufacture/pkd e.g. '08/2026'",
             "bbox": [ymin, xmin, ymax, xmax]
          },
          "country_of_origin": {
             "raw_text": "Country e.g. 'India'",
             "bbox": [ymin, xmin, ymax, xmax]
          },
          "consumer_care": {
             "raw_text": "Grievance details",
             "has_name": true/false,
             "has_phone": true/false,
             "has_email": true/false,
             "has_address": true/false,
             "bbox": [ymin, xmin, ymax, xmax]
          },
          "category_specific": {
             "category": "EDIBLE OILS | GARMENTS | PAN MASALA | MEDICAL DEVICES | E-COMMERCE | GENERAL",
             "declarations": { "garment_size": "...", "fiber_composition": "...", "oil_blend_ratio": "..." }
          },
          "all_raw_text_blocks": [
             { "text": "...", "bbox": [ymin, xmin, ymax, xmax] }
          ]
        }

        Return ONLY valid JSON without markdown formatting.
        """

        model_candidates = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash"]
        for model_name in model_candidates:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[pil_img, prompt]
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                data = json.loads(text.strip())
                print(f"[OCR SUCCESS ({model_name})] Vision extraction complete for {os.path.basename(image_path)}")
                return data
            except Exception as e:
                continue

        return None

    def extract_with_local_ocr(self, image_path):
        """
        Local OCR fallback using OpenCV text region analysis and regex parsing.
        """
        img = cv2.imread(image_path)
        if img is None:
            return self._heuristic_parse("", [], 800, 1000)
        
        h, w = img.shape[:2]
        extracted_text = ""
        raw_blocks = []

        # 1. Try pytesseract if available
        try:
            import pytesseract
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text_str = data['text'][i].strip()
                if text_str:
                    x, y, bw, bh = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    extracted_text += text_str + " "
                    norm_box = [
                        int((y / h) * 1000),
                        int((x / w) * 1000),
                        int(((y + bh) / h) * 1000),
                        int(((x + bw) / w) * 1000)
                    ]
                    raw_blocks.append({"text": text_str, "bbox": norm_box})
        except Exception:
            pass

        # 2. OpenCV Text Region Box Detection fallback
        if not raw_blocks:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Find horizontal text lines via morphological gradient
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Sort contours top to bottom
            contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
            for c in contours:
                x, y, bw, bh = cv2.boundingRect(c)
                if bw > 50 and bh > 10 and bh < (h * 0.15):
                    norm_box = [
                        int((y / h) * 1000),
                        int((x / w) * 1000),
                        int(((y + bh) / h) * 1000),
                        int(((x + bw) / w) * 1000)
                    ]
                    raw_blocks.append({"text": f"TEXT_LINE_{y}", "bbox": norm_box})

        return self._heuristic_parse(extracted_text, raw_blocks, w, h)

    def _heuristic_parse(self, text, raw_blocks, width_px, height_px):
        """Parses extracted OCR text lines using regex for mandatory fields."""
        fields = {
            "commodity_name": "Pre-Packaged Commodity",
            "mfg_name_address": None,
            "net_quantity": {"raw_text": None, "bbox": [500, 100, 560, 900]},
            "mrp": {"raw_text": None, "includes_taxes": False, "bbox": [580, 100, 640, 900]},
            "unit_sale_price": {"raw_text": None, "present": False, "bbox": [650, 100, 700, 900]},
            "mfg_date": {"raw_text": None, "bbox": [710, 100, 750, 900]},
            "country_of_origin": {"raw_text": None, "bbox": [760, 100, 800, 900]},
            "consumer_care": {"raw_text": None, "has_name": False, "has_phone": False, "has_email": False, "has_address": False, "bbox": [810, 100, 870, 900]},
            "category_specific": {"category": "GENERAL", "declarations": {}},
            "all_raw_text_blocks": raw_blocks
        }

        combined_text = text if text else " ".join([b["text"] for b in raw_blocks])
        
        # Match text patterns
        m_net = re.search(r'(NET\s*(?:QTY|QUANTITY|WT|WEIGHT)[^:\n]*:\s*[^\n]+)', combined_text, re.IGNORECASE)
        if m_net:
            fields["net_quantity"]["raw_text"] = m_net.group(1).strip()

        m_mrp = re.search(r'(MRP[^:\n]*:\s*[^\n]+|Rs\.?\s*\d+(?:\.\d+)?|₹\s*\d+)', combined_text, re.IGNORECASE)
        if m_mrp:
            raw_mrp = m_mrp.group(1).strip()
            fields["mrp"]["raw_text"] = raw_mrp
            fields["mrp"]["includes_taxes"] = ("incl" in combined_text.lower() or "taxes" in combined_text.lower())

        m_usp = re.search(r'(Unit\s*Sale\s*Price[^:\n]*:\s*[^\n]+|Rs\.?\s*\d+\.\d+\s*/\s*(?:g|ml|N))', combined_text, re.IGNORECASE)
        if m_usp:
            fields["unit_sale_price"]["raw_text"] = m_usp.group(1).strip()
            fields["unit_sale_price"]["present"] = True

        m_mfg = re.search(r'((?:Mfg|Pkd|Packed|Manufactured)\s*(?:Date)?\s*:\s*[^\n]+|\b\d{2}/\d{4}\b)', combined_text, re.IGNORECASE)
        if m_mfg:
            fields["mfg_date"]["raw_text"] = m_mfg.group(1).strip()

        m_coo = re.search(r'(Country\s*of\s*Origin\s*:\s*[^\n]+|Made\s*in\s*India|India)', combined_text, re.IGNORECASE)
        if m_coo:
            fields["country_of_origin"]["raw_text"] = m_coo.group(1).strip()

        m_care = re.search(r'(Consumer\s*Care[^:\n]*:\s*[^\n]+|Care\s*Manager[^\n]+)', combined_text, re.IGNORECASE)
        if m_care:
            fields["consumer_care"]["raw_text"] = m_care.group(1).strip()

        m_mfg_addr = re.search(r'((?:Manufacturer|Mfg\s*by|Packed\s*by)[^:\n]*:\s*[^\n]+)', combined_text, re.IGNORECASE)
        if m_mfg_addr:
            fields["mfg_name_address"] = m_mfg_addr.group(1).strip()

        # Update bounding boxes matching text blocks
        for b in raw_blocks:
            t = b["text"].lower()
            if "net" in t or "qty" in t:
                fields["net_quantity"]["bbox"] = b["bbox"]
                if not fields["net_quantity"]["raw_text"]:
                    fields["net_quantity"]["raw_text"] = b["text"]
            elif "mrp" in t or "rs" in t or "₹" in t:
                fields["mrp"]["bbox"] = b["bbox"]
                if not fields["mrp"]["raw_text"]:
                    fields["mrp"]["raw_text"] = b["text"]
            elif "usp" in t or "/ ml" in t or "/ g" in t:
                fields["unit_sale_price"]["bbox"] = b["bbox"]
                fields["unit_sale_price"]["present"] = True
                if not fields["unit_sale_price"]["raw_text"]:
                    fields["unit_sale_price"]["raw_text"] = b["text"]

        return fields

    def extract(self, image_path):
        """
        Main entry point: Tries Gemini Multimodal Vision AI first, falls back to Local OCR parsing.
        """
        vision_result = self.extract_with_gemini_vision(image_path)
        if vision_result:
            return vision_result
        
        print("[OCR ENGINE] Gemini Vision API fallback. Using local OCR & text box region extractor...")
        return self.extract_with_local_ocr(image_path)
