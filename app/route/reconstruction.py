import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_current_user
from app.core.colmap import get_colmap_diagnostics
from app.core.config import settings
from app.models.project import Project
from app.models.user import User
from app.reconstruction.pipeline import run_pipeline, OUTPUTS

router = APIRouter(
    prefix="/api/reconstruction",
    tags=["Reconstruction"],
)

JOBS_DIR = OUTPUTS / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory registry for fast lookups
JOBS_REGISTRY: Dict[str, Dict[str, Any]] = {}


def save_job_state(job_id: str, state: Dict[str, Any]) -> None:
    JOBS_REGISTRY[job_id] = state
    try:
        job_file = JOBS_DIR / f"{job_id}.json"
        job_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Failed to persist job {job_id}: {e}")


def load_job_state(job_id: str) -> Optional[Dict[str, Any]]:
    if job_id in JOBS_REGISTRY:
        return JOBS_REGISTRY[job_id]
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        try:
            data = json.loads(job_file.read_text(encoding="utf-8"))
            JOBS_REGISTRY[job_id] = data
            return data
        except Exception:
            pass
    return None


class GenerateModelRequest(BaseModel):
    upload_id: Optional[str] = None
    project_name: Optional[str] = None
    request_id: Optional[str] = None


@router.get("/diagnostics")
async def get_diagnostics():
    """
    Diagnostic endpoint to inspect photogrammetry engine and COLMAP resolution.
    """
    return {
        "status": "online",
        "engine": get_colmap_diagnostics(),
    }


def execute_reconstruction_task(job_id: str, upload_id: Optional[str], user_id: int):
    """
    Background worker function executing the photogrammetry pipeline.
    """
    db = SessionLocal()
    try:
        def update_status(stage: str, message: str):
            current = load_job_state(job_id) or {}
            current["status"] = stage
            current["stage"] = stage
            current["message"] = message
            current["updated_at"] = datetime.now().isoformat()
            save_job_state(job_id, current)

        update_status("RECONSTRUCTION", "Starting 3D reconstruction pipeline...")

        result = run_pipeline(
            upload_id=upload_id,
            status_callback=update_status,
        )

        project_id = result["project_id"]

        project = Project(
            project_id=project_id,
            user_id=user_id,
        )
        db.add(project)
        db.commit()

        final_state = {
            "job_id": job_id,
            "upload_id": upload_id,
            "project_id": project_id,
            "status": "COMPLETED",
            "stage": "COMPLETED",
            "message": "3D reconstruction completed successfully.",
            "model_url": f"/api/projects/{project_id}/model",
            "report_url": f"/api/report/download/{project_id}",
            "statistics": result.get("statistics", {}),
            "processing_time": result.get("processing_time", 0.0),
            "completed_at": datetime.now().isoformat(),
        }
        save_job_state(job_id, final_state)

    except Exception as e:
        db.rollback()
        print(f"[RECONSTRUCTION_JOB_FAILED] Job {job_id}: {e}")
        fail_state = {
            "job_id": job_id,
            "upload_id": upload_id,
            "status": "FAILED",
            "stage": "FAILED",
            "error": str(e),
            "message": f"Reconstruction failed: {str(e)}",
            "failed_at": datetime.now().isoformat(),
        }
        save_job_state(job_id, fail_state)
    finally:
        db.close()


@router.post("/generate")
async def generate_model(
    background_tasks: BackgroundTasks,
    payload: Optional[GenerateModelRequest] = Body(None),
    upload_id: Optional[str] = None,
    sync: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_upload_id = (payload.upload_id if payload else None) or upload_id
    req_id = (payload.request_id if payload else None) or f"REQ_{uuid.uuid4().hex[:6]}"
    job_id = f"JOB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    initial_state = {
        "job_id": job_id,
        "request_id": req_id,
        "upload_id": target_upload_id,
        "status": "QUEUED",
        "stage": "QUEUED",
        "message": "Reconstruction job queued for processing.",
        "created_at": datetime.now().isoformat(),
    }
    save_job_state(job_id, initial_state)

    print(f"[PIPELINE_JOB_CREATED] job_id={job_id} upload_id={target_upload_id} request_id={req_id}")

    if sync:
        # Synchronous execution mode
        try:
            result = await asyncio.to_thread(run_pipeline, upload_id=target_upload_id)
            project = Project(
                project_id=result["project_id"],
                user_id=current_user.id,
            )
            db.add(project)
            db.commit()
            db.refresh(project)

            return {
                "status": "COMPLETED",
                "job_id": job_id,
                "project_id": result["project_id"],
                "model_url": f"/api/projects/{result['project_id']}/model",
                "report_url": f"/api/report/download/{result['project_id']}",
                "statistics": result.get("statistics", {}),
                "processing_time": result.get("processing_time", 0.0),
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"3D Reconstruction failed: {str(e)}")

    # Asynchronous non-blocking background execution
    background_tasks.add_task(
        execute_reconstruction_task,
        job_id=job_id,
        upload_id=target_upload_id,
        user_id=current_user.id,
    )

    return {
        "status": "QUEUED",
        "job_id": job_id,
        "upload_id": target_upload_id,
        "request_id": req_id,
        "stage": "QUEUED",
        "message": "3D reconstruction job accepted and started in background.",
    }


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    state = load_job_state(job_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found. The server may have restarted or the job ID is invalid.",
        )
    return state


@router.get("/model/{project_id}")
async def get_model(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.user_id == current_user.id,
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    model_path = (settings.OUTPUT_DIR / "projects" / project_id / "model.glb").resolve()

    if not model_path.exists():
        fallback_path = Path("app/outputs/projects") / project_id / "model.glb"
        if fallback_path.exists():
            model_path = fallback_path
        else:
            raise HTTPException(
                status_code=404,
                detail="Model file not found.",
            )

    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename="model.glb",
    )
