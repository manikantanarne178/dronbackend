"""
Polygon operations module for AutoDCR Geometry Engine.
Provides polygon detection, boundary detection, merging, and splitting.
"""

from typing import List, Dict, Any, Tuple, Optional, Union
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import polygonize, unary_union


class CADPolygon:
    """
    Shapely Polygon wrapper that preserves CAD layer metadata and entity origin,
    supporting both attribute and dictionary-style access.
    """
    def __init__(self, polygon: Polygon, layer: str = "DEFAULT", source_entity: str = "POLYLINE"):
        self.polygon = polygon
        self.layer = layer
        self.source_entity = source_entity

    @property
    def area(self) -> float:
        return float(self.polygon.area)

    @property
    def exterior(self):
        return self.polygon.exterior

    @property
    def centroid(self):
        return self.polygon.centroid

    @property
    def points(self) -> List[List[float]]:
        if hasattr(self.polygon, "exterior") and self.polygon.exterior:
            return [[float(x), float(y)] for x, y in self.polygon.exterior.coords]
        return []

    @property
    def is_valid(self) -> bool:
        return bool(self.polygon.is_valid)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "layer":
            return self.layer
        elif key == "area":
            return self.area
        elif key == "points":
            return self.points
        elif key == "centroid":
            return [float(self.centroid.x), float(self.centroid.y)]
        elif key == "source_entity":
            return self.source_entity
        elif hasattr(self, key):
            return getattr(self, key)
        elif hasattr(self.polygon, key):
            return getattr(self.polygon, key)
        return default

    def __getitem__(self, key: str) -> Any:
        val = self.get(key, None)
        if val is None and key not in ("layer", "area", "points", "centroid", "source_entity"):
            raise KeyError(key)
        return val

    def __contains__(self, key: str) -> bool:
        return key in ("layer", "area", "points", "centroid", "source_entity", "polygon")

    def __getattr__(self, name: str) -> Any:
        if "polygon" in self.__dict__:
            return getattr(self.__dict__["polygon"], name)
        raise AttributeError(f"'CADPolygon' object has no attribute '{name}'")

    def __repr__(self) -> str:
        return f"<CADPolygon layer='{self.layer}' area={self.area:.2f}>"


class PolygonOps:
    """
    High-level polygon operations combining GeometryEngine primitives.
    """

    @staticmethod
    def detect_closed_polygons(entities: List[Dict[str, Any]]) -> List[CADPolygon]:
        """
        Extracts all valid closed polygons formed by polyline and line entities,
        preserving layer attributes and calculating area and centroid.
        """
        polygons: List[CADPolygon] = []
        linestrings = []

        for entity in entities:
            if not isinstance(entity, dict):
                continue

            layer = entity.get("layer", "DEFAULT")
            pts = entity.get("points", [])
            closed = entity.get("closed", False) or entity.get("is_closed", False)

            # Check if entity is already a closed polyline/polygon (>= 3 points)
            if pts and len(pts) >= 3:
                try:
                    clean_pts = [(float(p[0]), float(p[1])) for p in pts]
                    if clean_pts[0] != clean_pts[-1]:
                        clean_pts.append(clean_pts[0])
                    
                    poly = Polygon(clean_pts)
                    if poly.is_valid and poly.area > 1e-4:
                        polygons.append(CADPolygon(poly, layer=layer, source_entity=entity.get("type", "POLYLINE")))
                except Exception:
                    pass

            # Segment polyline edges for polygonize assembly (supports 2-point and multi-point)
            if pts and len(pts) >= 2:
                for i in range(len(pts) - 1):
                    p1 = (float(pts[i][0]), float(pts[i][1]))
                    p2 = (float(pts[i + 1][0]), float(pts[i + 1][1]))
                    if p1 != p2:
                        linestrings.append(LineString([p1, p2]))
                if closed and len(pts) >= 3:
                    p_last = (float(pts[-1][0]), float(pts[-1][1]))
                    p_first = (float(pts[0][0]), float(pts[0][1]))
                    if p_last != p_first:
                        linestrings.append(LineString([p_last, p_first]))

            elif "start" in entity and "end" in entity:
                p1 = (float(entity["start"][0]), float(entity["start"][1]))
                p2 = (float(entity["end"][0]), float(entity["end"][1]))
                if p1 != p2:
                    linestrings.append(LineString([p1, p2]))

        # Find additional polygons formed by intersecting line segments
        if linestrings:
            try:
                poly_from_lines = list(polygonize(linestrings))
                for poly in poly_from_lines:
                    if poly.is_valid and poly.area > 1e-4:
                        # Avoid duplicates if already detected
                        is_dup = any(abs(p.area - float(poly.area)) < 1e-3 and abs(p.centroid.x - float(poly.centroid.x)) < 1e-3 for p in polygons)
                        if not is_dup:
                            polygons.append(CADPolygon(poly, layer="DETECTED_LOOP", source_entity="LINE_ASSEMBLY"))
            except Exception:
                pass

        return polygons

    @staticmethod
    def detect_boundaries(polygons: List[Union[Polygon, CADPolygon]]) -> Tuple[Optional[Union[Polygon, CADPolygon]], List[Union[Polygon, CADPolygon]]]:
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
    def merge_adjacent_polygons(polygons: List[Union[Polygon, CADPolygon]], tolerance: float = 0.01) -> Polygon:
        """
        Merges adjacent or overlapping polygons into a single unified polygon/multipolygon.
        """
        if not polygons:
            return Polygon()
        raw_polys = [p.polygon if isinstance(p, CADPolygon) else p for p in polygons]
        buffered = [p.buffer(tolerance) for p in raw_polys]
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
