"""
Image upload router.

Provides:
    POST /api/upload/images  – upload one or more image files
"""

from typing import List
import shutil

from fastapi import APIRouter, File, HTTPException, status, UploadFile as FastAPIUploadFile

from app.utils import save_upload, UPLOAD_DIR

router = APIRouter(
    prefix="/api/upload",
    tags=["Upload"],
)


@router.post(
    "/images",
    summary="Upload image(s)",
    status_code=status.HTTP_200_OK,
)
async def upload_images(
    files: List[FastAPIUploadFile] = File(...),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided.",
        )

    # -------------------------------------------------
    # Clear previous uploaded images
    # -------------------------------------------------
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # Debug: Print received files
    # -------------------------------------------------
    print("\n==============================")
    print("UPLOAD API CALLED")
    print("==============================")

    print(f"Received {len(files)} file(s):")

    for i, file in enumerate(files, start=1):
        print(f"{i}. {file.filename}")

    # -------------------------------------------------
    # Save uploaded images
    # -------------------------------------------------
    uploaded = []

    for file in files:
        result = await save_upload(file)
        uploaded.append(result)

    # -------------------------------------------------
    # Debug: Verify upload folder
    # -------------------------------------------------
    print("\nFiles saved in upload folder:")

    saved_files = list(UPLOAD_DIR.iterdir())

    for f in saved_files:
        print(f.name)

    print(f"Total saved: {len(saved_files)}")
    print("==============================\n")

    return {
        "success": True,
        "message": f"{len(uploaded)} image(s) uploaded successfully.",
        "count": len(uploaded),
        "files": uploaded,
    }