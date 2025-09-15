from __future__ import annotations

from fastapi import FastAPI
from app.core.config import get_settings
from app.api.health import router as health_router

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router, prefix=settings.api_prefix)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": f"{settings.app_name} is running"}

    return app

app = create_app()