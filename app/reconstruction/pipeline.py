from app.reconstruction.colmap import run_colmap
from app.reconstruction.converter import convert_to_glb


def run_pipeline():
    try:
        print("=" * 60)
        print("Starting 3D Reconstruction Pipeline")
        print("=" * 60)

        # COLMAP + OpenMVS
        mesh = run_colmap()
        print("=" * 60)
        print("Returned mesh:", mesh)
        print("=" * 60)
        print("\nConverting mesh to GLB...\n")

        glb = convert_to_glb(mesh)

        print("\nPipeline completed successfully.\n")

        return {
            "success": True,
            "mesh": mesh,
            "glb": glb,
        }

    except Exception as e:
        print("\nPipeline failed!")
        print(e)
        raise