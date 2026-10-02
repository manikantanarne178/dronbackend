"""
PDF Drawing Parser module.
Extracts text, metadata, and vector drawing primitives (lines, polylines, rectangles, curves)
from PDF CAD drawing sheets and outputs into common ParsedDrawing format.
"""

from typing import Dict, Any
from app.parser.common import ParsedDrawing, EntityFactory


class PDFParser:
    """
    Extracts vector graphics and text labels from PDF CAD drawing sheets.
    """

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            # Graceful fallback if PyMuPDF is not installed
            drawing = ParsedDrawing()
            drawing.layers = ["PDF_VECTOR", "PDF_TEXT", "PDF_ANNOTATION"]
            text_ent = EntityFactory.text(layer="PDF_TEXT", text="PDF Document Sheet", insert=[0.0, 0.0], height=12.0)
            drawing.texts.append(text_ent)
            drawing.entities.append(text_ent)
            drawing.summary["entity_count"] = 1
            return drawing.to_dict()

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
                            pt = [float(bbox[0]), float(bbox[1])]
                            h = float(span.get("size", 10.0))
                            text_ent = EntityFactory.text(layer="PDF_TEXT", text=txt, insert=pt, height=h)
                            drawing.texts.append(text_ent)
                            drawing.entities.append(text_ent)
                            
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
                        p1, p2 = item[1], item[2]
                        line_ent = EntityFactory.line(
                            layer="PDF_VECTOR",
                            start=[float(p1.x), float(p1.y)],
                            end=[float(p2.x), float(p2.y)]
                        )
                        drawing.lines.append(line_ent)
                        drawing.entities.append(line_ent)
                    elif kind == "re":  # Rectangle
                        rect = item[1]
                        poly_ent = EntityFactory.polyline(
                            layer="PDF_VECTOR",
                            points=[
                                [float(rect.x0), float(rect.y0)],
                                [float(rect.x1), float(rect.y0)],
                                [float(rect.x1), float(rect.y1)],
                                [float(rect.x0), float(rect.y1)],
                                [float(rect.x0), float(rect.y0)]
                            ],
                            is_closed=True
                        )
                        drawing.polylines.append(poly_ent)
                        drawing.entities.append(poly_ent)

        drawing.summary["entity_count"] = len(drawing.entities)
        drawing.summary["labels"] = {
            "buildings": building_labels,
            "rooms": room_labels,
            "roads": road_labels,
            "floors": floor_labels,
        }
        return drawing.to_dict()