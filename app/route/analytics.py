from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)

PROJECTS_DIR = Path("app/outputs/projects")


@router.get("/{project_id}")
async def analytics(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership
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

    metadata = PROJECTS_DIR / project_id / "metadata.json"

    if not metadata.exists():
        raise HTTPException(
            status_code=404,
            detail="Metadata not found."
        )

    with open(metadata, "r", encoding="utf-8") as f:
        return json.load(f)