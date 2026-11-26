"""Resultados válidos de reconstrucción, sin implementar el algoritmo."""

from dataclasses import dataclass
from math import isfinite
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from contratos.geometria import InputGeometry, InputMode
from contratos.imagen import ROISelection
from contratos.reconstruccion import ROI, ReconstructionContext, forma_roi
from contratos.resultados import SolverResult
from contratos.volumen import ROI3DSelection


class _Resultado(Protocol):
    @property
    def geometry(self) -> InputGeometry: ...
    @property
    def roi(self) -> ROI: ...
    @property
    def threshold(self) -> float: ...
    @property
    def probability_map(self) -> NDArray[np.float64]: ...
    @property
    def mask(self) -> NDArray[np.bool_]: ...
    @property
    def solver_result(self) -> SolverResult: ...
    @property
    def touches_boundary(self) -> bool: ...


def _toca_frontera(mask: NDArray[np.bool_]) -> bool:
    return any(np.any(np.take(mask, [0, -1], axis=axis)) for axis in range(mask.ndim))


def _validar_resultado(result: _Resultado) -> None:
    shape = forma_roi(result.geometry, result.roi)
    if not result.solver_result.converged or result.solver_result.solution is None:
        raise ValueError("se requiere un solver CONVERGED con solución")
    if not isfinite(result.threshold) or not 0 < result.threshold < 1:
        raise ValueError("threshold inválido")
    p = result.probability_map
    if p.shape != shape or p.dtype != np.dtype("float64"):
        raise ValueError("forma o dtype de probabilidades incompatible con ROI")
    if not np.all(np.isfinite(p)) or np.any(p < 0) or np.any(p > 1):
        raise ValueError("probabilidades deben ser finitas y estar en [0, 1]")
    if result.mask.shape != shape or result.mask.dtype != np.dtype("bool"):
        raise ValueError("máscara debe ser booleana y coincidir con ROI")
    if not np.array_equal(result.mask, p >= result.threshold):
        raise ValueError("máscara incoherente con las probabilidades y el umbral")
    if type(result.touches_boundary) is not bool or result.touches_boundary != _toca_frontera(
        result.mask
    ):
        raise ValueError("indicador de contacto con frontera incoherente")


@dataclass(frozen=True, slots=True, eq=False)
class SegmentationResult:
    """Resultados 2D en ROI local; exterior no evaluado, sin fondo inventado."""

    geometry: InputGeometry
    roi: ROISelection
    threshold: float
    probability_map: NDArray[np.float64]
    mask: NDArray[np.bool_]
    boundary_mask: NDArray[np.bool_]
    solver_result: SolverResult
    touches_boundary: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.geometry.mode != InputMode.TWO_D:
            raise ValueError("SegmentationResult exige modo 2D")
        _validar_resultado(self)
        if self.boundary_mask.shape != self.mask.shape or self.boundary_mask.dtype != np.dtype(
            "bool"
        ):
            raise ValueError("contorno incompatible con máscara")
        if np.any(self.boundary_mask & ~self.mask):
            raise ValueError("el contorno debe pertenecer al primer plano")


@dataclass(frozen=True, slots=True, eq=False)
class VolumeSegmentationResult:
    """Resultados 3D en ROI local, con la geometría completa de trabajo."""

    geometry: InputGeometry
    roi: ROI3DSelection
    threshold: float
    probability_map: NDArray[np.float64]
    mask: NDArray[np.bool_]
    solver_result: SolverResult
    touches_boundary: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.geometry.mode != InputMode.THREE_D:
            raise ValueError("VolumeSegmentationResult exige modo 3D")
        _validar_resultado(self)


def validar_reconstruccion(
    context: ReconstructionContext,
    result: SegmentationResult | VolumeSegmentationResult,
    probability_atol: float,
) -> None:
    """Comprueba correspondencia y semillas; no modifica la solución ni la máscara.

    La tolerancia de redondeo es explícita y debe validarse experimentalmente.
    Control/Traducción deben invocar esta comprobación antes de publicar resultados.
    """
    if isinstance(probability_atol, bool) or not isfinite(probability_atol):
        raise ValueError("tolerancia de probabilidad inválida")
    if not 0 <= probability_atol < min(result.threshold, 1 - result.threshold):
        raise ValueError("tolerancia de probabilidad inválida")
    if result.geometry is not context.geometry or result.roi != context.roi:
        raise ValueError("el resultado no corresponde al contexto de reconstrucción")
    if result.threshold != context.model_config.threshold:
        raise ValueError("umbral distinto del modelo ejecutado")
    solution = result.solver_result.solution
    if solution is None or solution.shape != context.unknown_flat_indices.shape:
        raise ValueError("solution debe tener una entrada por incógnita")
    flat = result.probability_map.ravel(order="C")
    if not np.array_equal(flat[context.seed_flat_indices], context.seed_values):
        raise ValueError("la reconstrucción debe conservar exactamente las semillas")
    if not np.allclose(flat[context.unknown_flat_indices], solution, atol=probability_atol, rtol=0):
        raise ValueError("probabilidades no corresponden a las filas del sistema")
