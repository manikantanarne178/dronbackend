from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh


def compute_mesh_analytics(mesh_path) -> dict:
    """
    Compute analytics for a mesh file (.ply, .obj, or .glb).

    Returns a dict with:
        vertices        int
        triangles       int
        bounding_box    {min: [x,y,z], max: [x,y,z]}
        width            float  (X extent)
        height           float  (Y extent)
        depth            float  (Z extent)
        surface_area     float
        volume           float  (0.0 if mesh is not watertight)
        is_watertight    bool

    Uses Open3D for topology-safe metrics (vertex/triangle counts,
    bounding box) and trimesh for surface area / volume, since
    trimesh's volume computation correctly returns 0 / raises for
    non-watertight meshes rather than silently returning garbage.
    """

    mesh_path = Path(mesh_path)

    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh not found:\n{mesh_path}")

    o3d_mesh = o3d.io.read_triangle_mesh(str(mesh_path))

    if o3d_mesh.is_empty():
        raise RuntimeError(f"Mesh at {mesh_path} is empty; cannot compute analytics.")

    vertices = np.asarray(o3d_mesh.vertices)
    triangles = np.asarray(o3d_mesh.triangles)

    n_vertices = vertices.shape[0]
    n_triangles = triangles.shape[0]

    bbox_min = vertices.min(axis=0)
    bbox_max = vertices.max(axis=0)
    extent = bbox_max - bbox_min

    width = float(extent[0])
    height = float(extent[1])
    depth = float(extent[2])

    # trimesh for surface area / volume -- more robust watertight
    # handling than Open3D's get_volume(), which throws on
    # non-manifold meshes rather than gracefully reporting 0.
    tm = trimesh.load(str(mesh_path), process=False, force="mesh")

    surface_area = float(tm.area) if tm is not None else 0.0

    is_watertight = bool(tm.is_watertight) if tm is not None else False
    if is_watertight:
        try:
            volume = float(abs(tm.volume))
        except Exception:
            volume = 0.0
    else:
        volume = 0.0

    return {
        "vertices": int(n_vertices),
        "triangles": int(n_triangles),
        "bounding_box": {
            "min": [float(bbox_min[0]), float(bbox_min[1]), float(bbox_min[2])],
            "max": [float(bbox_max[0]), float(bbox_max[1]), float(bbox_max[2])],
        },
        "width": width,
        "height": height,
        "depth": depth,
        "surface_area": surface_area,
        "volume": volume,
        "is_watertight": is_watertight,
    }