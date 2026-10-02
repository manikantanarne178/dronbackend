import os
from pathlib import Path
import trimesh
import open3d as o3d
import numpy as np

def convert_to_glb(mesh_path: str, project_dir: str) -> str:
    """
    Convert a 3D mesh or point cloud (.ply / .obj) to standard .glb binary format.
    Uses native Python trimesh & open3d (cross-platform, zero external blender dependencies).
    """
    input_file = Path(mesh_path)
    if not input_file.exists():
        raise FileNotFoundError(f"3D Model input file not found: {mesh_path}")

    out_dir = Path(project_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    glb_path = out_dir / "model.glb"

    print(f"Converting 3D asset {input_file.name} to GLB at {glb_path}...")

    try:
        # Load mesh via trimesh
        loaded = trimesh.load(str(input_file))
        if isinstance(loaded, trimesh.Scene):
            # Scene with multiple geometries
            loaded.export(str(glb_path), file_type="glb")
        elif isinstance(loaded, trimesh.Trimesh):
            loaded.export(str(glb_path), file_type="glb")
        elif isinstance(loaded, trimesh.PointCloud):
            # Convert Point Cloud to small spheres or direct export
            scene = trimesh.Scene(geometry=[loaded])
            scene.export(str(glb_path), file_type="glb")
        else:
            # Fallback open3d
            pcd = o3d.io.read_point_cloud(str(input_file))
            if len(pcd.points) > 0:
                # Estimate normals and reconstruct surface via Poisson or Ball Pivoting
                pcd.estimate_normals()
                radii = [0.005, 0.01, 0.02, 0.04]
                mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                    pcd, o3d.utility.DoubleVector(radii)
                )
                temp_obj = out_dir / "temp_mesh.obj"
                o3d.io.write_triangle_mesh(str(temp_obj), mesh)
                tm = trimesh.load(str(temp_obj))
                tm.export(str(glb_path), file_type="glb")
                temp_obj.unlink(missing_ok=True)
            else:
                loaded.export(str(glb_path), file_type="glb")

    except Exception as e:
        print(f"Trimesh export notice: {e}, falling back to direct GLTF scene packaging...")
        # Direct raw scene packaging fallback
        mesh = trimesh.load(str(input_file), force="mesh")
        mesh.export(str(glb_path), file_type="glb")

    if glb_path.exists():
        print(f"GLB model generated successfully: {glb_path.stat().st_size} bytes")
        return str(glb_path)

    raise RuntimeError(f"Failed to generate GLB from {mesh_path}")
