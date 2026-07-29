from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models.user import User

from app.services.report_service import ReportService

router = APIRouter(
    prefix="/api/report",
    tags=["Report"]
)


@router.post("/generate/{project_id}")
def generate_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return ReportService.generate(
        project_id=project_id,
        current_user=current_user,
        db=db,
    )