"""Composición HTTP mínima; no ejecuta todavía segmentación."""

from fastapi import FastAPI

from capa_2_control.api.errores import registrar_errores
from capa_2_control.api.frontera_http import HTTPBoundary
from capa_2_control.api.health import router as health_router
from capa_2_control.api.previsualizacion import crear_router_preview
from capa_2_control.casos_uso.previsualizacion import PreviewOperations
from capa_2_control.recursos import ResourceLimits


def create_app(
    limits: ResourceLimits | None = None, *, translation: PreviewOperations | None = None
) -> FastAPI:
    """Solo registra previsualizacion con limites y Traduccion configurados."""
    if translation is not None and limits is None:
        raise ValueError("la previsualizacion requiere limites explicitos")
    app = FastAPI(title="NeuroVision", version="0.1.0")
    registrar_errores(app)
    app.add_middleware(HTTPBoundary, limits=limits)
    app.include_router(health_router, prefix="/api/v1")
    if limits is not None and translation is not None:
        app.include_router(crear_router_preview(limits, translation), prefix="/api/v1")
    return app
