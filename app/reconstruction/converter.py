import subprocess
from pathlib import Path

OUTPUT = Path("app/outputs")

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"


def convert_to_glb(mesh):

    mesh = Path(mesh)

    if not mesh.exists():
        raise FileNotFoundError(f"Mesh not found: {mesh}")

    glb = OUTPUT / "model.glb"

    script = OUTPUT / "blender_convert.py"

    script.write_text(f'''
import bpy
from pathlib import Path

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

mesh = Path(r"{mesh}")

# Import mesh based on extension
if mesh.suffix.lower() == ".obj":
    bpy.ops.wm.obj_import(filepath=str(mesh))

elif mesh.suffix.lower() == ".ply":
    bpy.ops.wm.ply_import(filepath=str(mesh))

else:
    raise Exception(f"Unsupported mesh format: {{mesh.suffix}}")

# Select everything
bpy.ops.object.select_all(action="SELECT")

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=r"{glb}",
    export_format="GLB",
    export_apply=True
)

print("GLB exported:", r"{glb}")
''')

    result = subprocess.run(
    [
        BLENDER,
        "--background",
        "--python",
        str(script),
    ],
    capture_output=True,
    text=True
)

    print(result.stdout)
    print(result.stderr)

    result.check_returncode()

    if not glb.exists():
        raise RuntimeError("Blender failed to create model.glb")

    print(f"\nGLB created successfully:\n{glb}\n")

    return str(glb)