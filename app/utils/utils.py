"""
Reusable helper functions for image upload validation and file saving.
"""

import uuid
import aiofiles
from pathlib import Path
from typing import Any, Set

from fastapi import UploadFile as _UploadFile, HTTPException, status


# ---------------------------------------------------------------------------
# Custom UploadFile – fixes Swagger UI file-picker
# ---------------------------------------------------------------------------

class UploadFile(_UploadFile):
    """
    Drop-in replacement for `fastapi.UploadFile` that forces the OpenAPI
    schema to use `format: binary` instead of the newer
    `contentMediaType: application/octet-stream`.

    *Why?*  FastAPI ≥ 0.129.1 switched to `contentMediaType` for OpenAPI
    3.1.0 compliance, but Swagger UI only renders a native file-picker when
    it sees `{"type": "string", "format": "binary"}`.  This class
    restores that behaviour at the Pydantic-schema level so the fix applies
    everywhere the type is referenced — no post-processing needed.
    """

    @classmethod
    def _get_pydantic_json_schema_(
        cls, core_schema: Any, handler: Any
    ) -> dict[str, Any]:
        return {"type": "string", "format": "binary"}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Allowed image extensions (lowercase, with leading dot)
ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}

# Allowed MIME content types
ALLOWED_CONTENT_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Maximum file size in bytes (10 MB)
MAX_FILE_SIZE: int = 10 * 1024 * 1024

# Upload destination
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Chunk size for streaming writes (64 KB)
CHUNK_SIZE: int = 64 * 1024


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_file_extension(filename: str) -> str:
    """
    Validate that the file has an allowed image extension.

    Returns the lowercase extension if valid; raises HTTPException otherwise.
    """
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File '{filename}' has unsupported extension '{extension}'. "
                f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )
    return extension


def validate_content_type(file: _UploadFile) -> None:
    """
    Validate that the uploaded file's MIME content-type is an allowed image type.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File '{file.filename}' has unsupported content type "
                f"'{file.content_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            ),
        )


def validate_not_empty(file: _UploadFile) -> None:
    """
    Reject files that have no filename or appear to be empty placeholders.
    """
    if not file.filename or file.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An uploaded file has no filename. Please select a valid file.",
        )


# ---------------------------------------------------------------------------
# File-saving helper
# ---------------------------------------------------------------------------

def generate_unique_filename(extension: str) -> str:
    """
    Generate a collision-free filename using UUID4.
    """
    return f"{uuid.uuid4().hex}{extension}"


async def save_upload(file: _UploadFile) -> dict:
    """
    Validate and save an uploaded image.

    Returns metadata that will later be stored in the project report.
    """

    validate_not_empty(file)

    extension = validate_file_extension(file.filename)

    validate_content_type(file)

    saved_name = generate_unique_filename(extension)

    file_path = UPLOAD_DIR / saved_name

    total_bytes = 0

    async with aiofiles.open(file_path, "wb") as out:

        while True:

            chunk = await file.read(CHUNK_SIZE)

            if not chunk:
                break

            total_bytes += len(chunk)

            if total_bytes > MAX_FILE_SIZE:
                await out.close()

                if file_path.exists():
                    file_path.unlink()

                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"{file.filename} exceeds 10 MB limit.",
                )

            await out.write(chunk)

    return {
        "original_name": file.filename,
        "saved_name": saved_name,
        "content_type": file.content_type,
        "size_bytes": total_bytes,
        "path": str(file_path),
    }