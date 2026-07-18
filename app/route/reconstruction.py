from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.reconstruction.pipeline import run_pipeline

router = APIRouter(
    prefix="/api/reconstruction",
    tags=["Reconstruction"]
)

# Final GLB location
MODEL_PATH = Path("app/outputs/model.glb")


@router.post("/generate")
async def generate_model():

    result = run_pipeline()

    return {
    "status": "success",
    "message": "3D model generated successfully",
    "model_url": "/api/reconstruction/model"
}


@router.get("/model")
async def get_model():

    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No model has been generated yet."
        )

    return FileResponse(
        path=MODEL_PATH,
        media_type="model/gltf-binary",
        filename="model.glb"
    )