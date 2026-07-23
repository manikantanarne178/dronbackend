from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.project import Project
from app.models.user import User

from app.reports.renderer import ModelRenderer
from app.reports.pdf_generator import PDFReportGenerator

router = APIRouter(
    prefix="/api/report",
    tags=["Report"],
)

PROJECTS = Path("app/outputs/projects")


@router.post("/generate/{project_id}")
async def generate_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership
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

    project = PROJECTS / project_id

    if not project.exists():
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    renderer = ModelRenderer(project)
    renderer.render()

    pdf = PDFReportGenerator(project)
    report = pdf.generate()

    return {
        "status": "success",
        "project_id": project_id,
        "report": str(report),
        "download_url": f"/api/report/download/{project_id}",
    }


@router.get("/download/{project_id}")
async def download_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership
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

    report = PROJECTS / project_id / "report.pdf"

    if not report.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not generated."
        )

    return FileResponse(
        report,
        media_type="application/pdf",
        filename=f"{project_id}_DroneVision_Report.pdf",
    )