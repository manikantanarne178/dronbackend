import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User

router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)

PROJECTS_DIR = Path("app/outputs/projects")


# ============================================================================
# GET - List All Projects
# ============================================================================

@router.get("/")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List only the current user's generated projects.
    """

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    projects = []

    project_records = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .all()
    )

    for record in project_records:

        project = PROJECTS_DIR / record.project_id

        if not project.exists():
            continue

        metadata_file = project / "metadata.json"

        if not metadata_file.exists():
            continue

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            dimensions = metadata.get("dimensions", {})

            projects.append({
                "project_id": metadata.get("project_id", project.name),
                "generated_at": metadata.get("generated_at"),
                "processing_time": metadata.get("processing_time_seconds"),
                "images_uploaded": metadata.get("images_uploaded", 0),

                "width": dimensions.get("width", 0),
                "length": dimensions.get("length", 0),
                "height": dimensions.get("height", 0),

                "ground_area": metadata.get("ground_area", 0),
                "surface_area": metadata.get("surface_area", 0),
                "volume": metadata.get("volume", 0),

                "vertices": metadata.get("vertices", 0),
                "triangles": metadata.get("triangles", 0),

                "model_url": f"/api/projects/{project.name}/model",
                "report_url": f"/api/projects/{project.name}/report",
            })

        except Exception as e:
            print(f"Error reading {metadata_file}: {e}")

    return {
        "success": True,
        "projects": projects
    }


# ============================================================================
# GET - Single Project Details
# ============================================================================

@router.get("/{project_id}")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project_db = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if not project_db:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    project = PROJECTS_DIR / project_id

    if not project.exists():
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    metadata_file = project / "metadata.json"

    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return metadata

    return {
        "project_id": project.name,
        "files": [f.name for f in project.iterdir()],
    }


# ============================================================================
# GET - Download Report
# ============================================================================

@router.get("/{project_id}/report")
def download_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project_db = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if not project_db:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    project = PROJECTS_DIR / project_id

    if not project.exists():
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    report = next(project.glob("*.pdf"), None)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return FileResponse(
        path=report,
        media_type="application/pdf",
        filename=report.name,
    )


# ============================================================================
# GET - Download Model
# ============================================================================

@router.get("/{project_id}/model")
def download_model(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project_db = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if not project_db:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    project = PROJECTS_DIR / project_id

    if not project.exists():
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    model = project / "model.glb"

    if not model.exists():
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    return FileResponse(
        path=model,
        media_type="model/gltf-binary",
        filename="model.glb",
    )


# ============================================================================
# DELETE - Delete Project
# ============================================================================

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project_db = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if not project_db:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    project = PROJECTS_DIR / project_id

    if project.exists():
        shutil.rmtree(project)

    db.delete(project_db)
    db.commit()

    return {
        "success": True,
        "message": "Project deleted successfully."
    }