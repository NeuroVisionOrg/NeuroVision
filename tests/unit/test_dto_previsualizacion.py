"""Transporte HTTP v2 sobre arreglos y geometria sinteticos, sin lectores medicos."""

import json
import struct
from base64 import b64encode
from dataclasses import replace

import numpy as np
import pytest
from numpy.typing import NDArray
from pydantic import ValidationError

from capa_2_control.api import dto_arreglos
from capa_2_control.api.dto_arreglos import (
    ArrayDTO,
    PayloadLimitError,
    codificar_arreglo,
    decodificar_arreglo,
)
from capa_2_control.api.dto_previsualizacion import PreviewDTO, a_dto_preview
from contratos.datos import PreviewData
from contratos.geometria import InputGeometry, InputMode, SpatialGeometry


def _arreglo_json(**changes: object) -> str:
    payload: dict[str, object] = {
        "dtype": "uint8",
        "shape": [2, 2],
        "order": "C",
        "encoding": "base64",
        "data": "AAECAw==",
    }
    payload.update(changes)
    return json.dumps(payload)


@pytest.mark.parametrize(
    "array",
    [
        np.arange(5, dtype=np.uint8),
        np.arange(12, dtype=np.uint8).reshape(3, 4).T,
        np.arange(24, dtype=np.uint8).reshape(2, 3, 4)[:, :, ::-1],
        np.array([0.25, -1.5, 3.0], dtype=">f4"),
        np.array([[1, 65536, 2**32 - 1]], dtype=">u4"),
    ],
)
def test_arreglo_ida_vuelta_sin_mutar(array: NDArray[np.generic]) -> None:
    original = array.copy()
    dto = codificar_arreglo(array, max_bytes=array.nbytes)
    restaurado = decodificar_arreglo(dto, max_bytes=array.nbytes)
    assert dto.shape == array.shape
    assert dto.nbytes == array.nbytes
    assert not restaurado.flags.writeable
    np.testing.assert_array_equal(restaurado, original)
    np.testing.assert_array_equal(array, original)


def test_bytes_float32_little_endian() -> None:
    array = np.array([[1.25, -2.5]], dtype=">f4")
    dto = codificar_arreglo(array, max_bytes=8)
    assert dto.dtype == "float32_le"
    assert dto.data == b64encode(struct.pack("<ff", 1.25, -2.5)).decode("ascii")


def test_bytes_uint32_little_endian() -> None:
    array = np.array([[1, 256, 65536]], dtype=">u4")
    dto = codificar_arreglo(array, max_bytes=12)
    assert dto.dtype == "uint32_le"
    assert dto.data == b64encode(struct.pack("<III", 1, 256, 65536)).decode("ascii")


def test_bytes_orden_c_no_fortran() -> None:
    array = np.array([[0, 1], [2, 3]], dtype=np.uint8, order="F")
    dto = codificar_arreglo(array, max_bytes=4)
    assert dto.order == "C"
    assert dto.data == "AAECAw=="


@pytest.mark.parametrize(
    "change",
    [
        {"shape": []},
        {"shape": [0, 2]},
        {"shape": [-2, 2]},
        {"shape": [True, 4]},
        {"shape": [2.0, 2]},
        {"shape": ["2", 2]},
        {"shape": [2, 2, 1, 1]},
        {"shape": [2, 4]},
        {"dtype": "float64"},
        {"dtype": "uint32_le"},
        {"order": "F"},
        {"encoding": "hex"},
        {"data": "AAAA"},
        {"data": 12345678},
        {"otro": 1},
    ],
)
def test_rechaza_metadatos_invalidos(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ArrayDTO.model_validate_json(_arreglo_json(**change))


@pytest.mark.parametrize("data", ["AA?CAw==", "AA CAw==", "AAECAwAA", "AAECAw=A", "\u00e9AECAw=="])
def test_rechaza_base64_invalido(data: str) -> None:
    dto = ArrayDTO.model_validate_json(_arreglo_json(data=data))
    with pytest.raises(ValueError, match="Base64"):
        decodificar_arreglo(dto, max_bytes=4)


def test_limite_antes_de_codificar(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_codificar(_data: bytes) -> bytes:
        pytest.fail("no debe codificar despues de superar el limite")

    monkeypatch.setattr(dto_arreglos, "b64encode", no_codificar)
    with pytest.raises(PayloadLimitError):
        codificar_arreglo(np.arange(4, dtype=np.uint8), max_bytes=3)


def test_limite_antes_de_decodificar(monkeypatch: pytest.MonkeyPatch) -> None:
    dto = ArrayDTO.model_validate_json(_arreglo_json())

    def no_decodificar(*_args: object, **_kwargs: object) -> bytes:
        pytest.fail("no debe decodificar despues de superar el limite")

    monkeypatch.setattr(dto_arreglos, "b64decode", no_decodificar)
    with pytest.raises(PayloadLimitError):
        decodificar_arreglo(dto, max_bytes=3)


@pytest.mark.parametrize("limit", [0, -1, True])
def test_limite_invalido(limit: int) -> None:
    with pytest.raises(ValueError, match="limite"):
        codificar_arreglo(np.arange(4, dtype=np.uint8), max_bytes=limit)


@pytest.mark.parametrize(
    "array",
    [
        np.array([1], dtype=np.float64),
        np.array([1], dtype=np.int64),
        np.array([True], dtype=np.bool_),
        np.array([], dtype=np.uint8),
        np.array(1, dtype=np.uint8),
        np.zeros((1, 1, 1, 1), dtype=np.uint8),
        np.array([float("nan")], dtype=np.float32),
        np.array([float("inf")], dtype=np.float32),
    ],
)
def test_no_convierte_precision_ni_acepta_arreglos_invalidos(array: NDArray[np.generic]) -> None:
    with pytest.raises(ValueError):
        codificar_arreglo(array, max_bytes=32)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_rechaza_float_no_finito_al_decodificar(value: float) -> None:
    data = b64encode(struct.pack("<f", value)).decode("ascii")
    dto = ArrayDTO.model_validate_json(_arreglo_json(dtype="float32_le", shape=[1], data=data))
    with pytest.raises(ValueError, match="no finito"):
        decodificar_arreglo(dto, max_bytes=4)


def _preview_2d() -> PreviewData:
    geometry = InputGeometry(InputMode.TWO_D, (2, 3), (2, 3), "PNG")
    return PreviewData(
        geometry, np.arange(6, dtype=np.uint8).reshape(2, 3), 1.0, 9.0, "0" * 64, "1"
    )


def _preview_3d() -> PreviewData:
    transform = np.array([[0, -1, 0, 2], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.int64)
    h_original = np.array(
        [[0, 2, 0, 5], [-2, 0, 0, -3], [0, 0, 2, 11], [0, 0, 0, 1]], dtype=np.float64
    )
    h_work = np.array([[2, 0, 0, 5], [0, 2, 0, -7], [0, 0, 2, 11], [0, 0, 0, 1]], dtype=np.float64)
    spatial = SpatialGeometry(
        h_original, h_work, transform, (2.0, 2.0, 2.0), ("R", "A", "S"), "sform", 0.0
    )
    geometry = InputGeometry(InputMode.THREE_D, (3, 2, 4), (2, 3, 4), "NIFTI", spatial)
    return PreviewData(
        geometry, np.arange(24, dtype=np.uint8).reshape(2, 3, 4), -3.0, 15.0, "0" * 64, "1"
    )


def test_preview_2d_json_sin_geometria_fisica() -> None:
    preview = _preview_2d()
    dto = a_dto_preview(preview, max_view_bytes=6)
    result = json.loads(dto.model_dump_json(by_alias=True))
    assert result["contract_version"] == "2"
    assert result["geometry"] == {
        "mode": "2d",
        "original_shape": [2, 3],
        "work_shape": [2, 3],
        "source_format": "PNG",
    }
    assert result["view"]["data"] == "AAECAwQF"
    assert result["input_id"] == preview.input_id
    assert result["preparation_version"] == preview.preparation_version
    assert result["display_min"] == 1.0
    assert result["display_max"] == 9.0


def test_preview_3d_preserva_geometria_y_vista() -> None:
    preview = _preview_3d()
    dto = a_dto_preview(preview, max_view_bytes=24)
    raw = dto.model_dump_json(by_alias=True)
    result = json.loads(raw)
    geometry = result["geometry"]
    spatial = preview.geometry.spatial
    assert spatial is not None
    assert geometry["mode"] == "3d"
    assert geometry["original_shape"] == [3, 2, 4]
    assert geometry["work_shape"] == [2, 3, 4]
    assert geometry["units"] == "mm"
    assert geometry["axis_codes"] == ["R", "A", "S"]
    assert geometry["spacing_mm"] == [2.0, 2.0, 2.0]
    assert geometry["affine_source"] == "sform"
    np.testing.assert_array_equal(geometry["H_original"], spatial.h_original)
    np.testing.assert_array_equal(geometry["H_work"], spatial.h_work)
    np.testing.assert_array_equal(geometry["T_work_to_original"], spatial.t_work_to_original)
    assert "h_original" not in geometry
    assert "atol_mm" not in geometry
    restaurado = PreviewDTO.model_validate_json(raw)
    assert restaurado.model_dump_json(by_alias=True) == raw
    view = decodificar_arreglo(restaurado.view, max_bytes=24)
    np.testing.assert_array_equal(view, preview.uint8_view)
    np.testing.assert_array_equal(view[:, :, 1].T, preview.uint8_view[:, :, 1].T)


def test_preview_conserva_advertencia_constante() -> None:
    preview = replace(
        _preview_2d(),
        uint8_view=np.zeros((2, 3), dtype=np.uint8),
        display_min=5.0,
        display_max=5.0,
        warnings=("CONSTANT_INTENSITY",),
    )
    dto = a_dto_preview(preview, max_view_bytes=6)
    assert dto.warnings == ("CONSTANT_INTENSITY",)
    assert dto.view.data == "AAAAAAAA"


def test_preview_respeta_limite_de_vista() -> None:
    with pytest.raises(PayloadLimitError):
        a_dto_preview(_preview_3d(), max_view_bytes=23)


@pytest.mark.parametrize("shape", [[3, 2], [1, 2, 3]])
def test_preview_rechaza_forma_incoherente(shape: list[int]) -> None:
    dto = a_dto_preview(_preview_2d(), max_view_bytes=6)
    payload = json.loads(dto.model_dump_json())
    payload["view"]["shape"] = shape
    with pytest.raises(ValidationError, match="vista uint8"):
        PreviewDTO.model_validate_json(json.dumps(payload))


def test_preview_rechaza_rango_invertido() -> None:
    dto = a_dto_preview(_preview_2d(), max_view_bytes=6)
    payload = json.loads(dto.model_dump_json())
    payload["display_min"] = 10
    with pytest.raises(ValidationError, match="rango"):
        PreviewDTO.model_validate_json(json.dumps(payload))


def test_mismo_largo_codificado_no_implica_mismos_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    dto = ArrayDTO.model_validate_json(_arreglo_json(shape=[2, 3]))

    def no_decodificar(*_args: object, **_kwargs: object) -> bytes:
        pytest.fail("el relleno incompatible debe rechazarse antes de decodificar")

    monkeypatch.setattr(dto_arreglos, "b64decode", no_decodificar)
    with pytest.raises(ValueError, match="relleno"):
        decodificar_arreglo(dto, max_bytes=6)


def test_preview_rechaza_dtype_distinto_de_uint8() -> None:
    dto = a_dto_preview(_preview_2d(), max_view_bytes=6)
    payload = json.loads(dto.model_dump_json())
    payload["view"] = codificar_arreglo(np.ones((2, 3), dtype=np.float32), max_bytes=24).model_dump(
        mode="json"
    )
    with pytest.raises(ValidationError, match="vista uint8"):
        PreviewDTO.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_preview_rechaza_rango_no_finito(value: float) -> None:
    dto = a_dto_preview(_preview_2d(), max_view_bytes=6)
    payload = json.loads(dto.model_dump_json())
    payload["display_min"] = value
    with pytest.raises(ValidationError):
        PreviewDTO.model_validate_json(json.dumps(payload))
