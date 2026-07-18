"""
Image upload router.

Provides:
    POST /api/upload/images  – upload one or more image files
"""

from typing import List

from fastapi import APIRouter, File, HTTPException, status, UploadFile as FastAPIUploadFile

from app.utils import save_upload

router = APIRouter(
    prefix="/api/upload",
    tags=["Upload"],
)


# ===========================================================================
# POST – Upload one or more images
# ===========================================================================
@router.post(
    "/images",
    summary="Upload image(s)",
    description=(
        "Upload one or more image files (jpg, jpeg, png, webp). "
        "Each file is saved with a unique UUID filename so that repeated "
        "uploads never overwrite previous files."
    ),
    status_code=status.HTTP_200_OK,
)
async def upload_images(
    files: List[FastAPIUploadFile] = File(
        ...,
        description="One or more image files to upload (jpg, jpeg, png, webp).",
    ),
):
    """
    Accept one or multiple image files via multipart/form-data.

    - Validates each file's extension and MIME type.
    - Rejects empty uploads and oversized files (>10 MB).
    - Saves each file with a unique UUID-based filename.
    - Returns metadata for every successfully saved file.
    """
    # Guard: reject requests with an empty file list
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided. Please select at least one image.",
        )

    uploaded: list[dict] = []

    for file in files:
        result = await save_upload(file)
        uploaded.append(result)

    return {
        "success": True,
        "message": f"{len(uploaded)} image(s) uploaded successfully.",
        "count": len(uploaded),
        "files": uploaded,
    }