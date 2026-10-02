import re
from typing import List, Dict, Any, Optional

_PLOT_LAYER_RE = re.compile(
    r"\b(plot|boundary|site|property|compound|land|plot_boundary|site_boundary)\b",
    re.IGNORECASE,
)


class PlotDetector:

    @staticmethod
    def detect(polygons: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not polygons:
            return None

        # 1. Layer-specific matching
        for p in polygons:
            layer = str(p.get("layer", "")).strip()
            if _PLOT_LAYER_RE.search(layer):
                return {
                    "points": p["points"],
                    "area": float(p["area"]),
                    "centroid": p["centroid"],
                    "layer": layer,
                    "confidence": 0.98,
                }

        # 2. Largest polygon by area
        sorted_polys = sorted(polygons, key=lambda x: float(x.get("area", 0.0)), reverse=True)
        if sorted_polys:
            plot = sorted_polys[0]
            return {
                "points": plot["points"],
                "area": float(plot["area"]),
                "centroid": plot["centroid"],
                "layer": plot.get("layer", "LARGEST_ENCLOSURE"),
                "confidence": 0.90,
            }

        return None