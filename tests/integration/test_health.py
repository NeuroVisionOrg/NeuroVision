"""Prueba HTTP mínima para verificar la composición FastAPI."""

import pytest
from fastapi.testclient import TestClient

from capa_2_control.api.app import create_app


@pytest.mark.integration
def test_health_http() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"service": "neurovision", "status": "ok"}
