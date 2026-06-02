from datetime import datetime
from typing import TYPE_CHECKING, Any
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.db.base import Base
from app.db.models.enums import AgentName, AgentStatus

if TYPE_CHECKING:
    from app.db.models.analysis_job import AnalysisJob


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (UniqueConstraint("job_id", "agent_name", name="uq_agent_runs_job_agent"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[AgentName] = mapped_column(
        Enum(AgentName, name="agentname", native_enum=False),
        nullable=False,
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agentstatus", native_enum=False),
        nullable=False,
        default=AgentStatus.PENDING,
    )
    processing_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped["AnalysisJob"] = relationship(back_populates="agent_runs")
