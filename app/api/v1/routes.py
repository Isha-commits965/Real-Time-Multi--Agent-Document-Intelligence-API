from fastapi import APIRouter

from app.api.v1.controllers import documents, jobs

api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(jobs.router, tags=["jobs"])
