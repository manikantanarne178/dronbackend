
import bpy
from pathlib import Path

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

mesh = Path(r"C:\Users\Manikantha.N\Desktop\dronevision-backend\app\outputs\openmvs\scene_dense_mesh.ply")

# Import mesh based on extension
if mesh.suffix.lower() == ".obj":
    bpy.ops.wm.obj_import(filepath=str(mesh))

elif mesh.suffix.lower() == ".ply":
    bpy.ops.wm.ply_import(filepath=str(mesh))

else:
    raise Exception(f"Unsupported mesh format: {mesh.suffix}")

# Select everything
bpy.ops.object.select_all(action="SELECT")

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=r"app\outputs\model.glb",
    export_format="GLB",
    export_apply=True
)

print("GLB exported:", r"app\outputs\model.glb")
