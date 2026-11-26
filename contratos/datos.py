"""Datos de entrada, previsualización y referencia; sin lectura ni remuestreo."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from re import fullmatch

import numpy as np
from numpy.typing import NDArray

from contratos.geometria import InputGeometry, InputMode
from contratos.reconstruccion import ROI, forma_roi


def _validar_digest(value: str) -> None:
    if fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("se requiere SHA-256 hexadecimal minúsculo")


@dataclass(frozen=True, slots=True, eq=False)
class DecodedData:
    """Intensidades originales en cuadrícula de trabajo, no normalizadas."""

    geometry: InputGeometry
    intensities: NDArray[np.generic]
    source_digest: str

    def __post_init__(self) -> None:
        if self.intensities.shape != self.geometry.work_shape:
            raise ValueError("forma de intensidades incompatible con la geometría")
        if self.intensities.dtype.kind not in {"i", "u", "f"}:
            raise ValueError("se requieren intensidades escalares numéricas reales")
        if not np.all(np.isfinite(self.intensities)):
            raise ValueError("intensidades no finitas")
        _validar_digest(self.source_digest)


@dataclass(frozen=True, slots=True, eq=False)
class PreviewData:
    """Vista uint8 de todo el dominio; nunca una entrada al cálculo de SOR."""

    geometry: InputGeometry
    uint8_view: NDArray[np.uint8]
    display_min: float
    display_max: float
    input_id: str
    preparation_version: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.uint8_view.shape != self.geometry.work_shape or self.uint8_view.dtype != np.dtype(
            "uint8"
        ):
            raise ValueError("vista debe ser uint8 y conservar la forma de trabajo")
        if not isfinite(self.display_min) or not isfinite(self.display_max):
            raise ValueError("rango de visualización no finito")
        if self.display_min > self.display_max:
            raise ValueError("rango de visualización invertido")
        if self.display_min == self.display_max and np.any(self.uint8_view != 0):
            raise ValueError("vista de intensidad constante debe ser cero")
        _validar_digest(self.input_id)
        if not self.preparation_version.strip():
            raise ValueError("falta versión de preparación")


class ReferencePolicy(StrEnum):
    BRISC_BIN_128 = "BRISC_BIN_128"
    ITKSNAP_LABEL_2 = "ITKSNAP_LABEL_2"


def validar_politica_referencia(mode: InputMode, policy: ReferencePolicy) -> None:
    if not isinstance(mode, InputMode) or not isinstance(policy, ReferencePolicy):
        raise ValueError("modo o política de referencia inválidos")
    if (mode == InputMode.TWO_D) != (policy == ReferencePolicy.BRISC_BIN_128):
        raise ValueError("política de referencia incompatible con el modo")


@dataclass(frozen=True, slots=True, eq=False)
class AlignedReference:
    """Referencia ya alineada y recortada por Traducción, solo para evaluación.

    La validación estructural no prueba emparejamiento, procedencia, licencia
    ni alineación anatómica. Traducción y Control deben verificarlos antes.
    """

    geometry: InputGeometry
    roi: ROI
    mask: NDArray[np.bool_]
    reference_id: str
    reference_policy: ReferencePolicy

    def __post_init__(self) -> None:
        shape = forma_roi(self.geometry, self.roi)
        if self.mask.shape != shape or self.mask.dtype != np.dtype("bool"):
            raise ValueError("referencia debe ser booleana y coincidir con ROI")
        if not self.reference_id.strip():
            raise ValueError("se requiere identidad de referencia")
        validar_politica_referencia(self.geometry.mode, self.reference_policy)
