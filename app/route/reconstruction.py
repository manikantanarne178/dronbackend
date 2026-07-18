from fastapi import APIRouter
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
        "result": result
    }