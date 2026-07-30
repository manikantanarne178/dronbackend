import math
from typing import List, Tuple, Dict, Any, Optional

from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity


class GeometryEngine:
    """Production‑grade geometry utilities.

    All methods accept plain Python structures (list of points) and return
    either primitive values or Shapely objects.  The public API is deliberately
    small so it can be used from detectors, area calculators, setbacks, etc.
    """

    @staticmethod
    def to_shapely_polygon(points: List[Tuple[float, float]]) -> Polygon:
        """Convert a sequence of (x, y) points to a closed :class:`shapely.Polygon`.

        The function automatically closes the polygon if the first and last
        points differ.
        """
        if not points:
            raise ValueError("Empty point list cannot form a polygon")
        # Ensure closure
        if points[0] != points[-1]:
            points = points + [points[0]]
        return Polygon(points)

    @staticmethod
    def polygon_area(polygon: Polygon) -> float:
        return polygon.area

    @staticmethod
    def polygon_perimeter(polygon: Polygon) -> float:
        return polygon.length

    @staticmethod
    def polygon_centroid(polygon: Polygon) -> Tuple[float, float]:
        c: Point = polygon.centroid
        return (c.x, c.y)

    @staticmethod
    def bounding_box(polygon: Polygon) -> Dict[str, float]:
        minx, miny, maxx, maxy = polygon.bounds
        return {
            "min_x": minx,
            "min_y": miny,
            "max_x": maxx,
            "max_y": maxy,
            "width": maxx - minx,
            "height": maxy - miny,
        }

    @staticmethod
    def minimum_bounding_rectangle(polygon: Polygon) -> Polygon:
        """Return the minimum area bounding rectangle (oriented)."""
        return polygon.minimum_rotated_rectangle

    @staticmethod
    def convex_hull(polygon: Polygon) -> Polygon:
        return polygon.convex_hull

    @staticmethod
    def buffer(polygon: Polygon, distance: float) -> Polygon:
        """Create an outward (positive) or inward (negative) buffer.

        ``distance`` is in the same unit as the polygon coordinates.
        """
        return polygon.buffer(distance)

    @staticmethod
    def union(polygons: List[Polygon]) -> Polygon:
        if not polygons:
            return Polygon()
        return unary_union(polygons)

    @staticmethod
    def intersection(poly_a: Polygon, poly_b: Polygon) -> Polygon:
        return poly_a.intersection(poly_b)

    @staticmethod
    def difference(poly_a: Polygon, poly_b: Polygon) -> Polygon:
        return poly_a.difference(poly_b)

    @staticmethod
    def contains(outer: Polygon, inner: Polygon) -> bool:
        return outer.contains(inner)

    @staticmethod
    def self_intersects(polygon: Polygon) -> bool:
        """Detect self‑intersection (invalid geometry)."""
        return not polygon.is_valid

    @staticmethod
    def orientation(polygon: Polygon) -> str:
        """Return 'clockwise' or 'counterclockwise' based on signed area.
        """
        # Shapely's exterior.coords are ordered; signed area can be computed.
        x, y = zip(*list(polygon.exterior.coords)[:-1])  # drop closing point
        area = 0.0
        for i in range(len(x)):
            j = (i + 1) % len(x)
            area += x[i] * y[j] - x[j] * y[i]
        return "clockwise" if area < 0 else "counterclockwise"

    @staticmethod
    def rotate(polygon: Polygon, angle_deg: float, origin: Tuple[float, float] = (0, 0)) -> Polygon:
        return affinity.rotate(polygon, angle_deg, origin=origin)

    @staticmethod
    def translate(polygon: Polygon, xoff: float = 0, yoff: float = 0) -> Polygon:
        return affinity.translate(polygon, xoff, yoff)

    @staticmethod
    def scale(polygon: Polygon, xfact: float = 1, yfact: float = 1, origin: Tuple[float, float] = (0, 0)) -> Polygon:
        return affinity.scale(polygon, xfact, yfact, origin=origin)

    @staticmethod
    def multi_polygon(polygons: List[Polygon]) -> MultiPolygon:
        """Create a MultiPolygon geometry from a list of Polygon objects."""
        return MultiPolygon(polygons)

    @staticmethod
    def has_holes(polygon: Polygon) -> bool:
        """Check if a polygon contains interior rings (holes)."""
        return len(polygon.interiors) > 0

    @staticmethod
    def get_holes(polygon: Polygon) -> List[Polygon]:
        """Extract interior rings as individual Polygon objects."""
        return [Polygon(interior) for interior in polygon.interiors]

    @staticmethod
    def topology_validate(polygon: Polygon) -> Dict[str, Any]:
        """Validates topological validity of a polygon geometry."""
        is_valid = polygon.is_valid
        reason = getattr(polygon, "validity_reason", "Valid Geometry") if not is_valid else "Valid Geometry"
        return {
            "is_valid": is_valid,
            "is_simple": polygon.is_simple,
            "is_empty": polygon.is_empty,
            "reason": reason
        }

    @staticmethod
    def coordinate_normalize(polygon: Polygon) -> Polygon:
        """Translates polygon so its minimum bounding box corner is at origin (0, 0)."""
        minx, miny, _, _ = polygon.bounds
        return affinity.translate(polygon, xoff=-minx, yoff=-miny)

