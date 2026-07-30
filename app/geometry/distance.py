"""
Distance utilities module for AutoDCR Geometry Engine.
Provides Shapely-based distance calculations without duplicating DistanceService API.
"""

from typing import Tuple, List, Union
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points


class DistanceCalculator:
    """
    Shapely-backed distance calculation engine for geometric entities.
    """

    @staticmethod
    def point_to_point(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Euclidean distance between two 2D points."""
        return Point(p1).distance(Point(p2))

    @staticmethod
    def point_to_line(point: Tuple[float, float], line_points: List[Tuple[float, float]]) -> float:
        """Minimum distance from a point to a line or polyline."""
        if len(line_points) < 2:
            return 0.0
        return Point(point).distance(LineString(line_points))

    @staticmethod
    def polygon_to_polygon(poly1: Polygon, poly2: Polygon) -> float:
        """Minimum clearance / distance between two polygons."""
        return poly1.distance(poly2)

    @staticmethod
    def hausdorff_distance(poly1: Polygon, poly2: Polygon) -> float:
        """Hausdorff distance between two polygons."""
        return poly1.hausdorff_distance(poly2)

    @staticmethod
    def nearest_points_between(poly1: Polygon, poly2: Polygon) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Returns the pair of nearest points between two geometries."""
        p1, p2 = nearest_points(poly1, poly2)
        return ((p1.x, p1.y), (p2.x, p2.y))
