from pathlib import Path
from datetime import datetime
import shutil
import uuid

BASE_OUTPUT = Path("app/outputs")
PROJECTS_DIR = BASE_OUTPUT / "projects"


def create_project():
    """
    Creates a new project directory.

    Returns:
        project_id (str)
        project_path (Path)
    """

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_id = f"PRJ_{timestamp}_{uuid.uuid4().hex[:6]}"

    project_path = PROJECTS_DIR / project_id

    (project_path / "uploaded_images").mkdir(parents=True, exist_ok=True)
    (project_path / "screenshots").mkdir(parents=True, exist_ok=True)

    return project_id, project_path


def save_uploaded_images(files, project_path):
    """
    Copies uploaded images into the project folder.
    """

    images_folder = project_path / "uploaded_images"

    for file in files:
        src = Path(file)
        if src.exists():
            shutil.copy2(src, images_folder / src.name)


def save_output_file(source, destination):
    """
    Copies reconstruction outputs into the project.
    """

    source = Path(source)

    if source.exists():
        shutil.copy2(source, destination)