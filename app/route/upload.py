"""
Image upload router.

Provides:
    POST /api/upload/images  – upload one or more image files
"""

import gc
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, status, UploadFile as FastAPIUploadFile

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
    upload_id: Optional[str] = Form(None),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided.",
        )

    session_upload_id = upload_id or f"UP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    session_dir = UPLOAD_DIR / session_upload_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # Also keep latest batch in root UPLOAD_DIR
    # -------------------------------------------------
    if UPLOAD_DIR.exists():
        for old_file in list(UPLOAD_DIR.glob("*.jpg")) + list(UPLOAD_DIR.glob("*.jpeg")) + list(UPLOAD_DIR.glob("*.png")):
            try:
                old_file.unlink()
            except Exception:
                pass

    print("\n==============================")
    print(f"UPLOAD API CALLED: {session_upload_id}")
    print("==============================")
    print(f"Received {len(files)} file(s):")

    for i, file in enumerate(files, start=1):
        print(f"{i}. {file.filename}")

    # -------------------------------------------------
    # Save uploaded images
    # -------------------------------------------------
    uploaded = []

    for file in files:
        try:
            # Save into session dir
            result = await save_upload(file, target_dir=session_dir)
            # Also copy to root upload dir for legacy backwards compatibility
            root_copy = UPLOAD_DIR / Path(result["saved_name"]).name
            shutil.copy2(result["path"], root_copy)
            uploaded.append(result)
        finally:
            await file.close()

    del files
    gc.collect()

    print(f"\nSaved {len(uploaded)} files in session: {session_dir}")
    print("==============================\n")

    return {
        "success": True,
        "message": f"{len(uploaded)} image(s) uploaded successfully.",
        "count": len(uploaded),
        "upload_id": session_upload_id,
        "files": uploaded,
    }
