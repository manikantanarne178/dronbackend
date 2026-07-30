"""
Parser Output Normalizer module.
Converts outputs from DXF, DWG, IFC, and PDF parsers into a single standard AutoDCR schema.
"""

from typing import Dict, Any, List
from app.parser.common import ParsedDrawing
from app.geometry.unit_converter import UnitConverter


class OutputNormalizer:
    """
    Normalizes parsed drawing outputs into a standardized dictionary structure
    for downstream AutoDCR detection, area, height, and rule validation engines.
    """

    @staticmethod
    def normalize(parsed: ParsedDrawing, target_unit: str = "m") -> Dict[str, Any]:
        """
        Normalizes a ParsedDrawing object into the standard AutoDCR dictionary structure.
        """
        source_unit = parsed.metadata.get("units", "mm") if parsed.metadata else "mm"
        scale_factor = UnitConverter.get_conversion_factor(source_unit, target_unit)

        # Basic normalized schema structure
        normalized = {
            "metadata": {
                "drawing_name": parsed.metadata.get("drawing_name", "UNKNOWN") if parsed.metadata else "UNKNOWN",
                "units": target_unit,
                "drawing_scale": parsed.metadata.get("drawing_scale", 1.0) if parsed.metadata else 1.0,
                "north_direction": parsed.metadata.get("north_direction", 90.0) if parsed.metadata else 90.0,
                "layers": parsed.layers,
                "building_labels": parsed.metadata.get("building_labels", []) if parsed.metadata else [],
                "room_labels": parsed.metadata.get("room_labels", []) if parsed.metadata else [],
                "road_labels": parsed.metadata.get("road_labels", []) if parsed.metadata else [],
                "floor_labels": parsed.metadata.get("floor_labels", []) if parsed.metadata else [],
            },
            "entities": {
                "lines": parsed.lines,
                "polylines": parsed.polylines,
                "circles": parsed.circles,
                "arcs": parsed.arcs,
                "ellipses": parsed.ellipses,
                "splines": parsed.splines,
                "hatches": parsed.hatches,
                "leaders": parsed.leaders,
                "texts": parsed.texts,
                "dimensions": parsed.dimensions,
                "blocks": parsed.blocks,
                "inserts": parsed.inserts,
            },
            "polygons": [],
            "plot_boundary": None,
            "building_boundary": None,
            "roads": [],
            "scale_factor": scale_factor
        }

        return normalized
