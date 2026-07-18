from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil

router = APIRouter(
    prefix="/api/upload",
    tags=["Upload"]
)

UPLOAD_DIR = Path("app/uploads/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/images")
async def upload_images(
    files: list[UploadFile] = File(...)
):
    uploaded_files = []

    for file in files:
        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_files.append(file.filename)

    return {
        "message": "Images uploaded successfully",
        "count": len(uploaded_files),
        "files": uploaded_files
    }