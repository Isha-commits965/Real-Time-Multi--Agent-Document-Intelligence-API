import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.db.models.agent_run import AgentRun
from app.db.models.analysis_job import AnalysisJob
from app.db.models.document import Document
from app.db.models.enums import AgentName, AgentStatus, JobStatus
from app.db.session import SessionLocal
from app.services.agents import document_classifier, entity_extractor, sentiment_analyzer, summarizer
from app.services.llm_client import LLMError

AGENT_HANDLERS: dict[AgentName, Callable[[str], Awaitable[dict]]] = {
    AgentName.SUMMARIZER: summarizer.analyze,
    AgentName.ENTITY_EXTRACTOR: entity_extractor.analyze,
    AgentName.SENTIMENT_ANALYZER: sentiment_analyzer.analyze,
    AgentName.DOCUMENT_CLASSIFIER: document_classifier.analyze,
}

STUB_DELAYS: dict[AgentName, float] = {
    AgentName.SUMMARIZER: 1.0,
    AgentName.ENTITY_EXTRACTOR: 2.0,
    AgentName.SENTIMENT_ANALYZER: 1.5,
    AgentName.DOCUMENT_CLASSIFIER: 0.8,
}


def _truncate_text(text: str) -> str:
    if len(text) <= settings.max_document_chars:
        return text
    return text[: settings.max_document_chars]


def _stub_result(agent_name: AgentName, text: str) -> dict[str, Any]:
    excerpt = text[:120].strip() or "Sample document excerpt."

    if agent_name == AgentName.SUMMARIZER:
        return {
            "summary": excerpt[:300],
            "key_points": [
                "Document uploaded for analysis",
                "Key terms and obligations identified",
                "Review recommended before final approval",
            ],
            "confidence": 0.85,
        }

    if agent_name == AgentName.ENTITY_EXTRACTOR:
        return {
            "people": [{"name": "Unknown Party", "role": None, "mentions": 1}],
            "organizations": [],
            "dates": [],
            "locations": [],
            "monetary_values": [],
        }

    if agent_name == AgentName.SENTIMENT_ANALYZER:
        return {
            "sentiment": "neutral",
            "tone": "formal",
            "urgency": "routine",
            "confidence": 0.82,
            "supporting_excerpts": [excerpt],
        }

    return {
        "category": "Other",
        "confidence": 0.78,
        "rationale": "Stub analysis — set OPENAI_API_KEY for real classification.",
    }


async def _run_stub_agent(job_id: str, agent_name: AgentName, text: str) -> None:
    started = time.perf_counter()
    await asyncio.sleep(STUB_DELAYS[agent_name])
    processing_time = round(time.perf_counter() - started, 1)
    _save_agent_success(job_id, agent_name, processing_time, _stub_result(agent_name, text))


async def _run_agent(job_id: str, agent_name: AgentName, text: str) -> None:
    if settings.force_agent_failure == agent_name.value:
        _save_agent_failure(job_id, agent_name, 0.0, "Forced agent failure")
        return

    if not settings.openai_api_key:
        await _run_stub_agent(job_id, agent_name, text)
        return

    started = time.perf_counter()
    try:
        handler = AGENT_HANDLERS[agent_name]
        result = await handler(text)
        processing_time = round(time.perf_counter() - started, 1)
        _save_agent_success(job_id, agent_name, processing_time, result)
    except (LLMError, ValueError) as exc:
        processing_time = round(time.perf_counter() - started, 1)
        _save_agent_failure(job_id, agent_name, processing_time, str(exc))


def _save_agent_success(
    job_id: str,
    agent_name: AgentName,
    processing_time: float,
    result: dict[str, Any],
) -> None:
    db = SessionLocal()
    try:
        run = db.scalar(
            select(AgentRun).where(
                AgentRun.job_id == job_id,
                AgentRun.agent_name == agent_name,
            )
        )
        if run is None:
            return
        run.status = AgentStatus.COMPLETED
        run.result = result
        run.processing_time_seconds = processing_time
        run.completed_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


def _save_agent_failure(
    job_id: str,
    agent_name: AgentName,
    processing_time: float,
    error: str,
) -> None:
    db = SessionLocal()
    try:
        run = db.scalar(
            select(AgentRun).where(
                AgentRun.job_id == job_id,
                AgentRun.agent_name == agent_name,
            )
        )
        if run is None:
            return
        run.status = AgentStatus.FAILED
        run.error = error
        run.processing_time_seconds = processing_time
        run.completed_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


def _finalize_job(job_id: str, total_seconds: float) -> None:
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return

        runs = db.scalars(select(AgentRun).where(AgentRun.job_id == job_id)).all()
        completed = sum(1 for r in runs if r.status == AgentStatus.COMPLETED)
        failed = sum(1 for r in runs if r.status == AgentStatus.FAILED)

        job.agents_completed = completed
        job.agents_failed = failed
        job.total_processing_time_seconds = round(total_seconds, 1)
        job.completed_at = datetime.now(UTC)

        if failed == 0:
            job.status = JobStatus.COMPLETED
        elif completed == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIALLY_FAILED

        db.commit()
    finally:
        db.close()


async def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return
        document = db.get(Document, job.document_id)
        if document is None:
            return
        text = _truncate_text(document.text_content)
    finally:
        db.close()

    started = time.perf_counter()
    await asyncio.gather(
        _run_agent(job_id, AgentName.SUMMARIZER, text),
        _run_agent(job_id, AgentName.ENTITY_EXTRACTOR, text),
        _run_agent(job_id, AgentName.SENTIMENT_ANALYZER, text),
        _run_agent(job_id, AgentName.DOCUMENT_CLASSIFIER, text),
        return_exceptions=True,
    )
    _finalize_job(job_id, time.perf_counter() - started)
