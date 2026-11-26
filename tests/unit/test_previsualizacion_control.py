"""Pruebas del puerto y de la ruta HTTP. Los datos NO son imagenes decodificadas."""

import asyncio
import base64
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from threading import Event, get_ident
from typing import Literal

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from capa_2_control.api.app import create_app
from capa_2_control.recursos import ResourceLimits
from contratos.admision import DataReadCode, DataReadError, DataReadLimits
from contratos.datos import DecodedData, PreviewData
from contratos.geometria import InputGeometry, InputMode, SpatialGeometry

_CONTENT = b"fixture-sintetico-no-es-una-imagen"
_PATH = "/api/v1/previsualizar"


@pytest.fixture
def limits() -> ResourceLimits:
    return ResourceLimits(
        max_request_bytes=4096,
        max_file_bytes=128,
        max_json_bytes=256,
        max_decompressed_bytes=512,
        max_axis_length=8,
        max_domain_elements=128,
        max_roi_elements=64,
        max_unknowns=62,
        max_seeds=8,
        max_iterations=10,
        max_array_bytes=128,
        max_response_bytes=4096,
        max_concurrent_requests=1,
    )


def _geometry(mode: InputMode) -> InputGeometry:
    if mode == InputMode.TWO_D:
        return InputGeometry(mode, (2, 3), (2, 3), "PNG")
    affine = np.eye(4, dtype=np.float64)
    spatial = SpatialGeometry(
        h_original=affine,
        h_work=affine,
        t_work_to_original=np.eye(4, dtype=np.int64),
        spacing_mm=(1.0, 1.0, 1.0),
        axis_codes=("R", "A", "S"),
        affine_source="fixture",
        atol_mm=1e-8,
    )
    return InputGeometry(mode, (2, 3, 4), (2, 3, 4), "NIfTI", spatial)


class TranslationDouble:
    """Doble explicito. No comprueba formatos, no normaliza datos reales."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.received_limits: DataReadLimits | None = None
        self.read_code: DataReadCode | None = None
        self.read_failure = False
        self.read_mismatch: Literal["mode", "digest", "shape"] | None = None
        self.preview_mismatch: Literal["digest", "geometry", "affine"] | None = None
        self.worker_ids: list[int] = []
        self.entered = Event()
        self.release: Event | None = None

    def leer_datos(self, content: bytes, mode: InputMode, *, limits: DataReadLimits) -> DecodedData:
        self.calls.append("leer")
        self.worker_ids.append(get_ident())
        self.received_limits = limits
        self.entered.set()
        if self.release is not None and not self.release.wait(timeout=10):
            raise RuntimeError("fixture timeout")
        if self.read_code is not None:
            raise DataReadError(self.read_code)
        if self.read_failure:
            raise ValueError("dato privado que no debe aparecer en HTTP")
        if self.read_mismatch == "mode":
            mode = InputMode.THREE_D if mode == InputMode.TWO_D else InputMode.TWO_D
        geometry = _geometry(mode)
        if self.read_mismatch == "shape":
            geometry = InputGeometry(InputMode.TWO_D, (9, 2), (9, 2), "PNG")
        source_digest = "0" * 64 if self.read_mismatch == "digest" else sha256(content).hexdigest()
        return DecodedData(
            geometry,
            np.arange(np.prod(geometry.work_shape), dtype=np.float32).reshape(geometry.work_shape),
            source_digest,
        )

    def previsualizar(self, data: DecodedData) -> PreviewData:
        self.calls.append("preview")
        self.worker_ids.append(get_ident())
        geometry = data.geometry
        if self.preview_mismatch == "geometry":
            geometry = InputGeometry(InputMode.TWO_D, (3, 2), (3, 2), "PNG")
        if self.preview_mismatch == "affine":
            assert geometry.spatial is not None
            translated = geometry.spatial.h_work.copy()
            translated[0, 3] = 1.0
            spatial = replace(geometry.spatial, h_work=translated, h_original=translated)
            geometry = replace(geometry, spatial=spatial)
        return PreviewData(
            geometry=geometry,
            uint8_view=np.arange(np.prod(geometry.work_shape), dtype=np.uint8).reshape(
                geometry.work_shape
            ),
            display_min=0.0,
            display_max=float(np.prod(geometry.work_shape) - 1),
            input_id="0" * 64 if self.preview_mismatch == "digest" else data.source_digest,
            preparation_version="fixture-v1",
        )


def _request(mode: str = "2d", version: str = "2") -> str:
    return json.dumps({"contract_version": version, "mode": mode})


def _post(
    client: TestClient, *, content: bytes = _CONTENT, request: str | None = None
) -> httpx.Response:
    return client.post(
        _PATH,
        files={"image": ("private-name.bin", content, "application/octet-stream")},
        data={"request": _request() if request is None else request},
    )


@pytest.mark.parametrize("mode,shape", [("2d", [2, 3]), ("3d", [2, 3, 4])])
def test_preview_http_con_doble(mode: str, shape: list[int], limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    client = TestClient(create_app(limits, translation=translation))
    response = client.post(
        _PATH,
        files={"image": ("private-name.bin", _CONTENT, "application/octet-stream")},
        data={"request": _request(mode)},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert data["contract_version"] == "2"
    assert data["input_id"] == sha256(_CONTENT).hexdigest()
    assert data["preparation_version"] == "fixture-v1"
    assert data["geometry"]["mode"] == mode
    assert data["view"]["shape"] == shape
    assert base64.b64decode(data["view"]["data"]) == bytes(range(int(np.prod(shape))))
    assert translation.calls == ["leer", "preview"]
    assert translation.received_limits == DataReadLimits(
        max_axis_length=limits.max_axis_length,
        max_domain_elements=limits.max_domain_elements,
        max_decompressed_bytes=limits.max_decompressed_bytes,
    )
    assert "private-name" not in response.text
    if mode == "3d":
        assert data["geometry"]["H_work"] == np.eye(4).tolist()
        assert data["geometry"]["axis_codes"] == ["R", "A", "S"]
    else:
        assert "H_work" not in data["geometry"]


@pytest.mark.parametrize(
    "field", ["max_axis_length", "max_domain_elements", "max_decompressed_bytes"]
)
@pytest.mark.parametrize("value", [0, -1, True, 2.5])
def test_presupuesto_lector_estricto(field: str, value: object) -> None:
    values: dict[str, object] = {
        "max_axis_length": 8,
        "max_domain_elements": 64,
        "max_decompressed_bytes": 256,
    }
    values[field] = value
    with pytest.raises(ValueError, match="enteros positivos"):
        DataReadLimits(**values)


def test_sin_traduccion_no_publica_preview(limits: ResourceLimits) -> None:
    assert _PATH not in create_app().openapi()["paths"]
    assert _PATH not in create_app(limits).openapi()["paths"]
    with pytest.raises(ValueError, match="limites explicitos"):
        create_app(translation=TranslationDouble())


@pytest.mark.parametrize(
    "code,status",
    [
        (DataReadCode.UNSUPPORTED_FORMAT, 415),
        (DataReadCode.INVALID_IMAGE, 422),
        (DataReadCode.UNSUPPORTED_COLOR, 422),
        (DataReadCode.UNSUPPORTED_GEOMETRY, 422),
        (DataReadCode.DECOMPRESSED_LIMIT, 413),
    ],
)
def test_error_tipado_lector(code: DataReadCode, status: int, limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    translation.read_code = code
    client = TestClient(create_app(limits, translation=translation))
    response = _post(client)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code.value
    assert translation.calls == ["leer"]


@pytest.mark.parametrize(
    "mode,version,code",
    [("2d", "1", "UNSUPPORTED_CONTRACT_VERSION"), ("4d", "2", "MALFORMED_REQUEST")],
)
def test_version_y_modo_no_llaman_lector(
    mode: str, version: str, code: str, limits: ResourceLimits
) -> None:
    translation = TranslationDouble()
    client = TestClient(create_app(limits, translation=translation))
    response = _post(client, request=_request(mode, version))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == code
    assert translation.calls == []


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("max_request_bytes", 10, "PAYLOAD_LIMIT"),
        ("max_file_bytes", 1, "FILE_TOO_LARGE"),
        ("max_json_bytes", 1, "PAYLOAD_LIMIT"),
    ],
)
def test_presupuesto_antes_de_lector(
    field: str, value: int, code: str, limits: ResourceLimits
) -> None:
    translation = TranslationDouble()
    client = TestClient(create_app(replace(limits, **{field: value}), translation=translation))
    response = _post(client)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == code
    assert translation.calls == []


@pytest.mark.parametrize("mismatch,status", [("mode", 500), ("digest", 500), ("shape", 413)])
def test_datos_incompatibles_no_generan_vista(
    mismatch: Literal["mode", "digest", "shape"], status: int, limits: ResourceLimits
) -> None:
    translation = TranslationDouble()
    translation.read_mismatch = mismatch
    response = _post(TestClient(create_app(limits, translation=translation)))
    assert response.status_code == status
    assert translation.calls == ["leer"]


@pytest.mark.parametrize("mismatch,mode", [("digest", "2d"), ("geometry", "2d"), ("affine", "3d")])
def test_vista_incompatible_no_se_envia(
    mismatch: Literal["digest", "geometry", "affine"], mode: str, limits: ResourceLimits
) -> None:
    translation = TranslationDouble()
    translation.preview_mismatch = mismatch
    client = TestClient(create_app(limits, translation=translation))
    response = _post(client, request=_request(mode))
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "view" not in response.json()


@pytest.mark.parametrize("field", ["max_array_bytes", "max_response_bytes"])
def test_presupuesto_de_salida(field: str, limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    client = TestClient(create_app(replace(limits, **{field: 1}), translation=translation))
    response = _post(client)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_LIMIT"
    assert translation.calls == ["leer", "preview"]


def test_error_inesperado_no_filtra_detalles_y_libera_cupo(limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    translation.read_failure = True
    client = TestClient(create_app(limits, translation=translation))
    response = _post(client)
    assert response.status_code == 500
    assert "dato privado" not in response.text
    assert "Traceback" not in response.text
    translation.read_failure = False
    assert _post(client).status_code == 200


@pytest.mark.parametrize(
    "variant", ["json", "sin_request", "duplicado", "campo_extra", "imagen_texto"]
)
def test_multipart_invalido(variant: str, limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    client = TestClient(create_app(limits, translation=translation))
    files = [("image", ("fixture.bin", _CONTENT)), ("request", (None, _request()))]
    if variant == "json":
        response = client.post(_PATH, json={"image": "fixture", "request": _request()})
    else:
        if variant == "sin_request":
            files.pop()
        elif variant == "duplicado":
            files.append(("request", (None, _request())))
        elif variant == "campo_extra":
            files.append(("extra", (None, "private")))
        else:
            files[0] = ("image", (None, "texto"))
        response = client.post(_PATH, files=files)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MALFORMED_REQUEST"
    assert translation.calls == []


def test_cupo_ocupado_y_recuperacion(limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    translation.release = Event()
    app = create_app(limits, translation=translation)
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(_post, client)
        try:
            assert translation.entered.wait(timeout=5)
            busy = _post(client)
            assert busy.status_code == 503
            assert busy.json()["error"]["code"] == "RESOURCE_BUSY"
            assert translation.calls == ["leer"]
        finally:
            translation.release.set()
        assert first.result(timeout=10).status_code == 200
        assert _post(client).status_code == 200


def test_openapi_describe_multipart(limits: ResourceLimits) -> None:
    app = create_app(limits, translation=TranslationDouble())
    body = app.openapi()["paths"][_PATH]["post"]["requestBody"]
    schema = body["content"]["multipart/form-data"]["schema"]
    assert schema["properties"]["image"]["format"] == "binary"
    assert schema["required"] == ["image", "request"]


@pytest.mark.parametrize("fail", [False, True])
def test_archivo_se_cierra_en_exito_y_error(
    fail: bool, limits: ResourceLimits, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[bool] = []
    original_close = UploadFile.close

    async def track_close(upload: UploadFile) -> None:
        await original_close(upload)
        closed.append(upload.file.closed)

    monkeypatch.setattr(UploadFile, "close", track_close)
    translation = TranslationDouble()
    translation.read_failure = fail
    response = _post(TestClient(create_app(limits, translation=translation)))
    assert response.status_code == (500 if fail else 200)
    assert closed == [True]


def test_lectura_y_vista_fuera_del_event_loop(limits: ResourceLimits) -> None:
    translation = TranslationDouble()
    app = create_app(limits, translation=translation)

    async def invoke() -> None:
        loop_thread = get_ident()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                _PATH,
                files={"image": ("fixture.bin", _CONTENT)},
                data={"request": _request()},
            )
        assert response.status_code == 200
        assert len(translation.worker_ids) == 2
        assert all(worker != loop_thread for worker in translation.worker_ids)

    asyncio.run(invoke())
