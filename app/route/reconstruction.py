import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.colmap import get_colmap_diagnostics
from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.reconstruction.pipeline import run_pipeline

router = APIRouter(
    prefix="/api/reconstruction",
    tags=["Reconstruction"],
)


@router.get("/diagnostics")
async def get_diagnostics():
    """
    Diagnostic endpoint to inspect photogrammetry engine and COLMAP resolution.
    """
    return {
        "status": "online",
        "engine": get_colmap_diagnostics(),
    }


@router.post("/generate")
async def generate_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Run reconstruction pipeline asynchronously in a worker thread to keep ASGI event loop non-blocking
        result = await asyncio.to_thread(run_pipeline)

        project = Project(
            project_id=result["project_id"],
            user_id=current_user.id,
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "status": "success",
            "message": "3D reconstruction completed successfully.",
            "project_id": result["project_id"],
            "model_url": f"/api/projects/{result['project_id']}/model",
            "report_url": f"/api/report/download/{result['project_id']}",
            "statistics": result.get("statistics", {}),
            "processing_time": result.get("processing_time", 0.0),
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"3D Reconstruction failed: {str(e)}",
        )


@router.get("/model/{project_id}")
async def get_model(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    model_path = (settings.OUTPUT_DIR / "projects" / project_id / "model.glb").resolve()

    if not model_path.exists():
        # Fallback check
        fallback_path = Path("app/outputs/projects") / project_id / "model.glb"
        if fallback_path.exists():
            model_path = fallback_path
        else:
            raise HTTPException(
                status_code=404,
                detail="Model file not found.",
            )

    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename="model.glb",
    )

