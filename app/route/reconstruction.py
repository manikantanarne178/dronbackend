from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User
from app.reconstruction.pipeline import run_pipeline

router = APIRouter(
    prefix="/api/reconstruction",
    tags=["Reconstruction"],
)


@router.post("/generate")
async def generate_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Run reconstruction pipeline
        result = run_pipeline()

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
            "model_url": f"/api/reconstruction/model/{result['project_id']}",
            "report_url": f"/api/report/download/{result['project_id']}",
            "statistics": result.get("statistics", {}),
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e),
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

    model_path = Path(
        "app/outputs/projects"
    ) / project_id / "model.glb"

    if not model_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Model file not found.",
        )

    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename="model.glb",
    )