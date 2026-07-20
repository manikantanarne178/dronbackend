"""
Measurement Module

Provides reusable geometric measurement utilities.

Features
--------
- Point-to-point distance
- Height difference
- Polygon area (3D)
- Polyline length
- Bounding box dimensions
- Future interactive measurement support
"""

from __future__ import annotations

import numpy as np
import trimesh


# ------------------------------------------------------------
# Euclidean Distance
# ------------------------------------------------------------
def length_factor(unit: str = "m"):
    return 100.0 if unit.lower() == "cm" else 1.0


def area_factor(unit: str = "m"):
    return 10000.0 if unit.lower() == "cm" else 1.0


def volume_factor(unit: str = "m"):
    return 1000000.0 if unit.lower() == "cm" else 1.0
def distance(point1, point2, unit="m") -> float:

    p1 = np.asarray(point1, dtype=float)
    p2 = np.asarray(point2, dtype=float)

    return float(np.linalg.norm(p2 - p1) * length_factor(unit))
    """
    Distance between two 3D points.

    Parameters
    ----------
    point1 : [x,y,z]
    point2 : [x,y,z]
    """

    p1 = np.asarray(point1, dtype=float)
    p2 = np.asarray(point2, dtype=float)

    return float(np.linalg.norm(p2 - p1))


# ------------------------------------------------------------
# Height Difference
# ------------------------------------------------------------

def height_difference(point1, point2, unit="m") -> float:

    return float(abs(point2[2] - point1[2]) * length_factor(unit))


# ------------------------------------------------------------
# Polyline Length
# ------------------------------------------------------------

def polyline_length(points, unit="m"):

    if len(points) < 2:
        return 0.0

    total = 0.0

    for i in range(len(points)-1):
        total += distance(points[i], points[i+1], unit)

    return float(total)


# ------------------------------------------------------------
# Polygon Area (Projected XY)
# ------------------------------------------------------------

def polygon_area(points):
    """
    Area of polygon projected on XY plane.

    Uses Shoelace Formula.
    """

    pts = np.asarray(points, dtype=float)

    if len(pts) < 3:
        return 0.0

    x = pts[:, 0]
    y = pts[:, 1]

    area = 0.5 * np.abs(
        np.dot(x, np.roll(y, -1))
        - np.dot(y, np.roll(x, -1))
    )

    return float(area)


# ------------------------------------------------------------
# Bounding Box Dimensions
# ------------------------------------------------------------

def bounding_box_dimensions(mesh: trimesh.Trimesh):
    """
    Width, Length, Height from mesh.
    """

    bounds = mesh.bounds

    size = bounds[1] - bounds[0]

    return {
        "width": float(size[0]),
        "length": float(size[1]),
        "height": float(size[2]),
    }


# ------------------------------------------------------------
# Mesh Height Range
# ------------------------------------------------------------

def height_range(mesh: trimesh.Trimesh):
    """
    Minimum and maximum elevations.
    """

    z = mesh.vertices[:, 2]

    return {
        "min_height": float(z.min()),
        "max_height": float(z.max()),
        "height_difference": float(z.max() - z.min()),
    }


# ------------------------------------------------------------
# Bounding Box Corners
# ------------------------------------------------------------

def bounding_box_corners(mesh: trimesh.Trimesh):
    """
    Returns bounding box corners.
    """

    return mesh.bounding_box.vertices.tolist()


# ------------------------------------------------------------
# Future Interactive Measurement
# ------------------------------------------------------------

def measure_between_points(start_point, end_point):
    """
    Returns all measurements between two picked points.

    This will be called by FastAPI after receiving
    coordinates from the React viewer.
    """

    return {

        "distance": distance(start_point, end_point),

        "height_difference": height_difference(
            start_point,
            end_point,
        ),

        "start": list(start_point),

        "end": list(end_point),
    }


# ------------------------------------------------------------
# Future Polygon Measurement
# ------------------------------------------------------------

def measure_polygon(points):
    """
    Measure area and perimeter of a polygon.
    """

    perimeter = polyline_length(points + [points[0]])

    area = polygon_area(points)

    return {

        "area": area,

        "perimeter": perimeter,

        "vertices": len(points),
    }


# ------------------------------------------------------------
# CLI Test
# ------------------------------------------------------------

if __name__ == "__main__":

    p1 = [0, 0, 0]
    p2 = [4, 3, 5]

    print("Distance:", distance(p1, p2))
    print("Height:", height_difference(p1, p2))

    polygon = [
        [0, 0, 0],
        [5, 0, 0],
        [5, 4, 0],
        [0, 4, 0],
    ]

    print(measure_polygon(polygon))