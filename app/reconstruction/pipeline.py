from pathlib import Path
import shutil
from datetime import datetime
import uuid

from app.reconstruction.colmap import run_colmap
from app.reconstruction.converter import convert_to_glb
from app.reconstruction.analysis import analyze_mesh
from app.reconstruction.metadata import save_metadata

from app.reports.renderer import ModelRenderer
from app.reports.pdf_generator import PDFReportGenerator


OUTPUT_DIR = Path("app/outputs")
PROJECTS_DIR = OUTPUT_DIR / "projects"
UPLOADS_DIR = Path("app/uploads/images")
def cleanup_workspace():
    """
    Remove previous reconstruction outputs.
    Do NOT delete uploaded images or saved projects.
    """
    # Remove old reconstruction folders
    for folder in ["colmap", "openmvs"]:
        path = OUTPUT_DIR / folder
        if path.exists():
            print(f"Deleting {path}")
            shutil.rmtree(path)

    # Remove old generated files
    for file in [
        "model.glb",
        "mesh.obj",
        "metadata.json",
        "sparse.mvs",
    ]:
        path = OUTPUT_DIR / file
        if path.exists():
            print(f"Deleting {path}")
            path.unlink()

def create_project():
    """
    Create a unique project folder.
    """
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    project_id = (
        f"PRJ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid.uuid4().hex[:6]}"
    )

    project_dir = PROJECTS_DIR / project_id

    (project_dir / "uploaded_images").mkdir(parents=True, exist_ok=True)
    (project_dir / "screenshots").mkdir(parents=True, exist_ok=True)

    return project_id, project_dir


def copy_if_exists(src, dst):
    src = Path(src)

    if src.exists():
        shutil.copy2(src, dst)


def copy_uploaded_images(project_dir):
    """
    Copy uploaded drone images into the project folder.
    """
    if not UPLOADS_DIR.exists():
        return

    destination = project_dir / "uploaded_images"

    for image in UPLOADS_DIR.iterdir():
        if image.is_file():
            shutil.copy2(image, destination / image.name)


def run_pipeline():

    try:

        print("=" * 70)
        print("STARTING DRONEVISION RECONSTRUCTION")
        print("=" * 70)

        # ---------------------------------------------------
        # Create Project
        # ---------------------------------------------------

        project_id, project_dir = create_project()

        print(f"PROJECT ID : {project_id}")
        print(f"PROJECT DIR: {project_dir}")

        # ---------------------------------------------------
        # COLMAP + OpenMVS
        # ---------------------------------------------------

        print("\nSTEP 1 -> Running COLMAP/OpenMVS")
        cleanup_workspace()

        print("\nSTEP 1 -> Running COLMAP/OpenMVS")
        mesh = run_colmap()

        print("STEP 1 COMPLETE")

        # ---------------------------------------------------
        # Convert OBJ -> GLB
        # ---------------------------------------------------

        print("\nSTEP 2 -> Convert Mesh to GLB")

        glb = convert_to_glb(mesh)

        print("STEP 2 COMPLETE")

        # ---------------------------------------------------
        # Analyze Mesh
        # ---------------------------------------------------

        print("\nSTEP 3 -> Analyze Mesh")

        metadata = analyze_mesh(glb)

        print("STEP 3 COMPLETE")

        # ---------------------------------------------------
        # Save Metadata
        # ---------------------------------------------------

        print("\nSTEP 4 -> Save Metadata")

        metadata_file = save_metadata(
    metadata=metadata,
    project_dir=project_dir,
    project_id=project_id,
    images_uploaded=len(list(UPLOADS_DIR.glob("*"))),
)

        print("STEP 4 COMPLETE")

        # ---------------------------------------------------
        # Copy Files to Project
        # ---------------------------------------------------

        print("\nSTEP 5 -> Saving Project Files")

        copy_if_exists(
            "app/outputs/model.glb",
            project_dir / "model.glb",
        )

        copy_if_exists(
            "app/outputs/mesh.obj",
            project_dir / "mesh.obj",
        )

        # copy_if_exists(
        #     metadata_file,
        #     project_dir / "metadata.json",
        # )

        copy_uploaded_images(project_dir)

        print("Project files copied.")

        # ---------------------------------------------------
        # Generate Screenshots
        # ---------------------------------------------------

        print("\nSTEP 6 -> Generating Screenshots")

        try:
            renderer = ModelRenderer(project_dir)
            renderer.render()

            print("Screenshots generated successfully.")

        except Exception as e:
            print(f"Screenshot generation skipped: {e}")

        # ---------------------------------------------------
        # Generate PDF
        # ---------------------------------------------------

        print("\nSTEP 7 -> Generating PDF Report")

        report_path = None

        try:
            pdf = PDFReportGenerator(project_dir)
            report_path = pdf.generate()

            print(f"Report generated: {report_path}")

        except Exception as e:
            print(f"PDF generation skipped: {e}")

        print("=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)

        return {
            "success": True,
            "project_id": project_id,
            "project_dir": str(project_dir),
            "mesh": str(project_dir / "mesh.obj"),
            "glb": str(project_dir / "model.glb"),
            "metadata": str(project_dir / "metadata.json"),
            "report": str(report_path) if report_path else None,
            "statistics": metadata,
        }

    except Exception as e:
        print("=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)
        print(e)
        raise