import re
from typing import List, Dict, Any, Optional
from shapely.geometry import Polygon

_BLDG_LAYER_RE = re.compile(
    r"\b(building|structure|footprint|proposed|proposed_building|bldg|ground_floor|tower|block|superstructure)\b",
    re.IGNORECASE,
)


class BuildingDetector:

    @staticmethod
    def normalize_point(point):
        if isinstance(point, dict):
            return float(point["x"]), float(point["y"])
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            return float(point[0]), float(point[1])
        raise ValueError(f"Invalid point format: {point}")

    @staticmethod
    def detect(polygons: List[Dict[str, Any]], plot: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not polygons:
            return None

        # 1. Layer-specific matching
        for p in polygons:
            layer = str(p.get("layer", "")).strip()
            if _BLDG_LAYER_RE.search(layer):
                return {
                    "points": p["points"],
                    "area": float(p["area"]),
                    "centroid": p["centroid"],
                    "layer": layer,
                    "confidence": 0.98,
                }

        # 2. Geometric containment within plot
        plot_area = float(plot.get("area", 0.0)) if plot else float("inf")
        plot_poly = None
        if plot and "points" in plot and len(plot["points"]) >= 3:
            try:
                plot_poly = Polygon(plot["points"])
            except Exception:
                pass

        candidates = []
        for p in polygons:
            p_area = float(p.get("area", 0.0))
            if p_area >= plot_area or p_area <= 1e-4:
                continue

            # Check if inside plot
            if plot_poly:
                try:
                    c_poly = Polygon(p["points"])
                    if plot_poly.contains(c_poly) or plot_poly.intersects(c_poly):
                        candidates.append(p)
                except Exception:
                    candidates.append(p)
            else:
                candidates.append(p)

        if candidates:
            candidates.sort(key=lambda x: float(x.get("area", 0.0)), reverse=True)
            chosen = candidates[0]
            return {
                "points": chosen["points"],
                "area": float(chosen["area"]),
                "centroid": chosen["centroid"],
                "layer": chosen.get("layer", "INNER_POLYGON"),
                "confidence": 0.90,
            }

        # 3. If only 2 polygons exist, the second largest is building
        if len(polygons) >= 2:
            sorted_polys = sorted(polygons, key=lambda x: float(x.get("area", 0.0)), reverse=True)
            chosen = sorted_polys[1]
            return {
                "points": chosen["points"],
                "area": float(chosen["area"]),
                "centroid": chosen["centroid"],
                "layer": chosen.get("layer", "SECOND_LARGEST"),
                "confidence": 0.85,
            }

        return None