from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import JobStatus

if TYPE_CHECKING:
    from app.db.models.agent_run import AgentRun
    from app.db.models.document import Document


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="jobstatus", native_enum=False),
        nullable=False,
        default=JobStatus.QUEUED,
    )
    agents_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agents_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_processing_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="analysis_jobs")
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
