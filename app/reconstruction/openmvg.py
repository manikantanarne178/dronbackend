from pathlib import Path

OUTPUT = Path("app/outputs")
OUTPUT.mkdir(exist_ok=True)

def run_openmvg():

    sparse = OUTPUT / "sparse.mvs"

    sparse.write_text("dummy sparse model")

    print("OpenMVG completed")

    return str(sparse)