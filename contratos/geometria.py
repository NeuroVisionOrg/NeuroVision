"""Geometría del dominio de trabajo, independiente de los lectores de archivos."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

import numpy as np
from numpy.typing import NDArray

_SPATIAL_DIMENSIONS = 3
_AFFINE_DIMENSIONS = 4


class InputMode(StrEnum):
    """Dimensión espacial de los datos, no cantidad de canales."""

    TWO_D = "2d"
    THREE_D = "3d"


def validar_forma(shape: tuple[int, ...], dimensions: int) -> None:
    """Exige dimensiones positivas e índices enteros no booleanos."""
    if len(shape) != dimensions or any(type(v) is not int or v <= 0 for v in shape):
        raise ValueError("forma incompatible con la dimensión del dominio")


def _validar_afin(affine: NDArray[np.float64]) -> None:
    if affine.shape != (_AFFINE_DIMENSIONS, _AFFINE_DIMENSIONS):
        raise ValueError("la afín debe tener forma 4x4")
    if affine.dtype != np.dtype("float64") or not np.all(np.isfinite(affine)):
        raise ValueError("la afín debe ser float64 finita")
    if not np.array_equal(affine[-1], [0, 0, 0, 1]):
        raise ValueError("última fila de la afín inválida")
    sign, logdet = np.linalg.slogdet(affine[:3, :3])
    if sign == 0 or not np.isfinite(logdet):
        raise ValueError("la afín debe ser no singular")


@dataclass(frozen=True, slots=True, eq=False)
class SpatialGeometry:
    """Metadatos 3D en mm; el lector debe comprobar su procedencia.

    La tolerancia absoluta es explícita, no una política clínica ni un valor
    definitivo de admisión. Las afines representan índices de vóxel, no bordes.
    Los arreglos geométricos se copian para no conservar alias con el lector.
    """

    h_original: NDArray[np.float64]
    h_work: NDArray[np.float64]
    t_work_to_original: NDArray[np.int64]
    spacing_mm: tuple[float, float, float]
    axis_codes: tuple[str, str, str]
    affine_source: str
    atol_mm: float

    def __post_init__(self) -> None:
        _validar_afin(self.h_original)
        _validar_afin(self.h_work)
        self._validar_transformacion()
        self._validar_espaciado()
        self._validar_consistencia()
        for name in ("h_original", "h_work", "t_work_to_original"):
            array = getattr(self, name).copy()
            array.setflags(write=False)
            object.__setattr__(self, name, array)

    def _validar_transformacion(self) -> None:
        transform = self.t_work_to_original
        if transform.shape != (_AFFINE_DIMENSIONS, _AFFINE_DIMENSIONS):
            raise ValueError("la transformación de índices debe tener forma 4x4")
        if transform.dtype != np.dtype("int64"):
            raise ValueError("la transformación de índices debe ser int64")
        if not np.array_equal(transform[-1], [0, 0, 0, 1]):
            raise ValueError("última fila de la transformación inválida")
        block = transform[:3, :3]
        if np.any((block < -1) | (block > 1)):
            raise ValueError("se exige una permutación con posibles inversiones")
        if not (
            np.all(np.count_nonzero(block, axis=0) == 1)
            and np.all(np.count_nonzero(block, axis=1) == 1)
        ):
            raise ValueError("se exige una permutación con posibles inversiones")

    def _validar_espaciado(self) -> None:
        if len(self.spacing_mm) != _SPATIAL_DIMENSIONS or any(
            not isfinite(v) or v <= 0 for v in self.spacing_mm
        ):
            raise ValueError("espaciamiento positivo y finito en mm requerido")
        if not isfinite(self.atol_mm) or not 0 <= self.atol_mm < min(self.spacing_mm):
            raise ValueError("tolerancia geométrica inválida")
        if not np.allclose(self.spacing_mm, self.spacing_mm[0], rtol=0, atol=self.atol_mm):
            raise ValueError("el piloto requiere espaciamiento isotrópico")
        if self.axis_codes != ("R", "A", "S") or np.any(np.diag(self.h_work[:3, :3]) <= 0):
            raise ValueError("el dominio de trabajo debe estar orientado a RAS+")
        if not np.allclose(
            self.h_work[:3, :3], np.diag(self.spacing_mm), rtol=0, atol=self.atol_mm
        ):
            raise ValueError("afín de trabajo incompatible con los ejes y el espaciamiento")
        if not self.affine_source.strip():
            raise ValueError("se requiere la procedencia de la afín")

    def _validar_consistencia(self) -> None:
        expected = self.h_original @ self.t_work_to_original
        if not np.allclose(self.h_work, expected, rtol=0, atol=self.atol_mm):
            raise ValueError("h_work no coincide con h_original y la transformación")

    def validar_formas(self, original_shape: tuple[int, ...], work_shape: tuple[int, ...]) -> None:
        """Comprueba la correspondencia exacta de las cuadrículas completas."""
        validar_forma(original_shape, _SPATIAL_DIMENSIONS)
        validar_forma(work_shape, _SPATIAL_DIMENSIONS)
        transform = self.t_work_to_original
        for axis in range(_SPATIAL_DIMENSIONS):
            source_axis = int(np.argmax(np.abs(transform[axis, :3])))
            sign = int(transform[axis, source_axis])
            offset = original_shape[axis] - 1 if sign < 0 else 0
            if work_shape[source_axis] != original_shape[axis] or transform[axis, 3] != offset:
                raise ValueError("transformación incompatible con las formas completas")


@dataclass(frozen=True, slots=True, eq=False)
class InputGeometry:
    """Identidad geométrica del dominio completo, antes de seleccionar una ROI.

    En 2D no se inventan medidas físicas. En 3D, `spatial` agrupa los campos
    de afines, transformación, espaciamiento y orientación del contrato C-02.
    """

    mode: InputMode
    original_shape: tuple[int, ...]
    work_shape: tuple[int, ...]
    source_format: str
    spatial: SpatialGeometry | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, InputMode):
            raise ValueError("modo de entrada inválido")
        if not self.source_format.strip():
            raise ValueError("se requiere el formato original")
        dimensions = 2 if self.mode == InputMode.TWO_D else _SPATIAL_DIMENSIONS
        validar_forma(self.original_shape, dimensions)
        validar_forma(self.work_shape, dimensions)
        if self.mode == InputMode.TWO_D:
            if self.spatial is not None or self.original_shape != self.work_shape:
                raise ValueError("la geometría 2D no admite afín física ni reescalado")
        elif self.spatial is None:
            raise ValueError("la geometría 3D requiere metadatos espaciales")
        else:
            self.spatial.validar_formas(self.original_shape, self.work_shape)
