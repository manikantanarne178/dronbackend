import json
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.project import Project
from app.models.user import User

router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)


@router.get("/")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all generated drone photogrammetry projects strictly belonging to the authenticated user.
    Database serves as the durable source of truth.
    """
    projects_dir = settings.PROJECTS_DIR
    projects_dir.mkdir(parents=True, exist_ok=True)

    project_records = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    projects = []

    for record in project_records:
        proj_dict = {
            "project_id": record.project_id,
            "name": record.name or f"Survey {record.project_id}",
            "generated_at": record.created_at.isoformat() if record.created_at else None,
            "processing_time": record.processing_time,
            "images_uploaded": record.images_uploaded,
            "status": record.status or "COMPLETED",
            "width": record.width,
            "length": record.length,
            "height": record.height,
            "dimensions": {
                "width": record.width,
                "length": record.length,
                "height": record.height,
            },
            "ground_area": record.ground_area,
            "surface_area": record.surface_area,
            "volume": record.volume,
            "vertices": record.vertices,
            "triangles": record.triangles,
            "model_url": record.model_url or f"/api/projects/{record.project_id}/model",
            "report_url": record.report_url or f"/api/projects/{record.project_id}/report",
        }

        # Check for disk metadata enrichment
        metadata_file = projects_dir / record.project_id / "metadata.json"
        if not metadata_file.exists():
            fallback_meta = Path("app/outputs/projects") / record.project_id / "metadata.json"
            if fallback_meta.exists():
                metadata_file = fallback_meta

        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                dims = meta.get("dimensions", {})
                proj_dict["name"] = meta.get("name", proj_dict["name"])
                proj_dict["images_uploaded"] = meta.get("images_uploaded", proj_dict["images_uploaded"])
                proj_dict["width"] = dims.get("width", proj_dict["width"])
                proj_dict["length"] = dims.get("length", proj_dict["length"])
                proj_dict["height"] = dims.get("height", proj_dict["height"])
                proj_dict["dimensions"] = {
                    "width": proj_dict["width"],
                    "length": proj_dict["length"],
                    "height": proj_dict["height"],
                }
                proj_dict["ground_area"] = meta.get("ground_area", proj_dict["ground_area"])
                proj_dict["surface_area"] = meta.get("surface_area", proj_dict["surface_area"])
                proj_dict["volume"] = meta.get("volume", proj_dict["volume"])
                proj_dict["vertices"] = meta.get("vertices", proj_dict["vertices"])
                proj_dict["triangles"] = meta.get("triangles", proj_dict["triangles"])
            except Exception as e:
                print(f"Notice reading metadata {metadata_file}: {e}")

        projects.append(proj_dict)

    return {
        "success": True,
        "count": len(projects),
        "projects": projects,
    }


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
            detail="Access denied or project not found.",
        )

    metadata_file = settings.PROJECTS_DIR / project_id / "metadata.json"
    if not metadata_file.exists():
        fallback_meta = Path("app/outputs/projects") / project_id / "metadata.json"
        if fallback_meta.exists():
            metadata_file = fallback_meta

    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Return constructed metadata from database
    return {
        "project_id": project_db.project_id,
        "name": project_db.name or f"Survey {project_db.project_id}",
        "generated_at": project_db.created_at.isoformat() if project_db.created_at else None,
        "processing_time_seconds": project_db.processing_time,
        "images_uploaded": project_db.images_uploaded,
        "dimensions": {
            "width": project_db.width,
            "length": project_db.length,
            "height": project_db.height,
        },
        "ground_area": project_db.ground_area,
        "surface_area": project_db.surface_area,
        "volume": project_db.volume,
        "vertices": project_db.vertices,
        "triangles": project_db.triangles,
        "model_url": f"/api/projects/{project_db.project_id}/model",
        "report_url": f"/api/projects/{project_db.project_id}/report",
    }


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
            detail="Access denied or project not found.",
        )

    model = settings.PROJECTS_DIR / project_id / "model.glb"
    if not model.exists():
        fallback_model = Path("app/outputs/projects") / project_id / "model.glb"
        if fallback_model.exists():
            model = fallback_model
        else:
            raise HTTPException(
                status_code=404,
                detail="3D model is not available for this project.",
            )

    return FileResponse(
        path=model,
        media_type="model/gltf-binary",
        filename="model.glb",
    )


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
            detail="Access denied or project not found.",
        )

    project_dir = settings.PROJECTS_DIR / project_id
    if not project_dir.exists():
        project_dir = Path("app/outputs/projects") / project_id

    report = next(project_dir.glob("*.pdf"), None) if project_dir.exists() else None

    if report is None or not report.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    return FileResponse(
        path=report,
        media_type="application/pdf",
        filename=report.name,
    )


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
            detail="Access denied or project not found.",
        )

    project_dir = settings.PROJECTS_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)

    db.delete(project_db)
    db.commit()

    return {
        "success": True,
        "message": "Project deleted successfully.",
    }
