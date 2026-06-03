from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import DocumentStatus, FileType

if TYPE_CHECKING:
    from app.db.models.analysis_job import AnalysisJob


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="filetype", native_enum=False),
        nullable=False,
    )
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="documentstatus", native_enum=False),
        nullable=False,
        default=DocumentStatus.READY,
    )
    analysis_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
