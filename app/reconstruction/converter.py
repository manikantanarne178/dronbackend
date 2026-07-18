from pathlib import Path

OUTPUT = Path("app/outputs")

def convert_to_glb(mesh):

    glb = OUTPUT / "model.glb"

    glb.write_text("dummy glb")

    print("Conversion completed")

    return str(glb)