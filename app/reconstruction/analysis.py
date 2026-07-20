"""
Mesh Analysis Module

Loads a reconstructed mesh (OBJ/GLB/PLY),
performs geometric analysis,
and returns a complete metadata dictionary.
"""

from pathlib import Path
import trimesh

from app.reconstruction.geometry import geometry_statistics


# ------------------------------------------------------------
# Load Mesh
# ------------------------------------------------------------

def load_mesh(model_path: str | Path) -> trimesh.Trimesh:
    """
    Load a mesh from disk.

    Supports:
    - GLB
    - GLTF
    - OBJ
    - PLY
    """

    model_path = Path(model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    mesh = trimesh.load(model_path)

    # Some GLBs load as Scene instead of Trimesh
    if isinstance(mesh, trimesh.Scene):

        if len(mesh.geometry) == 0:
            raise RuntimeError("Scene contains no geometry.")

        mesh = trimesh.util.concatenate(
            tuple(mesh.geometry.values())
        )

    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("Unable to load mesh.")

    return mesh


# ------------------------------------------------------------
# Analyze Mesh
# ------------------------------------------------------------

def analyze_mesh(model_path: str | Path):
    """
    Analyze reconstructed mesh.

    Returns:
        Dictionary containing
        - dimensions
        - area
        - volume
        - bounding box
        - statistics
    """

    mesh = load_mesh(model_path)

    stats = geometry_statistics(mesh)

    metadata = {

        "file": str(model_path),

        "vertices": stats["vertex_count"],

        "triangles": stats["triangle_count"],

        "bounding_box": stats["bounding_box"],

        "dimensions": stats["dimensions"],

        "center": stats["center"],

        "ground_area": stats["ground_area"],

        "surface_area": stats["surface_area"],

        "volume": stats["volume"]

    }

    return metadata


# ------------------------------------------------------------
# CLI Test
# ------------------------------------------------------------

if __name__ == "__main__":

    model = "app/outputs/model.glb"

    metadata = analyze_mesh(model)

    from pprint import pprint

    pprint(metadata)