from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.reports.renderer import ModelRenderer
from app.reports.pdf_generator import PDFReportGenerator

router = APIRouter(
    prefix="/api/report",
    tags=["Report"],
)

PROJECTS = Path("app/outputs/projects")


@router.post("/generate/{project_id}")
async def generate_report(project_id: str):

    project = PROJECTS / project_id

    if not project.exists():
        raise HTTPException(404, "Project not found.")

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
async def download_report(project_id: str):

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