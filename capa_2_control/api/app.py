"""Composición HTTP mínima; no ejecuta todavía segmentación."""

from fastapi import FastAPI

from capa_2_control.api.health import router as health_router


def create_app() -> FastAPI:
    """Construye la aplicación HTTP de la capa Control."""
    app = FastAPI(title="NeuroVision", version="0.1.0")
    app.include_router(health_router, prefix="/api/v1")
    return app
