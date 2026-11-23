"""Punto de entrada ASGI: uvicorn main:app --reload."""

from capa_2_control.api.app import create_app

app = create_app()
