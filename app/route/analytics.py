from pathlib import Path
import json

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)

PROJECTS_DIR = Path("app/outputs/projects")


@router.get("/{project_id}")
async def analytics(project_id: str):

    metadata = PROJECTS_DIR / project_id / "metadata.json"

    if not metadata.exists():
        raise HTTPException(
            status_code=404,
            detail="Metadata not found."
        )

    with open(metadata, "r", encoding="utf-8") as f:
        return json.load(f)