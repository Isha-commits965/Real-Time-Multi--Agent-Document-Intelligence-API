from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.common import get_db
from app.schemas.job import AnalyzeTriggerResponse, JobDetailResponse, JobListResponse
from app.services.analysis_service import run_analysis_job
from app.services.job_service import JobServiceError, create_analysis_job, get_job, list_jobs

router = APIRouter()


@router.post("/documents/{document_id}/analyze", response_model=AnalyzeTriggerResponse)
async def analyze_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalyzeTriggerResponse:
    try:
        response = create_analysis_job(db, document_id)
        background_tasks.add_task(run_analysis_job, response.job_id)
        return response
    except JobServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job_endpoint(job_id: str, db: Session = Depends(get_db)) -> JobDetailResponse:
    try:
        return get_job(db, job_id)
    except JobServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/jobs", response_model=JobListResponse)
def list_jobs_endpoint(db: Session = Depends(get_db)) -> JobListResponse:
    return list_jobs(db)
