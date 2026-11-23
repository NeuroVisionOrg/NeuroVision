"""Comprobación de disponibilidad sin depender de capas especializadas."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Indica que el servidor responde; no afirma que el MVP esté implementado."""
    return {"service": "neurovision", "status": "ok"}
