import os
import shutil
import subprocess
import glob
from pathlib import Path
from importlib_metadata import files
import open3d as o3d
import cv2
import numpy as np

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

UPLOADS = Path("app/uploads/images").resolve()
OUTPUTS = Path("app/outputs").resolve()

COLMAP_WORKSPACE = (OUTPUTS / "colmap").resolve()
OPENMVS_WORKSPACE = (OUTPUTS / "openmvs").resolve()

# Working copy of the image set actually fed to COLMAP.
WORK_IMAGES = (COLMAP_WORKSPACE / "images_padded").resolve()

COLMAP = r"C:\colmap-x64-windows-nocuda\bin\colmap.exe"
OPENMVS_BIN = Path(r"C:\OpenMVS_Windows_x64\vc17\x64\Release")

INTERFACE_COLMAP = OPENMVS_BIN / "InterfaceCOLMAP.exe"
DENSIFY = OPENMVS_BIN / "DensifyPointCloud.exe"
RECONSTRUCT = OPENMVS_BIN / "ReconstructMesh.exe"
REFINE = OPENMVS_BIN / "RefineMesh.exe"
TEXTURE = OPENMVS_BIN / "TextureMesh.exe"

DATABASE = (COLMAP_WORKSPACE / "database.db").resolve()
SPARSE = (COLMAP_WORKSPACE / "sparse").resolve()
DENSE = (COLMAP_WORKSPACE / "dense").resolve()
SCENE = (OPENMVS_WORKSPACE / "scene.mvs").resolve()

# Minimum number of images we want COLMAP to see. Fewer real images
# get padded out with optical-flow interpolated in-between frames.
MIN_IMAGES = 10

# Synthetic frames help COLMAP's sparse matcher bridge gaps between
# widely-spaced real photos, but can hurt dense MVS quality since
# they have no genuine 3D viewpoint. Turn off if dense results look
# thin/noisy and you have decent overlap in your real photos.
ENABLE_SYNTHETIC_PADDING = False

# Below this many dense points, ReconstructMesh will produce a
# degenerate/empty mesh after its own cleanup pass. Fail fast here
# instead of burning 10-20 minutes to hit that downstream.
MIN_DENSE_POINTS = 50

OUTPUTS.mkdir(parents=True, exist_ok=True)
COLMAP_WORKSPACE.mkdir(parents=True, exist_ok=True)
OPENMVS_WORKSPACE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Helper: run a subprocess and surface REAL errors
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
        list(map(str, cmd)), env=env, cwd=cwd, text=True, capture_output=True
    )

    print(result.stdout)
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({' '.join(map(str, cmd))}).\n"
            f"--- STDOUT ---\n{result.stdout}\n"
            f"--- STDERR ---\n{result.stderr}\n"
        )


def count_ply_elements(ply_path, element_name="vertex"):
    """Read the vertex/point count out of a PLY header without a
    full PLY parsing library."""
    try:
        with open(ply_path, "rb") as f:
            count = None
            for _ in range(200):  # PLY headers are short
                line = f.readline()
                if not line:
                    break
                text = line.decode("ascii", errors="ignore").strip()
                if text.startswith(f"element {element_name}"):
                    count = int(text.split()[-1])
                if text == "end_header":
                    break
            return count
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------
# Clean Workspace
# ---------------------------------------------------------

def prepare_workspace():
    print("\nAfter cleanup:")
    print("WORK_IMAGES:", WORK_IMAGES)

    files = list(WORK_IMAGES.glob("*"))
    print("Files after cleanup:", len(files))
    if DATABASE.exists():
        DATABASE.unlink()
    if SPARSE.exists():
        shutil.rmtree(SPARSE)
    if DENSE.exists():
        shutil.rmtree(DENSE)
    if WORK_IMAGES.exists():
        shutil.rmtree(WORK_IMAGES)
    if OPENMVS_WORKSPACE.exists():
        shutil.rmtree(OPENMVS_WORKSPACE)

    SPARSE.mkdir(parents=True)
    DENSE.mkdir(parents=True)
    WORK_IMAGES.mkdir(parents=True)
    OPENMVS_WORKSPACE.mkdir(parents=True)


# ---------------------------------------------------------
# Pad a small image set up to MIN_IMAGES using optical-flow
# interpolation between consecutive photos. Doesn't invent new 3D
# geometry -- just gives COLMAP's matcher more continuity between
# widely-spaced viewpoints.
# ---------------------------------------------------------

def interpolate_frame(img1, img2, alpha):
    """Blend img1 -> img2 at position alpha (0..1) using dense
    optical flow warping, falling back to cross-dissolve on failure."""
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    try:
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )

        h, w = gray1.shape
        grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))

        map_x = (grid_x + flow[..., 0] * alpha).astype(np.float32)
        map_y = (grid_y + flow[..., 1] * alpha).astype(np.float32)
        warped1 = cv2.remap(img1, map_x, map_y, cv2.INTER_LINEAR)

        map_x2 = (grid_x - flow[..., 0] * (1 - alpha)).astype(np.float32)
        map_y2 = (grid_y - flow[..., 1] * (1 - alpha)).astype(np.float32)
        warped2 = cv2.remap(img2, map_x2, map_y2, cv2.INTER_LINEAR)

        return cv2.addWeighted(warped1, 1 - alpha, warped2, alpha, 0)
    except cv2.error:
        return cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)


def pad_image_set(image_paths, min_images=MIN_IMAGES):
    files = list(WORK_IMAGES.glob("*"))

    print("\nWORK_IMAGES contains:")
    print(len(files))

    for f in files:
     print(f.name)
    image_paths = sorted(image_paths)

    if len(image_paths) == 0:
        raise RuntimeError("No images were uploaded.")

    for i, p in enumerate(image_paths):
        dst = WORK_IMAGES / f"real_{i:03d}{Path(p).suffix.lower()}"
        shutil.copy(p, dst)

    if len(image_paths) >= min_images or not ENABLE_SYNTHETIC_PADDING:
        if len(image_paths) < min_images:
            print(
                f"Only {len(image_paths)} real image(s) uploaded "
                f"(target {min_images}) and synthetic padding is "
                f"disabled. Proceeding with real images only."
            )
        return

    if len(image_paths) < 2:
        raise RuntimeError(
            "Need at least 2 images to attempt reconstruction, and 2 "
            "is only barely enough -- results will likely be a sparse "
            "point cloud at best, not a full mesh."
        )

    needed = min_images - len(image_paths)
    gaps = len(image_paths) - 1
    per_gap = max(1, -(-needed // gaps))  # ceil division

    synth_index = 0
    for i in range(gaps):
        img1 = cv2.imread(str(image_paths[i]))
        img2 = cv2.imread(str(image_paths[i + 1]))
        if img1 is None or img2 is None:
            continue
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        for k in range(1, per_gap + 1):
            alpha = k / (per_gap + 1)
            frame = interpolate_frame(img1, img2, alpha)
            out_path = WORK_IMAGES / f"synth_{i:03d}_{k:03d}.jpg"
            cv2.imwrite(str(out_path), frame)
            synth_index += 1

    total = len(list(WORK_IMAGES.glob("*")))
    print(f"Padded image set: {len(image_paths)} real + "
          f"{synth_index} synthetic = {total} total images "
          f"(target was {min_images}).")


# ---------------------------------------------------------
# COLMAP Sparse Reconstruction + OpenMVS Dense Pipeline
# ---------------------------------------------------------

def run_colmap():
    print("UPLOADS:", UPLOADS)
    print("COLMAP_WORKSPACE:", COLMAP_WORKSPACE)
    print("DENSE:", DENSE)
    print("OPENMVS:", OPENMVS_WORKSPACE)

    prepare_workspace()

    uploaded = sorted(
    str(p)
    for p in UPLOADS.iterdir()
    if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
)

    if len(uploaded) == 0:
        raise RuntimeError(f"No images found in {UPLOADS}")

    n_real = len(uploaded)
    print(f"Found {n_real} uploaded image(s).")
    print("\nImages passed to COLMAP:")

    for img in uploaded:
     print(Path(img).name)

    print("Total:", len(uploaded))

    pad_image_set(uploaded, min_images=MIN_IMAGES)

    print("\nSTEP 1 : Feature Extraction\n")
    run([
        COLMAP, "feature_extractor",
        "--database_path", DATABASE,
        "--image_path", WORK_IMAGES,
        "--ImageReader.single_camera", "1"
    ])

    print("\nSTEP 2 : Feature Matching\n")
    run([COLMAP, "exhaustive_matcher", "--database_path", DATABASE])

    print("\nSTEP 3 : Sparse Reconstruction\n")
    run([
        COLMAP, "mapper",
        "--database_path", DATABASE,
        "--image_path", WORK_IMAGES,
        "--output_path", SPARSE,
        "--Mapper.min_num_matches", "5",
        "--Mapper.abs_pose_min_num_inliers", "5",
        "--Mapper.init_min_num_inliers", "10"
    ])

    sparse_model = SPARSE / "0"
    if not sparse_model.exists():
        raise RuntimeError(
            "COLMAP failed to create a sparse model even after "
            "padding to the minimum image count. This usually means "
            "the real photos don't overlap enough for feature "
            "matching to register any cameras. Try photos/frames "
            "with more overlap (60-80%) between consecutive shots."
        )

    print("\nSTEP 4 : Image Undistortion\n")
    run([
        COLMAP, "image_undistorter",
        "--image_path", WORK_IMAGES,
        "--input_path", sparse_model,
        "--output_path", DENSE,
        "--output_type", "COLMAP"
    ])
    print("\nSTEP 5 : Patch Match Stereo\n")

#     run([
#     COLMAP,
#     "patch_match_stereo",
#     "--workspace_path", DENSE,
#     "--workspace_format", "COLMAP"
# ])
#     print("\nSTEP 6 : Stereo Fusion\n")

#     run([
#     COLMAP,
#     "stereo_fusion",
#     "--workspace_path", DENSE,
#     "--workspace_format", "COLMAP",
#     "--output_path", DENSE / "fused.ply"
# ])
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
    run([DENSIFY, "-i", SCENE.resolve()], cwd=OPENMVS_WORKSPACE)

    dense_scene = OPENMVS_WORKSPACE / "scene_dense.mvs"
    dense_ply = OPENMVS_WORKSPACE / "scene_dense.ply"

    if not dense_scene.exists():
        dense_scene = SCENE

    n_points = count_ply_elements(dense_ply, "vertex") if dense_ply.exists() else 0
    print(f"Dense point cloud: {n_points} points")
    if n_points < MIN_DENSE_POINTS:
        hint = (
            " Synthetic padding is currently ON -- try turning "
            "ENABLE_SYNTHETIC_PADDING off and re-running with "
            "just your real photos, since interpolated frames "
            "can confuse dense multi-view stereo."
            if ENABLE_SYNTHETIC_PADDING else
            " Try capturing more real photos/frames with 60-80% "
            "overlap between consecutive shots."
        )
        if n_real > 4:
            # With enough images, low dense points means a real coverage
            # problem -- fail fast rather than waste time on meshing.
            raise RuntimeError(
                f"Dense reconstruction only produced {n_points} points "
                f"(need at least {MIN_DENSE_POINTS}). This usually "
                f"means the source images don't have enough "
                f"consistent overlap for multi-view stereo to agree "
                f"on depth.{hint}"
            )
        else:
            # With <= 4 images, DensifyPointCloud routinely produces 0
            # dense points because depth-map fusion needs more stereo
            # views. The 117-point COLMAP sparse cloud is enough for
            # ReconstructMesh to build a basic mesh -- continue.
            print(
                f"WARNING: DensifyPointCloud produced only {n_points} dense "
                f"points with {n_real} image(s). This is normal for very small "
                f"image sets. Continuing with the sparse COLMAP point cloud.{hint}"
            )

    print("\nSTEP 7 : Reconstruct Mesh\n")

    mesh_scene = OPENMVS_WORKSPACE / "scene_dense_mesh.mvs"
    mesh_ply = OPENMVS_WORKSPACE / "scene_dense_mesh.ply"

    run([
        RECONSTRUCT,
        "-i", dense_scene.resolve(),
        "-o", mesh_scene.resolve()
    ], cwd=OPENMVS_WORKSPACE)

    # NOTE: on some OpenMVS builds, ReconstructMesh writes the mesh
    # geometry to .ply but does NOT re-embed it into a .mvs scene,
    # even though exit code is 0 and -o was given. Don't treat that
    # as fatal -- RefineMesh can take the mesh and scene separately
    # via -i (camera poses, pre-mesh) + -m (mesh file).
    if mesh_scene.exists():
        print("Mesh MVS created.")
        refine_input = mesh_scene
        refine_mesh_override = None
    elif mesh_ply.exists():
        print(
            "ReconstructMesh wrote scene_dense_mesh.ply but not the "
            ".mvs scene. Feeding RefineMesh the pre-mesh scene plus "
            "the mesh file directly instead."
        )
        refine_input = dense_scene
        refine_mesh_override = mesh_ply
    else:
        raise RuntimeError(
            "Mesh reconstruction produced an empty mesh (0 vertices "
            "after cleanup), so no output file was written. This is "
            "caused by too few reliable dense points feeding into "
            "ReconstructMesh -- see the point-count check in Step 6 "
            "above for the likely root cause."
        )

    print("\nSTEP 8 : Refine Mesh\n")

    refined_scene = OPENMVS_WORKSPACE / "scene_dense_mesh_refine.mvs"

    refine_cmd = [REFINE, "-i", refine_input.resolve()]
    if refine_mesh_override is not None:
        refine_cmd += ["-m", refine_mesh_override.resolve()]
    refine_cmd += ["-o", refined_scene.resolve()]

    run(refine_cmd, cwd=OPENMVS_WORKSPACE)

    # Use a variable for result path to avoid shadowing mesh_scene
    final_mvs = refined_scene if refined_scene.exists() else mesh_scene
    if not final_mvs.exists() and mesh_ply.exists():
        final_mvs = mesh_ply

    print("\nSTEP 9 : Texture Mesh\n")

    textured_scene = OPENMVS_WORKSPACE / "scene_dense_mesh_refine_texture.mvs"

    texture_cmd = [TEXTURE, "-i", final_mvs.resolve()]
    if final_mvs.suffix == ".ply":
        # final_mvs fell back to a bare .ply (no camera poses) --
        # still needs the scene for cameras.
        texture_cmd = [
            TEXTURE, "-i", dense_scene.resolve(),
            "-m", final_mvs.resolve()
        ]
    texture_cmd += ["-o", textured_scene.resolve()]

    run(texture_cmd, cwd=OPENMVS_WORKSPACE)

    ply_candidates = [
        OPENMVS_WORKSPACE / "scene_dense_mesh_refine_texture.ply",
        OPENMVS_WORKSPACE / "scene_dense_mesh_refine.ply",
        OPENMVS_WORKSPACE / "scene_dense_mesh.ply",
    ]

    mesh_file = None
    for p in ply_candidates:
        if p.exists():
            mesh_file = p
            break

        if mesh_file is None:
         raise RuntimeError("No textured mesh (.ply) was created.")

    glb_path = OUTPUTS / "model.glb"

    mesh = o3d.io.read_triangle_mesh(str(mesh_file))

    if mesh.is_empty():
        raise RuntimeError("Generated mesh is empty.")

    bbox = mesh.get_axis_aligned_bounding_box()
    center = bbox.get_center()

    mesh.translate(-center)

    R = mesh.get_rotation_matrix_from_xyz(
        (-np.pi / 2, 0, 0)
    )

    mesh.rotate(R, center=(0, 0, 0))

    mesh.compute_vertex_normals()

    o3d.io.write_triangle_mesh(
        str(glb_path),
        mesh,
        write_ascii=False
    )

    print("\n===================================")
    print("3D Reconstruction Completed")
    print(glb_path)
    print("===================================\n")

    return str(glb_path)