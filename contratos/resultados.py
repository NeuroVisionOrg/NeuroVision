"""Estructuras de salida; los algoritmos y las exportaciones aún no existen."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from contratos.solver import SolverMethod


class SolverStatus(str, Enum):
    CONVERGED = "CONVERGED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"


@dataclass(frozen=True, slots=True, eq=False)
class SolverResult:
    method: SolverMethod
    status: SolverStatus
    solution: NDArray[np.float64] | None
    iterations: int
    sweeps: int
    initial_residual: float
    final_residual: float
    residual_history: tuple[float, ...]
    elapsed_seconds: float
    omega_used: float | None = None

    def __post_init__(self) -> None:
        self._validar_recuento()
        self._validar_residuos()
        self._validar_solucion()

    def _validar_recuento(self) -> None:
        if self.iterations < 0 or self.sweeps < 0:
            raise ValueError("las iteraciones y barridos no pueden ser negativos")
        if self.method == SolverMethod.SSOR and self.sweeps != 2 * self.iterations:
            raise ValueError("SSOR requiere dos barridos por iteración completa")

    def _validar_residuos(self) -> None:
        if not self.residual_history:
            raise ValueError("se necesita al menos el residuo inicial")
        if len(self.residual_history) != self.iterations + 1:
            raise ValueError("el historial debe incluir el residuo inicial y cada iteración")
        if any(not isfinite(r) or r < 0 for r in self.residual_history):
            raise ValueError("el historial de residuos debe ser válido")
        if not all(isfinite(v) and v >= 0 for v in (
            self.initial_residual, self.final_residual, self.elapsed_seconds
        )):
            raise ValueError("residuos y tiempo deben ser finitos y no negativos")
        if self.initial_residual != self.residual_history[0]:
            raise ValueError("el residuo inicial no coincide con el historial")
        if self.final_residual != self.residual_history[-1]:
            raise ValueError("el residuo final no coincide con el historial")

    def _validar_solucion(self) -> None:
        if self.solution is not None:
            if self.solution.ndim != 1 or self.solution.dtype != np.dtype("float64"):
                raise ValueError("solution debe ser un vector float64")
        if self.status == SolverStatus.CONVERGED and self.solution is None:
            raise ValueError("una ejecución convergente debe conservar su solución")

    @property
    def converged(self) -> bool:
        return self.status == SolverStatus.CONVERGED


@dataclass(frozen=True, slots=True)
class MetricsResult:
    foreground_pixels: int
    dice: float | None = None
    iou: float | None = None
    reference_pixels: int | None = None
    true_positives: int | None = None
    false_positives: int | None = None
    false_negatives: int | None = None


@dataclass(frozen=True, slots=True, eq=False)
class SegmentationResult:
    solver_result: SolverResult
    probability_map: NDArray[np.float64] | None = None
    mask: NDArray[np.bool_] | None = None
    boundary_mask: NDArray[np.bool_] | None = None
    threshold: float = 0.5
    metrics: MetricsResult | None = None


@dataclass(frozen=True, slots=True)
class ExportResult:
    filename: str
    media_type: str
    content: bytes
