from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.services.storage_service import storage_service

BASE_UPLOAD_DIR = storage_service.root

def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def generate_file_path(filename: str) -> Path:
    import uuid
    safe_name = Path(filename).name
    unique_id = uuid.uuid4().hex
    return BASE_UPLOAD_DIR / f"{unique_id}_{safe_name}"

async def save_upload_file(upload_file: UploadFile) -> Tuple[Path, str]:
    content = await upload_file.read()
    res = storage_service.save_file(content, upload_file.filename)
    return res["physical_path"], res["file_uuid"]

def get_file_path(file_uuid: str, original_filename: str) -> Path:
    p = storage_service.resolve_physical_path(file_uuid)
    if p:
        return p
    safe_name = Path(original_filename).name
    return BASE_UPLOAD_DIR / f"{file_uuid}_{safe_name}"