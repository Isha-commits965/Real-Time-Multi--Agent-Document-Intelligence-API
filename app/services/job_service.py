from datetime import UTC, datetime
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.agent_run import AgentRun
from app.db.models.analysis_job import AnalysisJob
from app.db.models.document import Document
from app.db.models.enums import AgentName, AgentStatus, JobStatus
from app.schemas.agent_results import (
    DocumentClassifierResult,
    EntityExtractorResult,
    SentimentAnalyzerResult,
    SummarizerResult,
)
from app.schemas.job import (
    AgentStatusResponse,
    AgentsDetailResponse,
    AgentsStatusResponse,
    AnalyzeTriggerResponse,
    DocumentClassifierAgentResponse,
    EntityExtractorAgentResponse,
    JobDetailResponse,
    JobListItem,
    JobListResponse,
    SentimentAnalyzerAgentResponse,
    SummarizerAgentResponse,
)
from app.services.id_generator import generate_job_id

logger = logging.getLogger(__name__)


class JobServiceError(Exception):
    def __init__(self, message: str, status_code: int = 404) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


AGENT_ORDER = (
    AgentName.SUMMARIZER,
    AgentName.ENTITY_EXTRACTOR,
    AgentName.SENTIMENT_ANALYZER,
    AgentName.DOCUMENT_CLASSIFIER,
)


def _get_job_query():
    return select(AnalysisJob).options(
        selectinload(AnalysisJob.agent_runs),
        selectinload(AnalysisJob.document),
    )


def _agent_run_by_name(job: AnalysisJob, agent_name: AgentName) -> AgentRun:
    for run in job.agent_runs:
        if run.agent_name == agent_name:
            return run
    raise JobServiceError(f"Agent run not found: {agent_name.value}")


def _to_agents_status(job: AnalysisJob) -> AgentsStatusResponse:
    return AgentsStatusResponse(
        summarizer=AgentStatusResponse(status=_agent_run_by_name(job, AgentName.SUMMARIZER).status),
        entity_extractor=AgentStatusResponse(
            status=_agent_run_by_name(job, AgentName.ENTITY_EXTRACTOR).status
        ),
        sentiment_analyzer=AgentStatusResponse(
            status=_agent_run_by_name(job, AgentName.SENTIMENT_ANALYZER).status
        ),
        document_classifier=AgentStatusResponse(
            status=_agent_run_by_name(job, AgentName.DOCUMENT_CLASSIFIER).status
        ),
    )


def _parse_result(model_cls: type, data: dict[str, Any] | None):
    if data is None:
        return None
    return model_cls.model_validate(data)


def _to_summarizer_response(run: AgentRun) -> SummarizerAgentResponse:
    return SummarizerAgentResponse(
        status=run.status,
        processing_time_seconds=run.processing_time_seconds,
        result=_parse_result(SummarizerResult, run.result),
        error=run.error,
    )


def _to_entity_response(run: AgentRun) -> EntityExtractorAgentResponse:
    return EntityExtractorAgentResponse(
        status=run.status,
        processing_time_seconds=run.processing_time_seconds,
        result=_parse_result(EntityExtractorResult, run.result),
        error=run.error,
    )


def _to_sentiment_response(run: AgentRun) -> SentimentAnalyzerAgentResponse:
    return SentimentAnalyzerAgentResponse(
        status=run.status,
        processing_time_seconds=run.processing_time_seconds,
        result=_parse_result(SentimentAnalyzerResult, run.result),
        error=run.error,
    )


def _to_classifier_response(run: AgentRun) -> DocumentClassifierAgentResponse:
    return DocumentClassifierAgentResponse(
        status=run.status,
        processing_time_seconds=run.processing_time_seconds,
        result=_parse_result(DocumentClassifierResult, run.result),
        error=run.error,
    )


def _to_agents_detail(job: AnalysisJob) -> AgentsDetailResponse:
    return AgentsDetailResponse(
        summarizer=_to_summarizer_response(_agent_run_by_name(job, AgentName.SUMMARIZER)),
        entity_extractor=_to_entity_response(_agent_run_by_name(job, AgentName.ENTITY_EXTRACTOR)),
        sentiment_analyzer=_to_sentiment_response(
            _agent_run_by_name(job, AgentName.SENTIMENT_ANALYZER)
        ),
        document_classifier=_to_classifier_response(
            _agent_run_by_name(job, AgentName.DOCUMENT_CLASSIFIER)
        ),
    )


def _to_analyze_response(job: AnalysisJob) -> AnalyzeTriggerResponse:
    return AnalyzeTriggerResponse(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status,
        agents=_to_agents_status(job),
        created_at=job.created_at,
    )


def _to_job_detail(job: AnalysisJob) -> JobDetailResponse:
    show_counts = job.status in {
        JobStatus.COMPLETED,
        JobStatus.PARTIALLY_FAILED,
        JobStatus.FAILED,
    }
    return JobDetailResponse(
        job_id=job.id,
        document_id=job.document_id,
        document_name=job.document.filename,
        status=job.status,
        agents=_to_agents_detail(job),
        agents_completed=job.agents_completed if show_counts else None,
        agents_failed=job.agents_failed if show_counts else None,
        total_processing_time_seconds=job.total_processing_time_seconds,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def _to_job_list_item(job: AnalysisJob) -> JobListItem:
    return JobListItem(
        job_id=job.id,
        document_id=job.document_id,
        document_name=job.document.filename,
        status=job.status,
        agents_completed=job.agents_completed,
        agents_failed=job.agents_failed,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def create_analysis_job(db: Session, document_id: str) -> AnalyzeTriggerResponse:
    document = db.get(Document, document_id)
    if document is None:
        logger.warning("Analysis rejected: document not found id=%s", document_id)
        raise JobServiceError("Document not found")

    job_id = generate_job_id()
    now = datetime.now(UTC)

    job = AnalysisJob(
        id=job_id,
        document_id=document_id,
        status=JobStatus.PROCESSING,
        agents_completed=0,
        agents_failed=0,
    )
    db.add(job)

    for agent_name in AGENT_ORDER:
        db.add(
            AgentRun(
                job_id=job_id,
                agent_name=agent_name,
                status=AgentStatus.RUNNING,
                started_at=now,
            )
        )

    document.analysis_count += 1
    db.commit()

    job = db.scalar(_get_job_query().where(AnalysisJob.id == job_id))
    if job is None:
        logger.error("Failed to reload analysis job id=%s after creation", job_id)
        raise JobServiceError("Failed to create analysis job", status_code=500)

    logger.info(
        "Analysis job created: job_id=%s document_id=%s filename=%s analysis_count=%d",
        job.id,
        document_id,
        document.filename,
        document.analysis_count,
    )
    return _to_analyze_response(job)


def get_job(db: Session, job_id: str) -> JobDetailResponse:
    job = db.scalar(_get_job_query().where(AnalysisJob.id == job_id))
    if job is None:
        logger.warning("Job lookup failed: id=%s not found", job_id)
        raise JobServiceError("Job not found")
    return _to_job_detail(job)


def list_jobs(db: Session) -> JobListResponse:
    jobs = db.scalars(
        _get_job_query().order_by(AnalysisJob.created_at.desc())
    ).all()
    return JobListResponse(jobs=[_to_job_list_item(job) for job in jobs])
