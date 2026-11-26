"""Datos de entrada y referencia: validaciones, no lectura real."""

from dataclasses import replace

import numpy as np
import pytest

from contratos.datos import AlignedReference, DecodedData, PreviewData, ReferencePolicy
from contratos.geometria import InputGeometry, InputMode
from contratos.imagen import ROISelection


def geometria() -> InputGeometry:
    return InputGeometry(InputMode.TWO_D, (3, 4), (3, 4), "PNG")


def decodificado() -> DecodedData:
    return DecodedData(geometria(), np.arange(12, dtype=np.uint16).reshape(3, 4), "a" * 64)


def vista() -> PreviewData:
    return PreviewData(geometria(), np.zeros((3, 4), dtype=np.uint8), 5, 5, "a" * 64, "v1")


def referencia() -> AlignedReference:
    return AlignedReference(
        geometry=geometria(),
        roi=ROISelection(1, 1, 3, 3),
        mask=np.zeros((2, 2), dtype=np.bool_),
        reference_id="synthetic-reference",
        reference_policy=ReferencePolicy.BRISC_BIN_128,
    )


def test_decodificado_conserva_intensidades_originales() -> None:
    data = decodificado()
    assert data.intensities.dtype == np.dtype("uint16")
    assert data.intensities.max() == 11


@pytest.mark.parametrize(
    "intensities",
    [np.zeros((3, 4, 3)), np.zeros((3, 4), dtype=np.complex128), np.full((3, 4), np.nan)],
)
def test_decodificado_rechaza_arreglos_invalidos(intensities: np.ndarray) -> None:
    with pytest.raises(ValueError):
        replace(decodificado(), intensities=intensities)


def test_decodificado_exige_digest() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        replace(decodificado(), source_digest="unknown")


@pytest.mark.parametrize(
    "changes",
    [
        {"uint8_view": np.zeros((3, 4), dtype=np.float32)},
        {"uint8_view": np.ones((3, 4), dtype=np.uint8)},
        {"display_min": 8},
        {"display_max": float("inf")},
        {"input_id": ""},
        {"preparation_version": ""},
    ],
)
def test_previsualizacion_invalida(changes: dict) -> None:
    with pytest.raises(ValueError):
        replace(vista(), **changes)


def test_referencia_acotada_a_roi() -> None:
    assert referencia().mask.shape == (2, 2)


@pytest.mark.parametrize(
    "changes",
    [
        {"mask": np.zeros((3, 4), dtype=np.bool_)},
        {"mask": np.zeros((2, 2), dtype=np.uint8)},
        {"reference_id": ""},
        {"reference_policy": ReferencePolicy.ITKSNAP_LABEL_2},
    ],
)
def test_referencia_invalida(changes: dict) -> None:
    with pytest.raises(ValueError):
        replace(referencia(), **changes)
