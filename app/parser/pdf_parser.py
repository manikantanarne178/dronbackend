"""
PDF Drawing Parser module.
Extracts text, metadata, and vector drawing primitives (lines, polylines, rectangles, curves)
from PDF CAD drawing sheets and outputs into common ParsedDrawing format.
"""

import fitz  # PyMuPDF
from typing import Dict, Any
from app.parser.common import ParsedDrawing, EntityFactory


class PDFParser:
    """
    Extracts vector graphics and text labels from PDF CAD drawing sheets.
    """

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        doc = fitz.open(file_path)
        drawing = ParsedDrawing()
        drawing.layers = ["PDF_VECTOR", "PDF_TEXT", "PDF_ANNOTATION"]

        building_labels = []
        room_labels = []
        road_labels = []
        floor_labels = []

        for page_number, page in enumerate(doc):
            # Extract text blocks with position
            blocks = page.get_text("dict").get("blocks", [])
            for b in blocks:
                if b.get("type") == 0:  # Text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span.get("text", "").strip()
                            if not txt:
                                continue
                            bbox = span.get("bbox", (0, 0, 0, 0))
                            pt = (bbox[0], bbox[1])
                            drawing.texts.append(EntityFactory.text(txt, pt, height=span.get("size", 10.0), layer="PDF_TEXT"))
                            
                            # Simple label classification heuristics
                            txt_upper = txt.upper()
                            if any(k in txt_upper for k in ["BUILDING", "BLOCK", "TOWER"]):
                                building_labels.append(txt)
                            elif any(k in txt_upper for k in ["ROOM", "HALL", "BEDROOM", "KITCHEN"]):
                                room_labels.append(txt)
                            elif any(k in txt_upper for k in ["ROAD", "STREET", "PATH", "WAY"]):
                                road_labels.append(txt)
                            elif any(k in txt_upper for k in ["FLOOR", "GROUND", "BASEMENT", "TERRACE"]):
                                floor_labels.append(txt)

            # Extract vector drawings
            drawings = page.get_drawings()
            for draw in drawings:
                items = draw.get("items", [])
                for item in items:
                    kind = item[0]
                    if kind == "l":  # Line
                        p1 = (item[1].x, item[1].y)
                        p2 = (item[2].x, item[2].y)
                        drawing.lines.append(EntityFactory.line(p1, p2, layer="PDF_VECTOR"))
                    elif kind == "re":  # Rect
                        r = item[1]
                        pts = [(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1), (r.x0, r.y0)]
                        drawing.polylines.append(EntityFactory.polyline(pts, is_closed=True, layer="PDF_VECTOR"))
                    elif kind == "c":  # Curve (Bezier)
                        pts = [(item[1].x, item[1].y), (item[2].x, item[2].y), (item[3].x, item[3].y), (item[4].x, item[4].y)]
                        drawing.splines.append(EntityFactory.spline(pts, layer="PDF_VECTOR"))

        metadata = doc.metadata or {}
        drawing.metadata = {
            "source_format": "PDF",
            "page_count": len(doc),
            "units": "pt",
            "drawing_scale": 1.0,
            "north_direction": 90.0,
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "building_labels": building_labels,
            "room_labels": room_labels,
            "road_labels": road_labels,
            "floor_labels": floor_labels,
        }

        doc.close()
        return drawing.to_dict()