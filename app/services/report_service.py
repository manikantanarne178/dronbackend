import json
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.reports.pdf_generator import PDFReportGenerator


PROJECTS_DIR = Path("app/outputs/projects")


class ReportService:

    @staticmethod
    def generate(project_id: str, current_user: User, db: Session):

        project_db = (
            db.query(Project)
            .filter(
                Project.project_id == project_id,
                Project.user_id == current_user.id,
            )
            .first()
        )

        if not project_db:
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        project_path = PROJECTS_DIR / project_id

        if not project_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Project not found",
            )

        metadata_file = project_path / "metadata.json"

        if not metadata_file.exists():
            raise HTTPException(
                status_code=404,
                detail="metadata.json not found",
            )

        generator = PDFReportGenerator(project_path)

        pdf_path = generator.generate()

        return {
            "success": True,
            "message": "Report generated successfully.",
            "project_id": project_id,
            "report": str(pdf_path)
        }