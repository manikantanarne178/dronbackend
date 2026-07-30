"""
Floor & Open Space Detector module for AutoDCR.
Automatically detects Balconies, Basements, Terraces, Open Spaces, and Landscape Areas.
"""

from typing import Dict, Any, List
from shapely.geometry import Polygon


class FloorDetector:
    """
    Automatic detection of balconies, basements, terraces, open spaces, and landscape areas.
    """

    BALCONY_KEYWORDS = ["BALCONY", "BALC", "VERANDAH", "PROJECTION"]
    BASEMENT_KEYWORDS = ["BASEMENT", "CELLAR", "BSMT"]
    TERRACE_KEYWORDS = ["TERRACE", "ROOF", "MUMTY", "PARAPET"]
    LANDSCAPE_KEYWORDS = ["LANDSCAPE", "GREEN", "GARDEN", "PLANTATION", "SOFT_SCAPE"]
    OPEN_SPACE_KEYWORDS = ["OPEN_SPACE", "COURTYARD", "MARGIN", "SETBACK_ZONE"]

    @staticmethod
    def detect_floor_elements(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects floor spaces, projections, basements, terraces, and green/open spaces.
        """
        entities = parsed_data.get("entities", {})
        polylines = entities.get("polylines", [])

        balconies: List[Dict[str, Any]] = []
        basements: List[Dict[str, Any]] = []
        terraces: List[Dict[str, Any]] = []
        landscapes: List[Dict[str, Any]] = []
        open_spaces: List[Dict[str, Any]] = []

        for poly in polylines:
            layer = poly.get("layer", "").upper()
            pts = poly.get("points", [])
            if len(pts) < 3:
                continue

            try:
                p = Polygon(pts)
                info = {
                    "layer": poly.get("layer"),
                    "area": p.area,
                    "bounds": p.bounds,
                }

                if any(kw in layer for kw in FloorDetector.BALCONY_KEYWORDS):
                    balconies.append(info)
                elif any(kw in layer for kw in FloorDetector.BASEMENT_KEYWORDS):
                    basements.append(info)
                elif any(kw in layer for kw in FloorDetector.TERRACE_KEYWORDS):
                    terraces.append(info)
                elif any(kw in layer for kw in FloorDetector.LANDSCAPE_KEYWORDS):
                    landscapes.append(info)
                elif any(kw in layer for kw in FloorDetector.OPEN_SPACE_KEYWORDS):
                    open_spaces.append(info)
            except Exception:
                pass

        total_landscape_area = sum(item["area"] for item in landscapes)
        total_open_space_area = sum(item["area"] for item in open_spaces)
        total_balcony_area = sum(item["area"] for item in balconies)

        return {
            "balconies": balconies,
            "balcony_count": len(balconies),
            "total_balcony_area": total_balcony_area,
            "basements": basements,
            "basement_count": len(basements),
            "terraces": terraces,
            "terrace_count": len(terraces),
            "landscapes": landscapes,
            "total_landscape_area": total_landscape_area,
            "open_spaces": open_spaces,
            "total_open_space_area": total_open_space_area,
        }
