from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import AgentStatus, JobStatus
from app.schemas.agent_results import (
    DocumentClassifierResult,
    EntityExtractorResult,
    SentimentAnalyzerResult,
    SummarizerResult,
)


class AgentStatusResponse(BaseModel):
    status: AgentStatus


class SummarizerAgentResponse(BaseModel):
    status: AgentStatus
    processing_time_seconds: float | None = None
    result: SummarizerResult | None = None
    error: str | None = None


class EntityExtractorAgentResponse(BaseModel):
    status: AgentStatus
    processing_time_seconds: float | None = None
    result: EntityExtractorResult | None = None
    error: str | None = None


class SentimentAnalyzerAgentResponse(BaseModel):
    status: AgentStatus
    processing_time_seconds: float | None = None
    result: SentimentAnalyzerResult | None = None
    error: str | None = None


class DocumentClassifierAgentResponse(BaseModel):
    status: AgentStatus
    processing_time_seconds: float | None = None
    result: DocumentClassifierResult | None = None
    error: str | None = None


class AgentsStatusResponse(BaseModel):
    summarizer: AgentStatusResponse
    entity_extractor: AgentStatusResponse
    sentiment_analyzer: AgentStatusResponse
    document_classifier: AgentStatusResponse


class AgentsDetailResponse(BaseModel):
    summarizer: SummarizerAgentResponse
    entity_extractor: EntityExtractorAgentResponse
    sentiment_analyzer: SentimentAnalyzerAgentResponse
    document_classifier: DocumentClassifierAgentResponse


class AnalyzeTriggerResponse(BaseModel):
    job_id: str
    document_id: str
    status: JobStatus
    agents: AgentsStatusResponse
    created_at: datetime


class JobDetailResponse(BaseModel):
    job_id: str
    document_id: str
    document_name: str
    status: JobStatus
    agents: AgentsDetailResponse
    agents_completed: int | None = Field(default=None, ge=0)
    agents_failed: int | None = Field(default=None, ge=0)
    total_processing_time_seconds: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


class JobListItem(BaseModel):
    job_id: str
    document_id: str
    document_name: str
    status: JobStatus
    agents_completed: int
    agents_failed: int
    created_at: datetime
    completed_at: datetime | None = None


class JobListResponse(BaseModel):
    jobs: list[JobListItem]
