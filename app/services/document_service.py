from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document
from app.db.models.enums import DocumentStatus, FileType
from app.schemas.document import DocumentListItem, DocumentListResponse, DocumentUploadResponse
from app.services.id_generator import generate_document_id
from app.services.text_extractor import TextExtractionError, count_words, extract_text_from_file


class DocumentServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _resolve_file_type(filename: str) -> FileType:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        return FileType.PDF
    if extension == ".txt":
        return FileType.TXT
    raise DocumentServiceError("Only PDF and TXT files are supported")


def _ensure_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _to_upload_response(document: Document) -> DocumentUploadResponse:
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        word_count=document.word_count,
        uploaded_at=document.uploaded_at,
        status=document.status,
    )


def _to_list_item(document: Document) -> DocumentListItem:
    return DocumentListItem(
        document_id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        word_count=document.word_count,
        uploaded_at=document.uploaded_at,
        status=document.status,
        analysis_count=document.analysis_count,
    )


async def upload_document(db: Session, file: UploadFile) -> DocumentUploadResponse:
    if not file.filename:
        raise DocumentServiceError("Filename is required")

    file_type = _resolve_file_type(file.filename)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()

    if not content:
        raise DocumentServiceError("Uploaded file is empty")
    if len(content) > max_bytes:
        raise DocumentServiceError(
            f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
            status_code=413,
        )

    document_id = generate_document_id()
    upload_dir = _ensure_upload_dir()
    stored_filename = f"{document_id}{Path(file.filename).suffix.lower()}"
    file_path = upload_dir / stored_filename
    file_path.write_bytes(content)

    try:
        text_content = extract_text_from_file(file_path, file_type)
    except TextExtractionError as exc:
        file_path.unlink(missing_ok=True)
        raise DocumentServiceError(str(exc)) from exc

    document = Document(
        id=document_id,
        filename=file.filename,
        file_type=file_type,
        word_count=count_words(text_content),
        text_content=text_content,
        file_path=str(file_path),
        status=DocumentStatus.READY,
        analysis_count=0,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _to_upload_response(document)


def list_documents(db: Session) -> DocumentListResponse:
    documents = db.scalars(select(Document).order_by(Document.uploaded_at.desc())).all()
    return DocumentListResponse(documents=[_to_list_item(doc) for doc in documents])


def get_document_or_none(db: Session, document_id: str) -> Document | None:
    return db.get(Document, document_id)
