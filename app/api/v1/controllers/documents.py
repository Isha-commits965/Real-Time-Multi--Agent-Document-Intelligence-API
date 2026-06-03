from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.common import get_db
from app.schemas.document import DocumentListResponse, DocumentUploadResponse
from app.services.document_service import DocumentServiceError, list_documents, upload_document

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    try:
        return await upload_document(db, file)
    except DocumentServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=DocumentListResponse)
def list_documents_endpoint(db: Session = Depends(get_db)) -> DocumentListResponse:
    return list_documents(db)
