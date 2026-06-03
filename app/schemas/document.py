from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import DocumentStatus, FileType


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: FileType
    word_count: int
    uploaded_at: datetime
    status: DocumentStatus


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    file_type: FileType
    word_count: int
    uploaded_at: datetime
    status: DocumentStatus
    analysis_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]
