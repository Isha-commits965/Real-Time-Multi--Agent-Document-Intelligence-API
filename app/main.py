from pathlib import Path

from fastapi import FastAPI

from app.api.v1.routes import api_router
from app.core.config import settings

app = FastAPI(
    title="Document Intelligence API",
    description="Multi-agent document analysis service",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
