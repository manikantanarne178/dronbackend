from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.reconstruction.pipeline import run_pipeline

router = APIRouter(
    prefix="/api/reconstruction",
    tags=["Reconstruction"]
)


@router.post("/generate")
async def generate_model():

    result = run_pipeline()

    return {
        "status": "success",
        "message": "3D reconstruction completed successfully.",
        "project_id": result["project_id"],
        "model_url": f"/api/reconstruction/model/{result['project_id']}",
        "report_url": f"/api/report/download/{result['project_id']}",
        "statistics": result["statistics"],
    }


@router.get("/model/{project_id}")
async def get_model(project_id: str):

    model = Path(
        f"app/outputs/projects/{project_id}/model.glb"
    )

    if not model.exists():
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    return FileResponse(
        path=model,
        media_type="model/gltf-binary",
        filename="model.glb",
    )