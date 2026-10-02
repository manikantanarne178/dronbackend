"""
Image Drawing Parser module.
Processes raster drawings (PNG, JPG, JPEG, TIFF, BMP) using OpenCV / PIL
to extract image dimensions, aspect ratio, detect outer boundaries, contours,
and convert detected geometric contours into normalized ParsedDrawing format.
"""

import os
from typing import Dict, Any
from PIL import Image

from app.parser.common import ParsedDrawing, EntityFactory

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class ImageDrawingParser:
    """
    Analyzes raster drawing images (PNG, JPG, BMP) using computer vision / PIL.
    Extracts real pixel dimensions, bounding boxes, contours, and metadata.
    """

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        drawing = ParsedDrawing()
        drawing.layers = ["IMAGE_CONTOUR", "IMAGE_BOUNDARY", "IMAGE_ANNOTATION"]

        width = 800
        height = 600
        detected_polygons = []

        if HAS_OPENCV:
            img = cv2.imread(file_path)
            if img is None:
                try:
                    pil_img = Image.open(file_path)
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    raise ValueError(f"Failed to read image file {file_path}: {e}")

            height, width = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            min_area = (width * height) * 0.005
            max_area = (width * height) * 0.98

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area < area < max_area:
                    epsilon = 0.015 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    if len(approx) >= 3:
                        pts = [[float(pt[0][0]), float(height - pt[0][1])] for pt in approx]
                        detected_polygons.append(pts)
                        drawing.entities.append(
                            EntityFactory.polyline(
                                layer="IMAGE_CONTOUR",
                                points=pts,
                                closed=True,
                            )
                        )
        else:
            try:
                with Image.open(file_path) as pil_img:
                    width, height = pil_img.size
            except Exception as e:
                raise ValueError(f"Failed to read image file {file_path}: {e}")

        # Image outer boundary as reference frame
        boundary_pts = [
            [0.0, 0.0],
            [float(width), 0.0],
            [float(width), float(height)],
            [0.0, float(height)],
            [0.0, 0.0],
        ]
        drawing.entities.append(
            EntityFactory.polyline(
                layer="IMAGE_BOUNDARY",
                points=boundary_pts,
                closed=True,
            )
        )

        drawing.metadata = {
            "source_format": "IMAGE",
            "image_width_px": width,
            "image_height_px": height,
            "aspect_ratio": round(width / max(height, 1), 3),
            "detected_contour_count": len(detected_polygons),
            "units": "pixels",
            "drawing_scale": 1.0,
            "confidence": "PROCESSED",
            "note": "Image processed via computer vision raster analysis."
        }

        return drawing.to_dict()
