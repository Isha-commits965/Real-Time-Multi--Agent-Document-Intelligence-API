"""initial schema: documents, analysis_jobs, agent_runs

Revision ID: a7b3c9d1e2f4
Revises:
Create Date: 2026-06-02 16:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b3c9d1e2f4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("pdf", "txt", name="filetype", native_enum=False),
            nullable=False,
        ),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ready", "processing", name="documentstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("analysis_count", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("document_id", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "processing",
                "completed",
                "partially_failed",
                "failed",
                name="jobstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("agents_completed", sa.Integer(), nullable=False),
        sa.Column("agents_failed", sa.Integer(), nullable=False),
        sa.Column("total_processing_time_seconds", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_document_id"), "analysis_jobs", ["document_id"], unique=False)
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=32), nullable=False),
        sa.Column(
            "agent_name",
            sa.Enum(
                "summarizer",
                "entity_extractor",
                "sentiment_analyzer",
                "document_classifier",
                name="agentname",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                name="agentstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("processing_time_seconds", sa.Float(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "agent_name", name="uq_agent_runs_job_agent"),
    )
    op.create_index(op.f("ix_agent_runs_job_id"), "agent_runs", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_runs_job_id"), table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index(op.f("ix_analysis_jobs_document_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_table("documents")
