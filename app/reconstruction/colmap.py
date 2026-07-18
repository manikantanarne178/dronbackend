import os
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

UPLOADS = Path("app/uploads/images").resolve()
OUTPUTS = Path("app/outputs").resolve()

COLMAP_WORKSPACE = (OUTPUTS / "colmap").resolve()
OPENMVS_WORKSPACE = (OUTPUTS / "openmvs").resolve()

COLMAP = r"C:\colmap-x64-windows-nocuda\bin\colmap.exe"

OPENMVS_BIN = Path(
    r"C:\OpenMVS_Windows_x64\vc17\x64\Release"
)

INTERFACE_COLMAP = OPENMVS_BIN / "InterfaceCOLMAP.exe"
DENSIFY = OPENMVS_BIN / "DensifyPointCloud.exe"
RECONSTRUCT = OPENMVS_BIN / "ReconstructMesh.exe"
REFINE = OPENMVS_BIN / "RefineMesh.exe"
TEXTURE = OPENMVS_BIN / "TextureMesh.exe"

DATABASE = (COLMAP_WORKSPACE / "database.db").resolve()
SPARSE = (COLMAP_WORKSPACE / "sparse").resolve()
DENSE = (COLMAP_WORKSPACE / "dense").resolve()
SCENE = (OPENMVS_WORKSPACE / "scene.mvs").resolve()

OUTPUTS.mkdir(parents=True, exist_ok=True)
COLMAP_WORKSPACE.mkdir(parents=True, exist_ok=True)
OPENMVS_WORKSPACE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def run(cmd, cwd=None):

    print("\n===================================")
    print("RUNNING")
    print(" ".join(map(str, cmd)))
    print("===================================\n")

    env = os.environ.copy()

    env["PATH"] = (
        str(OPENMVS_BIN) + ";" +
        r"C:\colmap-x64-windows-nocuda\bin;" +
        env["PATH"]
    )

    env["QT_PLUGIN_PATH"] = r"C:\colmap-x64-windows-nocuda\plugins"

    result = subprocess.run(
        list(map(str, cmd)),
        env=env,
        cwd=cwd,
        text=True,
        capture_output=True
    )

    print(result.stdout)
    print(result.stderr)

    result.check_returncode()


# ---------------------------------------------------------
# Clean Workspace
# ---------------------------------------------------------

def prepare_workspace():

    if DATABASE.exists():
        DATABASE.unlink()

    if SPARSE.exists():
        shutil.rmtree(SPARSE)

    if DENSE.exists():
        shutil.rmtree(DENSE)

    if OPENMVS_WORKSPACE.exists():
        shutil.rmtree(OPENMVS_WORKSPACE)

    SPARSE.mkdir(parents=True)
    DENSE.mkdir(parents=True)
    OPENMVS_WORKSPACE.mkdir(parents=True)


# ---------------------------------------------------------
# COLMAP Sparse Reconstruction + OpenMVS Dense Pipeline
# ---------------------------------------------------------

def run_colmap():
    print("UPLOADS:", UPLOADS)
    print("COLMAP_WORKSPACE:", COLMAP_WORKSPACE)
    print("DENSE:", DENSE)
    print("OPENMVS:", OPENMVS_WORKSPACE)

    prepare_workspace()

    print("\nSTEP 1 : Feature Extraction\n")
    run([
        COLMAP,
        "feature_extractor",
        "--database_path", DATABASE,
        "--image_path", UPLOADS
    ])

    print("\nSTEP 2 : Feature Matching\n")
    run([
        COLMAP,
        "exhaustive_matcher",
        "--database_path", DATABASE
    ])

    print("\nSTEP 3 : Sparse Reconstruction\n")
    run([
        COLMAP,
        "mapper",
        "--database_path", DATABASE,
        "--image_path", UPLOADS,
        "--output_path", SPARSE
    ])

    sparse_model = SPARSE / "0"

    if not sparse_model.exists():
        raise RuntimeError(
            "COLMAP failed to create sparse model."
        )

    print("\nSTEP 4 : Image Undistortion\n")
    run([
        COLMAP,
        "image_undistorter",
        "--image_path", UPLOADS,
        "--input_path", sparse_model,
        "--output_path", DENSE,
        "--output_type", "COLMAP"
    ])

    # ----- PART 2 STARTS HERE -----
    print("\nSTEP 5 : Convert COLMAP -> OpenMVS\n")
    run([
        INTERFACE_COLMAP,
        "-i", DENSE.resolve(),
        "-o", SCENE.resolve(),
        "-w", OPENMVS_WORKSPACE.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    if not SCENE.exists():
        raise RuntimeError("InterfaceCOLMAP failed.")

    print("\nSTEP 6 : Densify Point Cloud\n")
    run([
        DENSIFY,
        "-i", SCENE.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    dense_scene = OPENMVS_WORKSPACE / "scene_dense.mvs"

    if not dense_scene.exists():
        dense_scene = SCENE

    print("\nSTEP 7 : Reconstruct Mesh\n")

    mesh_scene = OPENMVS_WORKSPACE / "scene_dense_mesh.mvs"
    mesh_ply = OPENMVS_WORKSPACE / "scene_dense_mesh.ply"

    run([
        RECONSTRUCT,
        "-i", dense_scene.resolve(),
        "-o", mesh_scene.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    # Some OpenMVS builds only generate the PLY mesh.
    if not mesh_scene.exists():
     if mesh_ply.exists():
        print("\n===================================")
        print("Mesh reconstructed successfully.")
        print(mesh_ply)
        print("Skipping RefineMesh and TextureMesh.")
        print("===================================\n")

        return str(mesh_ply)

    raise RuntimeError("Mesh reconstruction failed.")

    print("\nSTEP 8 : Refine Mesh\n")

    refined_scene = OPENMVS_WORKSPACE / "scene_dense_mesh_refine.mvs"

    run([
        REFINE,
        "-i", mesh_scene.resolve(),
        "-o", refined_scene.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    if refined_scene.exists():
        mesh_scene = refined_scene

    print("\nSTEP 9 : Texture Mesh\n")

    textured_scene = OPENMVS_WORKSPACE / "scene_dense_mesh_refine_texture.mvs"

    run([
        TEXTURE,
        "-i", mesh_scene.resolve(),
        "-o", textured_scene.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    if textured_scene.exists():
        mesh_scene = textured_scene

    obj = OPENMVS_WORKSPACE / "scene_dense_mesh_refine_texture.obj"

    if not obj.exists():
        obj = OPENMVS_WORKSPACE / "scene_dense_mesh_refine.obj"

    if not obj.exists():
        obj = OPENMVS_WORKSPACE / "scene_dense_mesh.obj"

    if not obj.exists():
        raise RuntimeError("OBJ model was not created.")

    print("\n===================================")
    print("3D Reconstruction Completed")
    print(obj)
    print("===================================\n")

    return str(obj)


if __name__ == "__main__":
    run_colmap()