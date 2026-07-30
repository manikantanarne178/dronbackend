import os
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

# Base directory for all autodcr uploads (outside source control)
BASE_UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads" / "autodcr"

def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist (thread‑safe)."""
    path.mkdir(parents=True, exist_ok=True)

def generate_file_path(filename: str) -> Path:
    """Generate a unique file path for an uploaded drawing.

    The file is stored as <uuid>_<original‑filename> inside ``BASE_UPLOAD_DIR``.
    """
    ensure_directory(BASE_UPLOAD_DIR)
    unique_id = uuid.uuid4().hex
    safe_name = Path(filename).name  # strip any path components
    return BASE_UPLOAD_DIR / f"{unique_id}_{safe_name}"

async def save_upload_file(upload_file: UploadFile) -> Tuple[Path, str]:
    """Save an ``UploadFile`` to disk and return the absolute path and its UUID.

    Returns:
        (Path, str): absolute file path and the generated UUID (without extension).
    """
    dest_path = generate_file_path(upload_file.filename)
    # Write in chunks to avoid loading whole file into memory
    with dest_path.open('wb') as buffer:
        while True:
            chunk = await upload_file.read(1024 * 1024)  # 1 MiB
            if not chunk:
                break
            buffer.write(chunk)
    # Extract just the UUID part for DB storage/reference
    uuid_part = dest_path.stem.split('_')[0]
    return dest_path, uuid_part

def get_file_path(file_uuid: str, original_filename: str) -> Path:
    """Re‑construct the stored file path from its UUID and original name.
    Used when other services need to read the file.
    """
    safe_name = Path(original_filename).name
    return BASE_UPLOAD_DIR / f"{file_uuid}_{safe_name}"
