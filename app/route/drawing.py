from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.controller.drawing import DrawingController
from app.core.database import get_db

router = APIRouter(
    prefix="/api/drawings",
    tags=["Drawings"]
)


@router.post("/upload")
async def upload_drawing(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await DrawingController.upload(file, db)