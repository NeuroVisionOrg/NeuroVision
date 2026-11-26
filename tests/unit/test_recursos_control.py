"""CT-03/06/07: presupuestos sinteticos, sin fijar limites del producto."""

import json
from dataclasses import fields, replace
from io import BytesIO
from uuid import UUID

import numpy as np
import pytest

from capa_2_control.api import limites as api_limites
from capa_2_control.api.dto_entrada import SegmentRequest2D, SegmentRequest3D
from capa_2_control.api.dto_previsualizacion import PreviewDTO
from capa_2_control.api.limites import (
    parsear_preview_acotada,
    parsear_segmentacion_acotada,
    serializar_preview_acotada,
)
from capa_2_control.recursos import (
    ProcessingCapacity,
    ResourceCode,
    ResourceLimitError,
    ResourceLimits,
    leer_archivo_acotado,
    validar_datos_decodificados,
)
from contratos.datos import DecodedData, PreviewData
from contratos.geometria import InputGeometry, InputMode, SpatialGeometry


@pytest.fixture
def limits() -> ResourceLimits:
    return ResourceLimits(
        max_request_bytes=8192,
        max_file_bytes=8,
        max_json_bytes=2048,
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


@pytest.mark.parametrize("name", [field.name for field in fields(ResourceLimits)])
def test_todos_los_limites_son_positivos(limits: ResourceLimits, name: str) -> None:
    with pytest.raises(ValueError, match=name):
        replace(limits, **{name: 0})


@pytest.mark.parametrize("value", [-1, True, 1.5, "8", None])
def test_limites_no_coercitivos(limits: ResourceLimits, value: object) -> None:
    with pytest.raises(ValueError, match="max_file_bytes"):
        replace(limits, max_file_bytes=value)


@pytest.mark.parametrize(
    "method,field,code",
    [
        ("validar_cuerpo", "max_request_bytes", ResourceCode.PAYLOAD_LIMIT),
        ("validar_archivo", "max_file_bytes", ResourceCode.FILE_TOO_LARGE),
        ("validar_json", "max_json_bytes", ResourceCode.PAYLOAD_LIMIT),
        ("validar_descompresion", "max_decompressed_bytes", ResourceCode.DECOMPRESSED_LIMIT),
        ("validar_arreglo", "max_array_bytes", ResourceCode.PAYLOAD_LIMIT),
        ("validar_respuesta", "max_response_bytes", ResourceCode.PAYLOAD_LIMIT),
        ("validar_iteraciones", "max_iterations", ResourceCode.INVALID_SOLVER_CONFIG),
    ],
)
def test_fronteras_de_presupuesto(
    limits: ResourceLimits, method: str, field: str, code: ResourceCode
) -> None:
    validate = getattr(limits, method)
    bound = getattr(limits, field)
    validate(bound)
    with pytest.raises(ResourceLimitError) as error:
        validate(bound + 1)
    assert error.value.code == code


@pytest.mark.parametrize("value", [-1, True, 3.0, "3"])
def test_cantidad_invalida(limits: ResourceLimits, value: object) -> None:
    with pytest.raises(ValueError, match="cantidad entera"):
        limits.validar_archivo(value)


@pytest.mark.parametrize("shape", [(8, 8), (4, 4, 8)])
def test_formas_admitidas(limits: ResourceLimits, shape: tuple[int, ...]) -> None:
    limits.validar_forma(shape)


@pytest.mark.parametrize("shape", [(9, 1), (8, 8, 3)])
def test_limites_de_forma(limits: ResourceLimits, shape: tuple[int, ...]) -> None:
    with pytest.raises(ResourceLimitError) as error:
        limits.validar_forma(shape)
    assert error.value.code == ResourceCode.DECOMPRESSED_LIMIT


@pytest.mark.parametrize("shape", [(), (1,), (2, 0), (2, -1), (True, 2), (1, 1, 1, 1)])
def test_forma_invalida(limits: ResourceLimits, shape: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="forma espacial"):
        limits.validar_forma(shape)


def test_roi_en_limite(limits: ResourceLimits) -> None:
    limits.validar_roi(64, 2)
    limits.validar_roi(64, 8)


@pytest.mark.parametrize(
    "elements,seeds,message",
    [(65, 3, "ROI"), (16, 9, "semillas"), (64, 1, "incognitas")],
)
def test_presupuestos_de_seleccion(
    limits: ResourceLimits, elements: int, seeds: int, message: str
) -> None:
    with pytest.raises(ResourceLimitError, match=message) as error:
        limits.validar_roi(elements, seeds)
    assert error.value.code == ResourceCode.ROI_LIMIT


@pytest.mark.parametrize("elements,seeds", [(2, 2), (2, 3), (-1, 0), (4, -1)])
def test_cantidades_roi_invalidas(limits: ResourceLimits, elements: int, seeds: int) -> None:
    with pytest.raises(ValueError):
        limits.validar_roi(elements, seeds)


class ShortRead(BytesIO):
    """Un stream puede devolver menos bytes que los solicitados."""

    def read(self, size: int = -1) -> bytes:
        assert size > 0
        return super().read(min(size, 2))


@pytest.mark.parametrize("data", [b"", b"abc", b"12345678"])
def test_lectura_acotada_incluso_con_lecturas_cortas(limits: ResourceLimits, data: bytes) -> None:
    stream = ShortRead(data)
    assert leer_archivo_acotado(stream, limits) == data
    assert not stream.closed


def test_no_lee_archivo_entero_al_exceder_limite(limits: ResourceLimits) -> None:
    stream = ShortRead(b"a" * 100)
    with pytest.raises(ResourceLimitError) as error:
        leer_archivo_acotado(stream, limits)
    assert error.value.code == ResourceCode.FILE_TOO_LARGE
    assert stream.tell() == limits.max_file_bytes + 1
    assert not stream.closed


def test_cupo_se_agota_y_se_libera(limits: ResourceLimits) -> None:
    capacity = ProcessingCapacity(limits)
    with capacity.ocupar(), capacity.ocupar():
        with pytest.raises(ResourceLimitError) as error, capacity.ocupar():
            pytest.fail("no hay cupo disponible")
        assert error.value.code == ResourceCode.RESOURCE_BUSY
    with capacity.ocupar(), capacity.ocupar():
        pass


def test_cupo_se_libera_ante_excepcion(limits: ResourceLimits) -> None:
    capacity = ProcessingCapacity(replace(limits, max_concurrent_requests=1))
    with pytest.raises(RuntimeError, match="fallo de prueba"), capacity.ocupar():
        raise RuntimeError("fallo de prueba")
    with capacity.ocupar():
        pass


def test_cupos_pertenecen_a_instancias_distintas(limits: ResourceLimits) -> None:
    first = ProcessingCapacity(replace(limits, max_concurrent_requests=1))
    second = ProcessingCapacity(replace(limits, max_concurrent_requests=1))
    with first.ocupar(), second.ocupar():
        pass


def _segment_json(mode: str) -> bytes:
    common = {
        "contract_version": "2",
        "mode": mode,
        "request_id": str(UUID(int=1, version=4)),
        "input_id": "0" * 64,
        "preparation_version": "1",
        "model": {"beta": 0, "threshold": 0.5},
        "solver": {"omega": 1.2, "rtol": 1e-6, "atol": 1e-10, "max_iterations": 10},
    }
    if mode == "2d":
        selection = {
            "work_shape": [4, 4],
            "roi": {"x_min": 0, "y_min": 0, "x_max": 4, "y_max": 4},
            "seeds": [
                {"x": 0, "y": 0, "label": "background"},
                {"x": 3, "y": 3, "label": "foreground"},
            ],
        }
    else:
        selection = {
            "work_shape": [4, 4, 4],
            "roi": {"i_min": 0, "j_min": 0, "k_min": 0, "i_max": 4, "j_max": 4, "k_max": 4},
            "seeds": [
                {"i": 0, "j": 0, "k": 0, "label": "background"},
                {"i": 3, "j": 3, "k": 3, "label": "foreground"},
            ],
        }
    return json.dumps(common | selection).encode("utf-8")


def test_preview_request_acotada(limits: ResourceLimits) -> None:
    content = b'{"contract_version":"2","mode":"3d"}'
    dto = parsear_preview_acotada(content, replace(limits, max_json_bytes=len(content)))
    assert dto.mode == "3d"


def test_preview_rechaza_bytes_antes_de_validar(limits: ResourceLimits) -> None:
    content = b"no es JSON valido"
    with pytest.raises(ResourceLimitError) as error:
        parsear_preview_acotada(content, replace(limits, max_json_bytes=1))
    assert error.value.code == ResourceCode.PAYLOAD_LIMIT


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_segment_request_acotada(limits: ResourceLimits, mode: str) -> None:
    dto = parsear_segmentacion_acotada(_segment_json(mode), limits)
    assert isinstance(dto, SegmentRequest2D if mode == "2d" else SegmentRequest3D)
    assert dto.mode == mode


def test_segment_rechaza_bytes_antes_de_parsear(
    limits: ResourceLimits, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_parsear(_content: bytes) -> None:
        pytest.fail("el limite debe preceder al parser")

    monkeypatch.setattr(api_limites, "parsear_segment_request", no_parsear)
    with pytest.raises(ResourceLimitError) as error:
        parsear_segmentacion_acotada(b"{}", replace(limits, max_json_bytes=1))
    assert error.value.code == ResourceCode.PAYLOAD_LIMIT


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("max_axis_length", 3, ResourceCode.DECOMPRESSED_LIMIT),
        ("max_domain_elements", 63, ResourceCode.DECOMPRESSED_LIMIT),
        ("max_roi_elements", 63, ResourceCode.ROI_LIMIT),
        ("max_unknowns", 61, ResourceCode.ROI_LIMIT),
        ("max_seeds", 1, ResourceCode.ROI_LIMIT),
        ("max_iterations", 9, ResourceCode.INVALID_SOLVER_CONFIG),
    ],
)
def test_segment_rechaza_presupuestos_declarados(
    limits: ResourceLimits, field: str, value: int, code: ResourceCode
) -> None:
    with pytest.raises(ResourceLimitError) as error:
        parsear_segmentacion_acotada(_segment_json("3d"), replace(limits, **{field: value}))
    assert error.value.code == code


def _geometria(mode: InputMode) -> InputGeometry:
    if mode == InputMode.TWO_D:
        return InputGeometry(mode, (2, 3), (2, 3), "PNG")
    spatial = SpatialGeometry(
        h_original=np.eye(4, dtype=np.float64),
        h_work=np.eye(4, dtype=np.float64),
        t_work_to_original=np.eye(4, dtype=np.int64),
        spacing_mm=(1.0, 1.0, 1.0),
        axis_codes=("R", "A", "S"),
        affine_source="fixture",
        atol_mm=1e-6,
    )
    return InputGeometry(mode, (2, 3, 4), (2, 3, 4), "NIfTI", spatial)


@pytest.mark.parametrize("mode", list(InputMode))
def test_verifica_datos_decodificados(limits: ResourceLimits, mode: InputMode) -> None:
    geometry = _geometria(mode)
    intensities = np.zeros(geometry.work_shape, dtype=np.float64)
    data = DecodedData(geometry, intensities, "0" * 64)
    validar_datos_decodificados(data, replace(limits, max_decompressed_bytes=intensities.nbytes))
    with pytest.raises(ResourceLimitError) as error:
        validar_datos_decodificados(
            data, replace(limits, max_decompressed_bytes=intensities.nbytes - 1)
        )
    assert error.value.code == ResourceCode.DECOMPRESSED_LIMIT


def _preview(mode: InputMode) -> PreviewData:
    geometry = _geometria(mode)
    view = np.zeros(geometry.work_shape, dtype=np.uint8)
    return PreviewData(geometry, view, 0.0, 0.0, "0" * 64, "1", ("visi\u00f3n",))


@pytest.mark.parametrize("mode", list(InputMode))
def test_serializacion_exacta_con_presupuesto(limits: ResourceLimits, mode: InputMode) -> None:
    preview = _preview(mode)
    response = serializar_preview_acotada(preview, limits)
    dto = PreviewDTO.model_validate_json(response)
    assert dto.geometry.mode == mode.value
    assert dto.view.shape == preview.geometry.work_shape
    assert dto.warnings == preview.warnings
    assert (
        serializar_preview_acotada(preview, replace(limits, max_response_bytes=len(response)))
        == response
    )
    with pytest.raises(ResourceLimitError) as error:
        serializar_preview_acotada(preview, replace(limits, max_response_bytes=len(response) - 1))
    assert error.value.code == ResourceCode.PAYLOAD_LIMIT


@pytest.mark.parametrize("field,value", [("max_array_bytes", 23), ("max_response_bytes", 31)])
def test_preview_rechaza_antes_de_codificar(
    limits: ResourceLimits, field: str, value: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_codificar(_preview: PreviewData, *, max_view_bytes: int) -> None:
        pytest.fail("no debe codificar la vista si el presupuesto es insuficiente")

    monkeypatch.setattr(api_limites, "a_dto_preview", no_codificar)
    with pytest.raises(ResourceLimitError) as error:
        serializar_preview_acotada(_preview(InputMode.THREE_D), replace(limits, **{field: value}))
    assert error.value.code == ResourceCode.PAYLOAD_LIMIT
