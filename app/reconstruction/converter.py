import subprocess
from pathlib import Path

# ==============================
# Paths
# ==============================

OUTPUT = Path("app/outputs")
OUTPUT.mkdir(parents=True, exist_ok=True)

SCRIPTS = Path("app/scripts")
SCRIPTS.mkdir(parents=True, exist_ok=True)

BLENDER = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")


def convert_to_glb(mesh_path):
    """
    Convert a mesh (.ply/.obj) into GLB using Blender.
    """

    mesh = Path(mesh_path)

    if not mesh.exists():
        raise FileNotFoundError(f"Mesh not found:\n{mesh}")

    if not BLENDER.exists():
        raise FileNotFoundError(f"Blender not found:\n{BLENDER}")

    glb = OUTPUT / "model.glb"
    script = SCRIPTS / "blender_convert.py"

    script.write_text(
f'''
import bpy
from pathlib import Path

print("="*60)
print("BLENDER STARTED")
print("Version:", bpy.app.version_string)

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

mesh = Path(r"{mesh}")

print("Mesh:", mesh)

if not mesh.exists():
    raise Exception(f"Mesh not found: {{mesh}}")

suffix = mesh.suffix.lower()

print("Extension:", suffix)

if suffix == ".ply":
    bpy.ops.wm.ply_import(filepath=str(mesh))

elif suffix == ".obj":
    bpy.ops.wm.obj_import(filepath=str(mesh))

else:
    raise Exception(f"Unsupported mesh format: {{suffix}}")

print("Mesh imported successfully.")

bpy.ops.object.select_all(action="SELECT")

output = r"{glb}"

print("Exporting to:", output)

bpy.ops.export_scene.gltf(
    filepath=output,
    export_format="GLB",
    export_apply=True
)

print("GLB exported successfully.")
print("="*60)
'''
    )

    print("\nLaunching Blender...\n")

    result = subprocess.run(
        [
            str(BLENDER),
            "--background",
            "--python",
            str(script),
        ],
        capture_output=True,
        text=True,
    )

    print("=" * 80)
    print("BLENDER STDOUT")
    print("=" * 80)
    print(result.stdout)

    print("=" * 80)
    print("BLENDER STDERR")
    print("=" * 80)
    print(result.stderr)

    print("=" * 80)
    print("RETURN CODE:", result.returncode)
    print("=" * 80)

    # -------------------------------------------------------
    # Success if GLB exists
    # -------------------------------------------------------

    if glb.exists():
        print("\n==========================================")
        print("GLB created successfully")
        print(glb)
        print("==========================================\n")

        return str(glb)

    # -------------------------------------------------------
    # Failure only if GLB was NOT created
    # -------------------------------------------------------

    raise RuntimeError(
        f"""
Blender did not generate the GLB.

Return Code:
{result.returncode}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""
    )