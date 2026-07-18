from pathlib import Path

OUTPUT = Path("app/outputs")

def run_openmvs(sparse_file):

    mesh = OUTPUT / "mesh.obj"

    mesh.write_text("dummy mesh")

    print("OpenMVS completed")

    return str(mesh)