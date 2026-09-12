import os
import re
import json
import time
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class OCRExtractor:
    """
    Stage 2: Multilingual OCR & Declaration Field Extraction.
    Multi-engine extraction pipeline:
      Engine 1: Gemini Vision AI (primary, with multi-model fallback chain)
      Engine 2: PyTesseract OCR (secondary local fallback)
      Engine 3: OpenCV MSER text region detector (tertiary offline fallback)

    Extracts all 8 mandatory declarations required by Rule 6(1) & Rule 11.
    """

    # Gemini model fallback chain - prioritized by current availability and low latency
    GEMINI_MODEL_CHAIN = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.6-flash",
    ]

    # Max retry attempts per model, with exponential backoff
    MAX_RETRIES_PER_MODEL = 2
    INITIAL_RETRY_DELAY = 5  # seconds

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[OCRExtractor] Gemini API init notice: {e}")

    def extract_declarations(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extracts structured legal declarations and bounding boxes from packaging panel image.
        Tries Gemini Vision AI models first (with retry/fallback chain), then Tesseract, then OpenCV MSER.
        """
        # Engine 1: Gemini Vision AI (try multiple models)
        if self.client:
            for model_name in self.GEMINI_MODEL_CHAIN:
                delay = self.INITIAL_RETRY_DELAY
                for attempt in range(self.MAX_RETRIES_PER_MODEL):
                    try:
                        print(f"[OCRExtractor] Trying Gemini model '{model_name}' (attempt {attempt + 1})...")
                        result = self._extract_with_gemini(image, model_name)
                        if result and result.get("fields"):
                            present_count = sum(1 for f in result["fields"].values() if f.get("present"))
                            print(f"[OCRExtractor] Gemini Vision AI extraction successful via '{model_name}' ({present_count}/8 fields detected).")
                            return result
                    except Exception as e:
                        err_str = str(e)
                        if "503" in err_str or "UNAVAILABLE" in err_str:
                            print(f"[OCRExtractor] Model '{model_name}' is high demand (503). Switching immediately to next model...")
                            break
                        elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            if attempt < self.MAX_RETRIES_PER_MODEL - 1:
                                print(f"[OCRExtractor] Rate limited on '{model_name}'. Retrying in {delay}s...")
                                time.sleep(delay)
                                delay = min(delay * 2, 60)
                                continue
                            else:
                                print(f"[OCRExtractor] Quota exhausted for '{model_name}'. Trying next model...")
                                break
                        elif "404" in err_str or "NOT_FOUND" in err_str:
                            print(f"[OCRExtractor] Model '{model_name}' unavailable. Trying next model...")
                            break
                        else:
                            print(f"[OCRExtractor] Gemini error on '{model_name}': {e}")
                            break

            print("[OCRExtractor] All Gemini models exhausted. Falling back to local OCR engines.")

        # Engine 2: Tesseract OCR
        tess_result = self._extract_with_tesseract(image)
        if tess_result and any(f.get("present") for f in tess_result.get("fields", {}).values()):
            print("[OCRExtractor] Tesseract OCR extraction successful.")
            return tess_result

        # Engine 3: OpenCV MSER text region detector (last resort)
        print("[OCRExtractor] Using OpenCV MSER text region detector as final fallback.")
        return self._extract_with_opencv_mser(image)

    def _build_gemini_prompt(self) -> str:
        """Builds the structured Gemini Vision prompt for packaging declaration extraction."""
        return """You are an expert Legal Metrology Packaging Inspector for the Department of Consumer Affairs (DoCA), India.

Carefully analyze this packaging image. Find and extract ALL 8 mandatory legal declarations under Rule 6(1) of the Legal Metrology (Packaged Commodities) Rules, 2011.

For EACH of the 8 fields below, locate the text on the package and provide PRECISE bounding box coordinates.

MANDATORY RULES & BOUNDING BOX REQUIREMENTS:
1. manufacturer_details: Full Manufacturer / Packer / Importer block. Look for "Mfd By:", "Manufactured By:", "Marketed By:", "Packed By:" followed by company name and postal address. Bounding box MUST enclose the entire manufacturer name + postal address block.
2. generic_name: Common or generic product name (e.g., "ALL IN ONE", "KHATTA MEETHA", "Namkeen", "Biscuits"). Usually the prominent title. Box MUST enclose the full product name text.
3. net_quantity: Net quantity declaration (e.g., "NET QUANTITY : 200g" or "NET QTY: 210g"). Bounding box MUST enclose the ENTIRE key-value line: from the label "NET QUANTITY :" on the left to the numeric value "200g" on the right.
4. mfg_date: Date of manufacture or packaging.
   - In tabular layouts, locate the pre-printed label "MFG. DATE :" and the stamped manufacturing date (e.g. "06/05/26" or "23/05/26").
   - Your bounding box MUST START at the top of "MFG. DATE :". DO NOT omit "MFG. DATE :" or start at "USE BY :"!
   - The box must span across to enclose both the label and the date stamp.
5. mrp: Maximum Retail Price.
   - Look at the table row for MRP. The pre-printed label has "MRP. ₹ (INCL. OF ALL TAXES);" or "MRP. ₹ (INCL. OF" or "M.R.P. :".
   - The stamped price is the total packet price (e.g. "Rs.60.00" or "Rs.50.00").
   - "label_box": [ymin, xmin, ymax, xmax] of the MRP label.
   - "value_box": [ymin, xmin, ymax, xmax] of the stamped price (e.g. "Rs.60.00").
   - "box_2d": Unified bounding box covering BOTH the MRP label and the price value.
   - CRITICAL: DO NOT merge MRP and USP! The MRP box must NOT extend down into the USP row!
6. usp: Unit Sale Price.
   - Look at the row for USP. The pre-printed label is "USP :" (or "ALL TAXES); USP :").
   - The stamped rate is the unit rate per gram/ml (e.g. "Rs.0.30/g" or "Rs.0.25/g").
   - "label_box": [ymin, xmin, ymax, xmax] of the USP label.
   - "value_box": [ymin, xmin, ymax, xmax] of the unit rate (e.g. "Rs.0.30/g").
   - "box_2d": Unified bounding box covering BOTH the USP label and the unit rate.
   - USP is a separate declaration from MRP. Keep their bounding boxes separate.
7. customer_care: Consumer / Customer Care contact details. Bounding box MUST enclose the entire customer care block (heading, address, phone numbers, email, web).
8. country_of_origin: Country of Origin declaration (e.g. "PRODUCT OF INDIA", "Made in India"). Bounding box MUST enclose the full declaration text.

CRITICAL COORDINATE REQUIREMENTS:
- All bounding boxes MUST be [ymin, xmin, ymax, xmax] normalized 0-1000.
- For table/column declarations (net_quantity, mfg_date, mrp, usp):
  Stretch horizontally from the beginning of the label (xmin) to the end of the stamped value (xmax).

Return ONLY a valid JSON object matching this schema:
{
  "fields": {
     "manufacturer_details": {"text": "full text including label and address", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]},
     "generic_name": {"text": "...", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]},
     "net_quantity": {"text": "full line e.g. NET QUANTITY : 200g", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]},
     "mfg_date": {"text": "full line e.g. MFG. DATE : 06/05/26", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]},
     "mrp": {"text": "full text e.g. MRP. (INCL. OF ALL TAXES): Rs.60.00", "present": true/false, "confidence": 0.0-1.0, "label_box": [ymin, xmin, ymax, xmax], "value_box": [ymin, xmin, ymax, xmax], "box_2d": [ymin, xmin, ymax, xmax]},
     "usp": {"text": "full text e.g. USP : Rs.0.30/g", "present": true/false, "confidence": 0.0-1.0, "label_box": [ymin, xmin, ymax, xmax], "value_box": [ymin, xmin, ymax, xmax], "box_2d": [ymin, xmin, ymax, xmax]},
     "customer_care": {"text": "...", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]},
     "country_of_origin": {"text": "...", "present": true/false, "confidence": 0.0-1.0, "box_2d": [ymin, xmin, ymax, xmax]}
  },
  "raw_ocr_text": "all visible text concatenated"
}"""

    def _extract_with_gemini(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """Uses Gemini Vision API to extract declarations with bounding boxes."""
        import PIL.Image
        from google.genai import types

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = PIL.Image.fromarray(rgb_image)

        prompt = self._build_gemini_prompt()

        response = self.client.models.generate_content(
            model=model_name,
            contents=[pil_img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )

        response_text = response.text.strip()
        # Clean JSON markdown fences
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback 1: Remove trailing commas before closing braces/brackets
            cleaned = re.sub(r',\s*([\]}])', r'\1', response_text)
            # Fallback 2: Extract content between first { and last }
            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')
            if first_brace != -1 and last_brace != -1:
                cleaned = cleaned[first_brace:last_brace+1]
            try:
                parsed = json.loads(cleaned)
            except Exception:
                # Fallback 3: Replace unescaped internal quotes
                cleaned = re.sub(r'(?<=:\s*")([^"\\]*(?:\\.[^"\\]*)*)"(?=[^,}\]\s])', r"\1'", cleaned)
                parsed = json.loads(cleaned)

        # Union label_box and value_box for mrp and usp if both detected
        if "fields" in parsed:
            for tk in ["mrp", "usp"]:
                fdata = parsed["fields"].get(tk, {})
                l_box = fdata.get("label_box")
                v_box = fdata.get("value_box")
                if l_box and v_box and len(l_box) == 4 and len(v_box) == 4:
                    fdata["box_2d"] = [
                        min(float(l_box[0]), float(v_box[0])),
                        min(float(l_box[1]), float(v_box[1])),
                        max(float(l_box[2]), float(v_box[2])),
                        max(float(l_box[3]), float(v_box[3]))
                    ]

        # Post-process tabular key-value pair alignment (net_quantity, mfg_date, mrp, usp)
        # Guarantees that bounding boxes span the entire row from the left label column to the right value column
        if "fields" in parsed:
            table_keys = ["net_quantity", "mfg_date", "mrp", "usp"]
            valid_xmins = []
            valid_xmaxs = []
            for tk in table_keys:
                box = parsed["fields"].get(tk, {}).get("box_2d")
                if box and len(box) == 4:
                    valid_xmins.append(box[1])
                    valid_xmaxs.append(box[3])

            if valid_xmins:
                common_left = min(valid_xmins)
                common_right = max(valid_xmaxs)
                for tk in table_keys:
                    fdata = parsed["fields"].get(tk, {})
                    box = fdata.get("box_2d")
                    if box and len(box) == 4:
                        if box[1] > common_left + 40:
                            box[1] = common_left
                        if box[3] < common_right - 40:
                            box[3] = common_right
                        fdata["box_2d"] = box

            # Ensure mfg_date starts at MFG. DATE label, not at USE BY
            net_box = parsed["fields"].get("net_quantity", {}).get("box_2d")
            mfg_box = parsed["fields"].get("mfg_date", {}).get("box_2d")
            if net_box and mfg_box:
                if mfg_box[0] > net_box[2] + 30:
                    mfg_box[0] = net_box[2] + 15

            # Prevent MRP and USP from overlapping or swallowing each other
            mrp_f = parsed["fields"].get("mrp", {})
            usp_f = parsed["fields"].get("usp", {})
            if mrp_f.get("present") and usp_f.get("present"):
                mrp_b = mrp_f.get("box_2d")
                usp_b = usp_f.get("box_2d")
                mrp_v = mrp_f.get("value_box")
                usp_v = usp_f.get("value_box")
                if mrp_b and usp_b:
                    # If MRP extends down past the top of USP, split cleanly between the two rows
                    if mrp_b[2] > usp_b[0]:
                        if mrp_v and usp_v and usp_v[0] > mrp_v[2]:
                            split_y = (mrp_v[2] + usp_v[0]) / 2.0
                        else:
                            split_y = (mrp_b[0] + usp_b[2]) / 2.0
                        mrp_b[2] = round(split_y, 1)
                        usp_b[0] = round(split_y, 1)

        # Convert normalized box_2d [ymin, xmin, ymax, xmax] (0-1, 0-100 or 0-1000) to pixel coordinates [x1, y1, x2, y2]
        img_h, img_w = image.shape[:2]
        if "fields" in parsed:
            for field_key, fdata in parsed["fields"].items():
                box = fdata.get("box_2d")
                if box and len(box) == 4:
                    box_vals = [float(v) for v in box]
                    max_val = max(box_vals)
                    if max_val <= 1.0:
                        denom = 1.0
                    elif max_val <= 100.0:
                        denom = 100.0
                    else:
                        denom = 1000.0
                    ymin, xmin, ymax, xmax = box_vals
                    
                    ymin_c, ymax_c = min(ymin, ymax), max(ymin, ymax)
                    xmin_c, xmax_c = min(xmin, xmax), max(xmin, xmax)

                    x1 = int((xmin_c / denom) * img_w)
                    y1 = int((ymin_c / denom) * img_h)
                    x2 = int((xmax_c / denom) * img_w)
                    y2 = int((ymax_c / denom) * img_h)

                    # Clamp to image bounds
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(img_w - 1, x2), min(img_h - 1, y2)
                    fdata["bbox_pixel"] = [x1, y1, x2, y2]
                else:
                    fdata["bbox_pixel"] = None

        return parsed

    def _extract_with_tesseract(self, image: np.ndarray) -> Dict[str, Any]:
        """Tesseract OCR fallback with rule-based regex pattern matching and real bounding box detection."""
        h, w = image.shape[:2]
        raw_text = ""
        word_data = None

        try:
            import pytesseract
            # Get structured word-level bounding box data from Tesseract
            word_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            raw_text = pytesseract.image_to_string(image)
        except Exception as err:
            print(f"[OCRExtractor] Tesseract not available: {err}")
            return self._empty_fields_result()

        if not raw_text.strip():
            return self._empty_fields_result()

        fields = self._init_empty_fields()

        # Build line-level bounding boxes from word_data
        line_bboxes = self._build_line_bboxes(word_data, h, w)

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        for i, line in enumerate(lines):
            bbox = line_bboxes.get(i)

            # MRP pattern
            if re.search(r'(MRP|M\.R\.P|₹)\s*[:\.]?\s*(Rs\.?|₹)?\s*[0-9]', line, re.IGNORECASE):
                if not fields["mrp"]["present"]:
                    fields["mrp"] = {"text": line, "present": True, "confidence": 0.90, "bbox_pixel": bbox}

            # Net Quantity pattern
            if re.search(r'(NET\s*(QTY|QUANTITY|WT|WEIGHT|CONTENT)\s*[:\.]?\s*[0-9]|[0-9]+\s*(g|kg|ml|l|gms|gm)\b)', line, re.IGNORECASE):
                if not fields["net_quantity"]["present"]:
                    fields["net_quantity"] = {"text": line, "present": True, "confidence": 0.90, "bbox_pixel": bbox}

            # Mfg Date pattern
            if re.search(r'(MFG\.?\s*DATE|PKD|DATE\s*OF\s*(MFG|PACKING|MANUFACTURE))\s*[:\.]?\s*[0-9]', line, re.IGNORECASE):
                if not fields["mfg_date"]["present"]:
                    fields["mfg_date"] = {"text": line, "present": True, "confidence": 0.85, "bbox_pixel": bbox}

            # Customer Care pattern
            if re.search(r'(CUSTOMER\s*CARE|CONSUMER\s*(CARE|SERVICE)|FOR\s*(FEEDBACK|QUERIES)|TOLL\s*FREE|HELPLINE|1800[\-\s]?\d)', line, re.IGNORECASE):
                if not fields["customer_care"]["present"]:
                    # Aggregate multi-line customer care block
                    care_text = line
                    for j in range(i+1, min(i+5, len(lines))):
                        if re.search(r'(SECTOR|NOIDA|DELHI|BUDH|NAGAR|\d{6}|@|\.COM|0\d{2,3}[\-\s]\d{6,8}|1800)', lines[j], re.IGNORECASE):
                            care_text += " " + lines[j]
                        else:
                            break
                    bbox_ext = bbox
                    if bbox and i+1 < len(lines) and line_bboxes.get(min(i+4, len(lines)-1)):
                        end_bbox = line_bboxes.get(min(i+4, len(lines)-1))
                        if end_bbox:
                            bbox_ext = [min(bbox[0], end_bbox[0]), bbox[1], max(bbox[2], end_bbox[2]), max(bbox[3], end_bbox[3])]
                    fields["customer_care"] = {"text": care_text, "present": True, "confidence": 0.85, "bbox_pixel": bbox_ext}

            # Manufacturer pattern
            if re.search(r'(MFD\.?\s*BY|MANUFACTURED\s*BY|MARKETED\s*BY|PACKED\s*BY)\s*[:\.]?', line, re.IGNORECASE):
                if not fields["manufacturer_details"]["present"]:
                    mfr_text = line
                    for j in range(i+1, min(i+4, len(lines))):
                        if re.search(r'(PVT|LTD|LIMITED|VILLAGE|SECTOR|NOIDA|DELHI|HIGHWAY|\d{6})', lines[j], re.IGNORECASE):
                            mfr_text += " " + lines[j]
                        else:
                            break
                    bbox_ext = bbox
                    if bbox and i+1 < len(lines) and line_bboxes.get(min(i+3, len(lines)-1)):
                        end_bbox = line_bboxes.get(min(i+3, len(lines)-1))
                        if end_bbox:
                            bbox_ext = [min(bbox[0], end_bbox[0]), bbox[1], max(bbox[2], end_bbox[2]), max(bbox[3], end_bbox[3])]
                    fields["manufacturer_details"] = {"text": mfr_text, "present": True, "confidence": 0.85, "bbox_pixel": bbox_ext}

            # Country of Origin pattern
            if re.search(r'(PRODUCT\s*OF\s*INDIA|MADE\s*IN\s*INDIA|COUNTRY\s*OF\s*ORIGIN)', line, re.IGNORECASE):
                if not fields["country_of_origin"]["present"]:
                    fields["country_of_origin"] = {"text": line, "present": True, "confidence": 0.90, "bbox_pixel": bbox}

            # USP pattern
            if re.search(r'(USP|Rs\.?\s*[0-9.]+\s*/\s*(g|ml|kg|l)\b|₹\s*[0-9.]+\s*/\s*(g|ml|kg|l)\b)', line, re.IGNORECASE):
                if not fields["usp"]["present"]:
                    fields["usp"] = {"text": line, "present": True, "confidence": 0.85, "bbox_pixel": bbox}

            # Generic Name detection - first large prominent text (usually product name)
            if not fields["generic_name"]["present"] and i < 5:
                if len(line) > 3 and line.isupper() and not re.search(r'(MRP|MFG|NET|BATCH|INGREDIENTS|NUTRITIONAL|FSSAI|STORE|KEEP)', line, re.IGNORECASE):
                    fields["generic_name"] = {"text": line, "present": True, "confidence": 0.75, "bbox_pixel": bbox}

        return {
            "fields": fields,
            "raw_ocr_text": raw_text
        }

    def _extract_with_opencv_mser(self, image: np.ndarray) -> Dict[str, Any]:
        """
        OpenCV MSER (Maximally Stable Extremal Regions) text region detector.
        Detects text regions with bounding boxes even without any OCR engine.
        Cannot read text content, but identifies WHERE text exists and assigns regions
        to likely declaration fields based on spatial layout heuristics.
        """
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # MSER detector for text-like regions
        mser = cv2.MSER_create()
        mser.setMinArea(60)
        mser.setMaxArea(int(h * w * 0.15))

        regions, _ = mser.detectRegions(gray)

        # Merge overlapping MSER regions into text line bounding boxes
        bboxes = []
        for region in regions:
            x, y, bw, bh = cv2.boundingRect(region)
            if bh > 8 and bw > 10 and bw / bh < 30:  # filter noise
                bboxes.append([x, y, x + bw, y + bh])

        # Cluster nearby bounding boxes into text line groups
        merged_boxes = self._merge_nearby_boxes(bboxes, h, w)

        # Sort merged boxes by vertical position (top to bottom)
        merged_boxes.sort(key=lambda b: b[1])

        fields = self._init_empty_fields()

        # Assign regions to declaration fields using spatial layout heuristics
        # Bottom-right quadrant typically has Net Qty, MFG Date, MRP, USP
        # Bottom-left quadrant typically has Customer Care, Manufacturer details
        # Top area typically has Generic Name / Brand
        # Middle typically has Country of Origin, Manufacturer

        bottom_right_boxes = [b for b in merged_boxes if b[1] > h * 0.5 and b[0] > w * 0.35]
        bottom_left_boxes = [b for b in merged_boxes if b[1] > h * 0.5 and b[0] < w * 0.5]
        top_boxes = [b for b in merged_boxes if b[1] < h * 0.25]
        mid_boxes = [b for b in merged_boxes if h * 0.35 < b[1] < h * 0.7]

        field_assignments = [
            ("generic_name", top_boxes),
            ("net_quantity", bottom_right_boxes),
            ("mrp", bottom_right_boxes),
            ("mfg_date", bottom_right_boxes),
            ("usp", bottom_right_boxes),
            ("manufacturer_details", mid_boxes if mid_boxes else bottom_left_boxes),
            ("customer_care", bottom_left_boxes),
            ("country_of_origin", mid_boxes),
        ]

        used_boxes = set()
        for field_key, candidate_boxes in field_assignments:
            for box in candidate_boxes:
                box_tuple = tuple(box)
                if box_tuple not in used_boxes:
                    fields[field_key] = {
                        "text": f"[MSER Region Detected - OCR Unavailable]",
                        "present": True,
                        "confidence": 0.40,
                        "bbox_pixel": list(box)
                    }
                    used_boxes.add(box_tuple)
                    break

        return {
            "fields": fields,
            "raw_ocr_text": "[OpenCV MSER Region Detection - No OCR Engine Available. Install Tesseract or reset Gemini API quota.]"
        }

    def _merge_nearby_boxes(self, bboxes: List[List[int]], img_h: int, img_w: int) -> List[List[int]]:
        """Merges overlapping/nearby bounding boxes into text line groups."""
        if not bboxes:
            return []

        # Sort by y then x
        bboxes.sort(key=lambda b: (b[1], b[0]))

        merged = [bboxes[0]]
        y_threshold = img_h * 0.02  # merge if within 2% vertical distance
        x_threshold = img_w * 0.05  # merge if within 5% horizontal distance

        for box in bboxes[1:]:
            last = merged[-1]
            # Check vertical and horizontal proximity
            if (abs(box[1] - last[1]) < y_threshold and
                    box[0] < last[2] + x_threshold):
                # Merge
                merged[-1] = [
                    min(last[0], box[0]),
                    min(last[1], box[1]),
                    max(last[2], box[2]),
                    max(last[3], box[3])
                ]
            else:
                merged.append(box)

        # Filter out very small or very large merged boxes
        filtered = []
        for b in merged:
            bw = b[2] - b[0]
            bh = b[3] - b[1]
            if bh > 12 and bw > 30 and bw < img_w * 0.95 and bh < img_h * 0.3:
                filtered.append(b)

        return filtered

    def _build_line_bboxes(self, word_data: Dict, img_h: int, img_w: int) -> Dict[int, List[int]]:
        """Builds line-level bounding boxes from Tesseract word_data output."""
        line_map = {}
        n = len(word_data.get("text", []))

        for idx in range(n):
            text = word_data["text"][idx].strip()
            conf = int(word_data["conf"][idx]) if word_data["conf"][idx] != "-1" else 0
            if not text or conf < 30:
                continue

            line_num = word_data["line_num"][idx]
            block_num = word_data["block_num"][idx]
            key = (block_num, line_num)

            x = word_data["left"][idx]
            y = word_data["top"][idx]
            bw = word_data["width"][idx]
            bh = word_data["height"][idx]

            if key not in line_map:
                line_map[key] = [x, y, x + bw, y + bh]
            else:
                line_map[key][0] = min(line_map[key][0], x)
                line_map[key][1] = min(line_map[key][1], y)
                line_map[key][2] = max(line_map[key][2], x + bw)
                line_map[key][3] = max(line_map[key][3], y + bh)

        # Map sequential line index to bbox
        sorted_keys = sorted(line_map.keys())
        result = {}
        for i, key in enumerate(sorted_keys):
            result[i] = line_map[key]
        return result

    def _init_empty_fields(self) -> Dict[str, Dict]:
        return {
            "manufacturer_details": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "generic_name": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "net_quantity": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "mfg_date": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "mrp": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "usp": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "customer_care": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None},
            "country_of_origin": {"text": None, "present": False, "confidence": 0.0, "bbox_pixel": None}
        }

    def _empty_fields_result(self) -> Dict[str, Any]:
        return {
            "fields": self._init_empty_fields(),
            "raw_ocr_text": ""
        }
