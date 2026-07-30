"""
Directional Setback Calculation Service for AutoDCR.
Calculates exact directional setback clearances (Front, Rear, Left, Right, Corner Plot Setbacks)
from building boundary to corresponding plot boundary edges.
"""

from typing import Dict, Any, List, Tuple
from shapely.geometry import Polygon, LineString, Point


class SetbackService:

    @staticmethod
    def calculate(plot: Dict[str, Any], building: Dict[str, Any], road: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculates exact directional setbacks for Front, Rear, Left, and Right edges.
        """
        if not plot or not building or "points" not in plot or "points" not in building:
            return {"front": 0.0, "rear": 0.0, "left": 0.0, "right": 0.0}

        plot_pts = plot["points"]
        bldg_pts = building["points"]

        if len(plot_pts) < 3 or len(bldg_pts) < 3:
            return {"front": 0.0, "rear": 0.0, "left": 0.0, "right": 0.0}

        try:
            plot_poly = Polygon(plot_pts)
            bldg_poly = Polygon(bldg_pts)

            # Determine road-facing direction
            road_dir = "north"
            if road and isinstance(road, dict) and road.get("direction"):
                road_dir = str(road.get("direction")).lower()

            # Directional mapping vectors
            dir_vectors = {
                "north": (0, 1),
                "south": (0, -1),
                "east": (1, 0),
                "west": (-1, 0)
            }

            # Opposite & side directions
            opposite_map = {"north": "south", "south": "north", "east": "west", "west": "east"}
            left_map = {"north": "west", "south": "east", "east": "north", "west": "south"}
            right_map = {"north": "east", "south": "west", "east": "south", "west": "north"}

            front_dir = road_dir
            rear_dir = opposite_map.get(front_dir, "south")
            left_dir = left_map.get(front_dir, "west")
            right_dir = right_map.get(front_dir, "east")

            # Extract plot boundary segments and compute distance to building for each side
            plot_lines = SetbackService._extract_oriented_lines(plot_pts, plot_poly.centroid)

            setbacks = {
                "front": SetbackService._min_distance_in_direction(bldg_poly, plot_lines.get(front_dir, [])),
                "rear": SetbackService._min_distance_in_direction(bldg_poly, plot_lines.get(rear_dir, [])),
                "left": SetbackService._min_distance_in_direction(bldg_poly, plot_lines.get(left_dir, [])),
                "right": SetbackService._min_distance_in_direction(bldg_poly, plot_lines.get(right_dir, []))
            }

            return {
                "front": round(float(setbacks["front"]), 3),
                "rear": round(float(setbacks["rear"]), 3),
                "left": round(float(setbacks["left"]), 3),
                "right": round(float(setbacks["right"]), 3)
            }
        except Exception:
            # Safe minimum distance computation fallback if geometry is degenerate
            dist = float(Polygon(bldg_pts).distance(Polygon(plot_pts)))
            return {"front": round(dist, 3), "rear": round(dist, 3), "left": round(dist, 3), "right": round(dist, 3)}

    @staticmethod
    def _extract_oriented_lines(points: List[Tuple[float, float]], centroid: Point) -> Dict[str, List[LineString]]:
        """
        Classifies plot edges into cardinal orientation buckets (north, south, east, west) relative to centroid.
        """
        lines_by_dir: Dict[str, List[LineString]] = {"north": [], "south": [], "east": [], "west": []}

        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            edge = LineString([p1, p2])
            mid_x = (p1[0] + p2[0]) / 2.0
            mid_y = (p1[1] + p2[1]) / 2.0

            dx = mid_x - centroid.x
            dy = mid_y - centroid.y

            if abs(dx) >= abs(dy):
                d = "east" if dx > 0 else "west"
            else:
                d = "north" if dy > 0 else "south"

            lines_by_dir[d].append(edge)

        return lines_by_dir

    @staticmethod
    def _min_distance_in_direction(bldg_poly: Polygon, plot_lines: List[LineString]) -> float:
        """
        Calculates minimum clearance distance from building polygon to a set of plot edge lines.
        """
        if not plot_lines:
            return 1.0  # Default safe distance if line bucket empty

        min_dist = float("inf")
        for line in plot_lines:
            d = bldg_poly.distance(line)
            if d < min_dist:
                min_dist = d

        return min_dist if min_dist != float("inf") else 0.0