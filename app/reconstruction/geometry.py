"""
Geometry Analysis Module

Provides professional measurements for reconstructed meshes.

Calculates

- Bounding Box
- Width
- Length
- Height
- Ground Area
- Surface Area
- Volume
- Vertex Count
- Triangle Count
"""

import numpy as np
import trimesh


# ------------------------------------------------------------
# Bounding Box
# ------------------------------------------------------------

def bounding_box(mesh: trimesh.Trimesh):

    bounds = mesh.bounds

    minimum = bounds[0]
    maximum = bounds[1]

    size = maximum - minimum

    return {
        "min": minimum.tolist(),
        "max": maximum.tolist(),
        "size": size.tolist()
    }


# ------------------------------------------------------------
# Width Length Height
# ------------------------------------------------------------

def dimensions(mesh: trimesh.Trimesh):

    bounds = mesh.bounds

    minimum = bounds[0]
    maximum = bounds[1]

    size = maximum - minimum

    return {
        "width": float(size[0]),
        "length": float(size[1]),
        "height": float(size[2])
    }


# ------------------------------------------------------------
# Center
# ------------------------------------------------------------

def center(mesh: trimesh.Trimesh):

    return mesh.bounding_box.centroid.tolist()


# ------------------------------------------------------------
# Surface Area
# ------------------------------------------------------------

def surface_area(mesh: trimesh.Trimesh):

    return float(mesh.area)


# ------------------------------------------------------------
# Ground Area
# ------------------------------------------------------------

def ground_area(mesh: trimesh.Trimesh):

    bounds = mesh.bounds

    size = bounds[1] - bounds[0]

    return float(size[0] * size[1])


# ------------------------------------------------------------
# Volume
# ------------------------------------------------------------

def volume(mesh: trimesh.Trimesh):

    if mesh.is_watertight:
        return float(mesh.volume)

    return 0.0


# ------------------------------------------------------------
# Vertex Count
# ------------------------------------------------------------

def vertex_count(mesh: trimesh.Trimesh):

    return int(len(mesh.vertices))


# ------------------------------------------------------------
# Triangle Count
# ------------------------------------------------------------

def triangle_count(mesh: trimesh.Trimesh):

    return int(len(mesh.faces))


# ------------------------------------------------------------
# Complete Geometry Statistics
# ------------------------------------------------------------

def geometry_statistics(mesh: trimesh.Trimesh):

    return {

        "bounding_box": bounding_box(mesh),

        "dimensions": dimensions(mesh),

        "center": center(mesh),

        "surface_area": surface_area(mesh),

        "ground_area": ground_area(mesh),

        "volume": volume(mesh),

        "vertex_count": vertex_count(mesh),

        "triangle_count": triangle_count(mesh)

    }