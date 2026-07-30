"""
Polygon operations module for AutoDCR Geometry Engine.
Provides polygon detection, boundary detection, merging, and splitting.
"""

from typing import List, Dict, Any, Tuple, Optional, Union
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import polygonize, unary_union
from app.geometry.engine import GeometryEngine


class PolygonOps:
    """
    High-level polygon operations combining GeometryEngine primitives.
    """

    @staticmethod
    def detect_closed_polygons(lines: List[Dict[str, Any]]) -> List[Polygon]:
        """
        Extracts all valid closed polygons formed by a set of line/polyline entities.
        """
        linestrings = []
        for line in lines:
            pts = line.get("points", [])
            if not pts and "start" in line and "end" in line:
                pts = [line["start"], line["end"]]
            if len(pts) >= 2:
                linestrings.append(LineString(pts))

        if not linestrings:
            return []

        # Find polygons formed by intersecting linestrings
        polygons = list(polygonize(linestrings))
        valid_polys = [p for p in polygons if p.is_valid and p.area > 1e-4]
        return valid_polys

    @staticmethod
    def detect_boundaries(polygons: List[Polygon]) -> Tuple[Optional[Polygon], List[Polygon]]:
        """
        Detects plot boundary (largest outer polygon) and building boundaries (interior large polygons).
        """
        if not polygons:
            return None, []

        sorted_polys = sorted(polygons, key=lambda p: p.area, reverse=True)
        plot_boundary = sorted_polys[0]
        building_boundaries = sorted_polys[1:]

        return plot_boundary, building_boundaries

    @staticmethod
    def merge_adjacent_polygons(polygons: List[Polygon], tolerance: float = 0.01) -> Polygon:
        """
        Merges adjacent or overlapping polygons into a single unified polygon/multipolygon.
        """
        if not polygons:
            return Polygon()
        buffered = [p.buffer(tolerance) for p in polygons]
        merged = unary_union(buffered)
        if isinstance(merged, (Polygon, MultiPolygon)):
            return merged.buffer(-tolerance)
        return merged

    @staticmethod
    def split_multi_polygon(multi_poly: Union[Polygon, MultiPolygon]) -> List[Polygon]:
        """
        Extracts individual Polygon objects from a MultiPolygon or Polygon.
        """
        if isinstance(multi_poly, Polygon):
            return [multi_poly] if not multi_poly.is_empty else []
        elif isinstance(multi_poly, MultiPolygon):
            return list(multi_poly.geoms)
        return []
