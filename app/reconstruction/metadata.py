"""
Project Metadata Manager

Stores metadata for each reconstruction project.

Example:

app/
└── outputs/
    └── projects/
        └── PRJ_xxxxxx/
            ├── metadata.json
            ├── model.glb
            ├── report.pdf
            └── ...
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json


def metadata_path(project_dir: Path) -> Path:
    """
    Returns metadata.json path for a project.
    """
    return Path(project_dir) / "metadata.json"


# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------

def save_metadata(
    metadata: Dict[str, Any],
    project_dir: Path | None = None,
    project_id: str | None = None,
    processing_time: float | None = None,
    images_uploaded: int | None = None,
) -> Path:

    if project_dir is None:
        project_dir = Path("app/outputs")

    project_dir.mkdir(parents=True, exist_ok=True)

    data = dict(metadata)

    data.update(
        {
            "project_id": project_id,
            "generated_at": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            "images_uploaded": images_uploaded,
        }
    )

    file = metadata_path(project_dir)

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return file


# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------

def load_metadata(project_dir: Path):

    file = metadata_path(project_dir)

    if not file.exists():
        raise FileNotFoundError(file)

    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------
# Exists
# ------------------------------------------------------------------

def metadata_exists(project_dir: Path):

    return metadata_path(project_dir).exists()


# ------------------------------------------------------------------
# Update
# ------------------------------------------------------------------

def update_metadata(project_dir: Path, values: Dict[str, Any]):

    data = {}

    if metadata_exists(project_dir):
        data = load_metadata(project_dir)

    data.update(values)

    save_metadata(
        data,
        project_dir=project_dir,
    )


# ------------------------------------------------------------------
# Delete
# ------------------------------------------------------------------

def delete_metadata(project_dir: Path):

    file = metadata_path(project_dir)

    if file.exists():
        file.unlink()