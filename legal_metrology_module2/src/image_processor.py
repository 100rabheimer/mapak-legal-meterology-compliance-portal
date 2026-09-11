import cv2
import numpy as np
import os
from typing import Dict, Any, Tuple, Optional

class ImageProcessor:
    """
    Stage 1: Image Preprocessing, PDP Boundary Detection, Deskewing,
    and PDP Surface Area (cm^2) Calculation.
    """

    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi

    def load_image(self, image_path: str) -> np.ndarray:
        """Loads image from disk with UTF-8 / Windows compatibility."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")
        
        # Read file via byte array to handle unicode paths reliably on Windows
        image_bytes = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Could not decode image at: {image_path}")
        return image

    def detect_pdp(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Detects the Principal Display Panel (PDP) surface area, boundary contour,
        and calculates pixel surface dimensions without distorting coordinate space.
        """
        h_orig, w_orig = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian Blur and Canny edge detection
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 150)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_cnt = None
        max_area = 0
        min_pdp_area = (h_orig * w_orig) * 0.15
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area and area >= min_pdp_area:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / max(1, h)
                if 0.2 <= aspect_ratio <= 5.0:
                    max_area = area
                    best_cnt = cnt

        if best_cnt is not None:
            peri = cv2.arcLength(best_cnt, True)
            approx = cv2.approxPolyDP(best_cnt, 0.02 * peri, True)
            x, y, w, h = cv2.boundingRect(best_cnt)
            bbox = [x, y, w, h]
            pts = approx.reshape(len(approx), 2).tolist() if len(approx) == 4 else [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
        else:
            bbox = [0, 0, w_orig, h_orig]
            pts = [[0, 0], [w_orig, 0], [w_orig, h_orig], [0, h_orig]]

        # Keep original image coordinate space so OCR bounding boxes match 100%
        pdp_cropped = image.copy()
        pdp_h, pdp_w = pdp_cropped.shape[:2]
        pixel_area = max_area if max_area > 0 else (pdp_h * pdp_w)

        metadata = {
            "original_shape": (h_orig, w_orig),
            "pdp_shape": (pdp_h, pdp_w),
            "bbox_xywh": bbox,
            "corners": pts,
            "pixel_area": pixel_area,
            "detected_contour": best_cnt is not None
        }

        return pdp_cropped, metadata

    def four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Performs 4-point perspective transformation to deskew the PDP."""
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        # Compute width of new image
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        # Compute height of new image
        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_width, max_height))
        return warped

    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """Orders coordinates: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def calculate_surface_area_cm2(self, pixel_area: float, scale_ratio_k: float) -> float:
        """
        Calculates PDP surface area in cm^2.
        scale_ratio_k is in mm / pixel.
        Area (mm^2) = pixel_area * (scale_ratio_k ^ 2)
        Area (cm^2) = Area (mm^2) / 100
        """
        area_mm2 = pixel_area * (scale_ratio_k ** 2)
        area_cm2 = area_mm2 / 100.0
        return round(area_cm2, 2)
