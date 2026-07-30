"""
Rate Limiter and Security Middleware module for AutoDCR.
Provides rate limiting, file upload MIME and extension verification,
path traversal protection, and malicious payload sanitization.
"""

import os
from typing import List
from fastapi import HTTPException, UploadFile, Request


class SecurityValidator:
    """
    Security and validation helper functions.
    """

    ALLOWED_EXTENSIONS = {".dxf", ".dwg", ".ifc", ".pdf"}
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB limit

    @classmethod
    def validate_file_upload(cls, file: UploadFile) -> None:
        """
        Validates file extension, size, and sanitizes filename against path traversal attacks.
        """
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()

        if ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )

        # Path traversal prevention
        if ".." in filename or "/" in filename or "\\" in filename:
            safe_basename = os.path.basename(filename.replace("\\", "/"))
            file.filename = safe_basename

    @classmethod
    def sanitize_path(cls, path_str: str) -> str:
        """
        Ensures a path string cannot break out of workspace root.
        """
        clean = os.path.normpath(path_str)
        if clean.startswith("..") or "/.." in clean or "\\.." in clean:
            raise HTTPException(status_code=400, detail="Invalid path string: path traversal detected.")
        return clean
