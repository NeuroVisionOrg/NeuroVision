"""CT-01/03/07/10: frontera HTTP, sin lectores ni solver ficticios."""

import asyncio
import json
from collections.abc import Sequence
from dataclasses import replace
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import File, Form, HTTPException, UploadFile
from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from capa_2_control.api.app import create_app
from capa_2_control.api.dto_entrada import PreviewRequest
from capa_2_control.api.errores import (
    MALFORMED,
    RequestContractError,
    error_recursos,
    parsear_preview_http,
    parsear_segmentacion_http,
)
from capa_2_control.api.frontera_http import HTTPBoundary
from capa_2_control.recursos import ResourceCode, ResourceLimitError, ResourceLimits


@pytest.fixture
def limits() -> ResourceLimits:
    return ResourceLimits(
        max_request_bytes=1024,
        max_file_bytes=128,
        max_json_bytes=512,
        max_decompressed_bytes=512,
        max_axis_length=8,
        max_domain_elements=128,
        max_roi_elements=64,
        max_unknowns=62,
        max_seeds=8,
        max_iterations=10,
        max_array_bytes=128,
        max_response_bytes=4096,
        max_concurrent_requests=2,
    )


@pytest.mark.parametrize(
    "code,status,stage",
    [
        (ResourceCode.FILE_TOO_LARGE, 413, "request"),
        (ResourceCode.DECOMPRESSED_LIMIT, 413, "input"),
        (ResourceCode.ROI_LIMIT, 413, "selection"),
        (ResourceCode.PAYLOAD_LIMIT, 413, "request"),
        (ResourceCode.INVALID_SOLVER_CONFIG, 422, "solver"),
        (ResourceCode.RESOURCE_BUSY, 503, "control"),
    ],
)
def test_mapear_recursos_sin_exponer_mensaje(code: ResourceCode, status: int, stage: str) -> None:
    error = error_recursos(ResourceLimitError(code, "contenido privado"))
    response = error.response()
    assert response.status_code == status
    payload = json.loads(bytes(response.body))
    assert payload["contract_version"] == "2"
    assert payload["error"]["code"] == code.value
    assert payload["error"]["stage"] == stage
    assert payload["error"]["request_id"] is None
    assert b"contenido privado" not in response.body
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "content,code",
    [
        (b'{"contract_version":"1","mode":"2d"}', "UNSUPPORTED_CONTRACT_VERSION"),
        (b'{"contract_version":2,"mode":"2d"}', "UNSUPPORTED_CONTRACT_VERSION"),
        (b'{"contract_version":"2","mode":"4d"}', "MALFORMED_REQUEST"),
        (b'{"contract_version":"2","mode":"2d","private":"file"}', "MALFORMED_REQUEST"),
        (b'{"contract_version":"2",', "MALFORMED_REQUEST"),
        (b'{"mode":"2d"}', "MALFORMED_REQUEST"),
    ],
)
def test_preview_error_publico(content: bytes, code: str, limits: ResourceLimits) -> None:
    with pytest.raises(RequestContractError) as error:
        parsear_preview_http(content, limits)
    assert error.value.public.code == code
    assert error.value.public.status == 400
    assert "private" not in str(error.value)


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_preview_request_valido(mode: str, limits: ResourceLimits) -> None:
    content = json.dumps({"contract_version": "2", "mode": mode}).encode()
    assert parsear_preview_http(content, limits).mode == mode


def _segment_request() -> dict[str, object]:
    return {
        "contract_version": "2",
        "request_id": str(UUID(int=1, version=4)),
        "input_id": "0" * 64,
        "preparation_version": "1",
        "mode": "2d",
        "work_shape": [3, 3],
        "roi": {"x_min": 0, "y_min": 0, "x_max": 3, "y_max": 3},
        "seeds": [
            {"x": 0, "y": 0, "label": "background"},
            {"x": 2, "y": 2, "label": "foreground"},
        ],
        "model": {"beta": 0, "threshold": 0.5},
        "solver": {"omega": 1.2, "rtol": 1e-6, "atol": 1e-10, "max_iterations": 10},
    }


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("contract_version", "1", "UNSUPPORTED_CONTRACT_VERSION"),
        ("solver", {"omega": 3}, "INVALID_SOLVER_CONFIG"),
        ("model", {"beta": -1, "threshold": 0.5}, "INVALID_MODEL_CONFIG"),
        ("roi", {"x_min": -1}, "INVALID_ROI"),
        ("roi", {"i_min": 0}, "MALFORMED_REQUEST"),
        ("seeds", [], "MALFORMED_REQUEST"),
        ("mode", "4d", "MALFORMED_REQUEST"),
    ],
)
def test_segment_error_publico(
    field: str, value: object, code: str, limits: ResourceLimits
) -> None:
    content = json.dumps(_segment_request() | {field: value}).encode()
    with pytest.raises(RequestContractError) as error:
        parsear_segmentacion_http(content, limits)
    assert error.value.public.code == code


def test_segment_request_valido(limits: ResourceLimits) -> None:
    result = parsear_segmentacion_http(json.dumps(_segment_request()).encode(), limits)
    assert result.mode == "2d"
    assert result.solver.max_iterations == 10


def test_presupuesto_json_se_mantiene(limits: ResourceLimits) -> None:
    with pytest.raises(ResourceLimitError) as error:
        parsear_preview_http(b" " * (limits.max_json_bytes + 1), limits)
    assert error.value.code == ResourceCode.PAYLOAD_LIMIT


def _simular_asgi(
    limits: ResourceLimits,
    headers: Sequence[tuple[bytes, bytes]],
    messages: list[Message],
) -> tuple[list[Message], list[bytes], int]:
    responses: list[Message] = []
    bodies: list[bytes] = []
    reads = 0
    scope: Scope = {
        "type": "http",
        "path": "/api/v1/previsualizar",
        "method": "POST",
        "headers": list(headers),
    }
    incoming = iter(messages)

    async def receive() -> Message:
        nonlocal reads
        reads += 1
        return next(incoming)

    async def send(message: Message) -> None:
        responses.append(message)

    async def probe(_scope: Scope, replay: Receive, send_message: Send) -> None:
        event = await replay()
        assert not event.get("more_body", False)
        bodies.append(event["body"])
        await send_message({"type": "http.response.start", "status": 200, "headers": []})
        await send_message({"type": "http.response.body", "body": b"ok"})

    asyncio.run(HTTPBoundary(probe, limits=limits)(scope, receive, send))
    return responses, bodies, reads


def _body(content: bytes, *, more: bool = False) -> Message:
    return {"type": "http.request", "body": content, "more_body": more}


@pytest.mark.parametrize("headers", [[], [(b"content-length", b"6")]])
def test_replay_fragmentos(headers: list[tuple[bytes, bytes]], limits: ResourceLimits) -> None:
    responses, bodies, reads = _simular_asgi(
        replace(limits, max_request_bytes=6), headers, [_body(b"abc", more=True), _body(b"def")]
    )
    assert bodies == [b"abcdef"]
    assert reads == 2
    assert responses[0]["status"] == 200
    assert (b"cache-control", b"no-store") in responses[0]["headers"]


@pytest.mark.parametrize("declared", [b"7", b"9" * 5000])
def test_header_excesivo_no_lee_cuerpo(declared: bytes, limits: ResourceLimits) -> None:
    responses, bodies, reads = _simular_asgi(
        replace(limits, max_request_bytes=6), [(b"content-length", declared)], []
    )
    assert not bodies
    assert reads == 0
    assert responses[0]["status"] == 413


@pytest.mark.parametrize("declared", [[], [(b"content-length", b"6")]])
def test_fragmentos_excesivos_no_llegan_al_parser(
    declared: list[tuple[bytes, bytes]], limits: ResourceLimits
) -> None:
    responses, bodies, reads = _simular_asgi(
        replace(limits, max_request_bytes=6),
        declared,
        [_body(b"abcd", more=True), _body(b"efg", more=True)],
    )
    assert not bodies
    assert reads == 2
    assert responses[0]["status"] == 413


@pytest.mark.parametrize(
    "headers,reads_expected",
    [
        ([(b"content-length", b"-1")], 0),
        ([(b"content-length", b"bad")], 0),
        ([(b"content-length", b"2"), (b"content-length", b"2")], 0),
        ([(b"content-length", b"3")], 1),
    ],
)
def test_longitud_invalida(
    headers: list[tuple[bytes, bytes]], reads_expected: int, limits: ResourceLimits
) -> None:
    responses, bodies, reads = _simular_asgi(limits, headers, [_body(b"ab")])
    assert not bodies
    assert reads == reads_expected
    assert responses[0]["status"] == 400


def test_desconexion_no_llega_al_parser(limits: ResourceLimits) -> None:
    responses, bodies, reads = _simular_asgi(
        limits, [], [_body(b"a", more=True), {"type": "http.disconnect"}]
    )
    assert not responses
    assert not bodies
    assert reads == 2


def test_multipart_acotado_y_errores(limits: ResourceLimits) -> None:
    # Ruta exclusivamente de prueba: no lee imagen medica ni prepara una vista.
    app = create_app(limits)
    seen: list[str] = []

    @app.post("/api/v1/probe")
    def probe(
        image: Annotated[UploadFile, File()], request: Annotated[str, Form()]
    ) -> dict[str, object]:
        seen.append("called")
        dto = parsear_preview_http(request.encode(), limits)
        return {"mode": dto.mode, "size": image.size}

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/probe",
            files={"image": ("fixture.bin", b"abc")},
            data={"request": '{"contract_version":"2","mode":"2d"}'},
        )
        assert response.status_code == 200
        assert response.json() == {"mode": "2d", "size": 3}
        assert response.headers["cache-control"] == "no-store"
        too_large = client.post(
            "/api/v1/probe",
            files={"image": ("fixture.bin", b"x" * 1025)},
            data={"request": "{}"},
        )
        assert too_large.status_code == 413
        assert len(seen) == 1
        missing = client.post("/api/v1/probe", data={"request": "private"})
        assert missing.status_code == 400
        assert "private" not in missing.text
        invalid = client.post(
            "/api/v1/probe",
            files={"image": ("fixture.bin", b"abc")},
            data={"request": '{"contract_version":"1","mode":"2d"}'},
        )
        assert invalid.status_code == 400
        assert invalid.json()["error"]["code"] == "UNSUPPORTED_CONTRACT_VERSION"


@pytest.mark.parametrize(
    "kind,status,code",
    [
        ("resource", 503, "RESOURCE_BUSY"),
        ("request", 400, "MALFORMED_REQUEST"),
        ("http", 415, "UNSUPPORTED_FORMAT"),
        ("unexpected", 500, "INTERNAL_ERROR"),
        ("pydantic_internal", 500, "INTERNAL_ERROR"),
    ],
)
def test_errores_no_exponen_contenido(
    kind: str, status: int, code: str, limits: ResourceLimits, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app(limits)
    request_id = UUID(int=2, version=4)

    @app.post("/api/v1/probe")
    def probe() -> None:
        if kind == "resource":
            raise ResourceLimitError(ResourceCode.RESOURCE_BUSY, "private")
        if kind == "request":
            raise RequestContractError(MALFORMED, request_id)
        if kind == "http":
            raise HTTPException(415, detail="private")
        if kind == "pydantic_internal":
            PreviewRequest.model_validate_json(b'{"contract_version":"private"}')
        raise RuntimeError("private")

    with TestClient(app) as client:
        response = client.post("/api/v1/probe")
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    expected_id = str(request_id) if kind == "request" else None
    assert response.json()["error"]["request_id"] == expected_id
    assert response.headers["cache-control"] == "no-store"
    assert "private" not in response.text
    assert "private" not in caplog.text


def test_app_sin_limites_no_publica_operaciones() -> None:
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json() == {"service": "neurovision", "status": "ok"}
        response = client.post("/api/v1/previsualizar")
        assert response.status_code == 404
        assert response.headers["cache-control"] == "no-store"
