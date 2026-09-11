import cv2
import numpy as np
import os
from PIL import Image

class PDPImageProcessor:
    """
    Image Preprocessing & Principal Display Panel (PDP) Detector
    Handles image deskewing, rotation, PDP bounding box detection, and surface area calculation.
    """
    def __init__(self, target_dpi=300):
        self.target_dpi = target_dpi

    def load_image(self, image_path):
        """Loads image from file path using OpenCV."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not decode image at path: {image_path}")
        return img

    def deskew(self, image):
        """
        Detects skew angle in text/packaging layout and rotates image to upright position.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Thresholding
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find coordinates of non-zero pixels
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) == 0:
            return image, 0.0

        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct minAreaRect angle convention
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If skew angle is minimal, return original image
        if abs(angle) < 0.5:
            return image, 0.0

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        print(f"[IMAGE PROCESSOR] Deskewed image by {angle:.2f} degrees")
        return rotated, angle

    def detect_pdp(self, image, assumed_dpi=150, physical_width_cm=None, physical_height_cm=None):
        """
        Detects the Principal Display Panel (PDP) boundary and calculates surface area in cm².
        
        Returns:
            dict containing:
                - pdp_crop: Cropped image array of the PDP
                - pdp_bbox: (x, y, width, height) in pixels
                - pdp_area_cm2: Surface area in cm²
                - contours: Contour points
        """
        h, w = image.shape[:2]

        # Convert to grayscale & blur
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edged = cv2.Canny(blurred, 50, 200)

        # Find contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_bbox = (0, 0, w, h)
        max_area = 0

        # Look for largest quadrilateral / rectangular contour
        for c in contours:
            area = cv2.contourArea(c)
            if area > (w * h * 0.15): # Must occupy at least 15% of image canvas
                x, y, cw, ch = cv2.boundingRect(c)
                if area > max_area:
                    max_area = area
                    best_bbox = (x, y, cw, ch)

        x, y, bw, bh = best_bbox

        # Crop PDP region
        pdp_crop = image[y:y+bh, x:x+bw]

        # Calculate physical PDP Area (cm²)
        if physical_width_cm and physical_height_cm:
            area_cm2 = physical_width_cm * physical_height_cm
        else:
            # Estimate using assumed DPI (1 inch = 2.54 cm)
            px_per_cm = (assumed_dpi / 2.54)
            width_cm = bw / px_per_cm
            height_cm = bh / px_per_cm
            area_cm2 = width_cm * height_cm

        return {
            "pdp_crop": pdp_crop,
            "pdp_bbox": (x, y, bw, bh),
            "pdp_area_cm2": round(area_cm2, 2),
            "canvas_size_px": (w, h),
            "pdp_size_cm": (round(bw / (assumed_dpi / 2.54), 1), round(bh / (assumed_dpi / 2.54), 1))
        }

    def process_pipeline(self, image_path):
        """End-to-end processing pipeline: load -> deskew -> detect PDP."""
        raw_img = self.load_image(image_path)
        deskewed_img, skew_angle = self.deskew(raw_img)
        pdp_info = self.detect_pdp(deskewed_img)
        pdp_info["skew_angle"] = skew_angle
        pdp_info["processed_image"] = deskewed_img
        return pdp_info
