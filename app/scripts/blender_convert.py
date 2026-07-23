
import bpy
from pathlib import Path

print("=" * 60)
print("BLENDER STARTED")
print("Version:", bpy.app.version_string)

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

mesh = Path(r"C:\Users\Manikantha.N\Desktop\dronevision-backend\app\outputs\openmvs\scene_dense_mesh_refine_texture.ply")

print("Mesh:", mesh)

if not mesh.exists():
    raise Exception(f"Mesh not found: {mesh}")

suffix = mesh.suffix.lower()

print("Extension:", suffix)

if suffix == ".ply":
    bpy.ops.wm.ply_import(filepath=str(mesh))

elif suffix == ".obj":
    bpy.ops.wm.obj_import(filepath=str(mesh))

else:
    raise Exception(f"Unsupported mesh format: {suffix}")

print("Mesh imported successfully.")

bpy.ops.object.select_all(action="SELECT")

output = r"C:\Users\Manikantha.N\Desktop\dronevision-backend\app\outputs\projects\ff95d255661e497d9f3e8fdbf6a1d80a\model.glb"

print("Exporting to:", output)

bpy.ops.export_scene.gltf(
    filepath=output,
    export_format="GLB",
    export_apply=True
)

print("GLB exported successfully.")
print("=" * 60)
