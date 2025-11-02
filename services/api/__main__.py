"""Entrypoint for running the FastAPI service with uvicorn."""

import uvicorn

from services.api.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "services.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
    )
