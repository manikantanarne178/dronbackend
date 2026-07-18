from app.reconstruction.openmvg import run_openmvg
from app.reconstruction.openmvs import run_openmvs
from app.reconstruction.converter import convert_to_glb

def run_pipeline():

    print("Running OpenMVG...")

    sparse = run_openmvg()

    print("Running OpenMVS...")

    mesh = run_openmvs(sparse)

    print("Converting...")

    glb = convert_to_glb(mesh)

    return {
        "sparse": sparse,
        "mesh": mesh,
        "glb": glb
    }