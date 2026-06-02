from fastapi import FastAPI

from app.api.v1.routes import api_router

app = FastAPI(
    title="Document Intelligence API",
    description="Multi-agent document analysis service",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
