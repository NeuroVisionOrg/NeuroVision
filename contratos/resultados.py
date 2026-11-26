"""Contratos de diagnóstico numérico independientes de las imágenes."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from contratos.sistema import LinearSystem
from contratos.solver import SolverConfig, SolverMethod, validar_umbral_parada


class SolverStatus(StrEnum):
    CONVERGED = "CONVERGED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"


@dataclass(frozen=True, slots=True, eq=False)
class SolverResult:
    """Diagnóstico de una ejecución aceptada, incluso cuando no converge.

    Los barridos registrados son únicamente los que terminaron con residuo
    finito. Una ejecución fallida no publica un vector como solución válida.
    """

    method: SolverMethod
    status: SolverStatus
    solution: NDArray[np.float64] | None
    iterations: int
    sweeps: int
    initial_residual: float | None
    final_residual: float | None
    residual_history: tuple[float, ...]
    elapsed_seconds: float
    omega_used: float
    rtol: float
    atol: float
    max_iterations: int
    stopping_threshold: float
    initialization: str
    failure_code: str | None = None
    failed_at_sweep: int | None = None

    def __post_init__(self) -> None:
        self._validar_configuracion()
        self._validar_recuento()
        self._validar_residuos()
        self._validar_estado()
        self._validar_solucion()

    def _validar_configuracion(self) -> None:
        SolverConfig(
            method=self.method,
            omega=self.omega_used,
            rtol=self.rtol,
            atol=self.atol,
            max_iterations=self.max_iterations,
        )
        validar_umbral_parada(self.stopping_threshold)
        if self.initialization not in {"zero", "provided"}:
            raise ValueError("initialization debe ser zero o provided")
        if not isinstance(self.status, SolverStatus):
            raise ValueError("estado numérico desconocido")
        if not isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0:
            raise ValueError("el tiempo debe ser finito y no negativo")

    def _validar_recuento(self) -> None:
        if any(type(v) is not int or v < 0 for v in (self.iterations, self.sweeps)):
            raise ValueError("las iteraciones y barridos deben ser enteros no negativos")
        if self.iterations != self.sweeps:
            raise ValueError("SOR requiere un barrido evaluado por iteración registrada")
        if self.iterations > self.max_iterations:
            raise ValueError("las iteraciones exceden el máximo configurado")

    def _validar_residuos(self) -> None:
        if not self.residual_history:
            self._validar_historial_vacio()
            return
        if len(self.residual_history) != self.iterations + 1:
            raise ValueError("el historial debe incluir el residuo inicial y cada iteración")
        if any(not isfinite(r) or r < 0 for r in self.residual_history):
            raise ValueError("el historial de residuos debe ser finito y no negativo")
        if self.initial_residual != self.residual_history[0]:
            raise ValueError("el residuo inicial no coincide con el historial")
        if self.final_residual != self.residual_history[-1]:
            raise ValueError("el residuo final no coincide con el historial")

    def _validar_historial_vacio(self) -> None:
        if (
            self.status != SolverStatus.NUMERICAL_FAILURE
            or self.iterations != 0
            or self.initial_residual is not None
            or self.final_residual is not None
            or self.failed_at_sweep is not None
        ):
            raise ValueError("historial vacío solo si falla la evaluación del residuo inicial")

    def _validar_estado(self) -> None:
        if self.status == SolverStatus.NUMERICAL_FAILURE:
            self._validar_fallo()
            return
        if self.failure_code is not None or self.failed_at_sweep is not None:
            raise ValueError("solo un fallo numérico admite detalles de fallo")
        if self.final_residual is None:
            raise ValueError("se requiere un residuo final evaluado")
        if self.status == SolverStatus.CONVERGED:
            if self.final_residual > self.stopping_threshold:
                raise ValueError("el residuo final supera el umbral de convergencia")
        elif (
            self.iterations != self.max_iterations or self.final_residual <= self.stopping_threshold
        ):
            raise ValueError("MAX_ITERATIONS requiere agotar el máximo sin converger")

    def _validar_fallo(self) -> None:
        if not self.failure_code or not self.failure_code.strip():
            raise ValueError("NUMERICAL_FAILURE requiere failure_code")
        if not self.residual_history:
            return
        if (
            type(self.failed_at_sweep) is not int
            or self.failed_at_sweep != self.iterations + 1
            or self.failed_at_sweep > self.max_iterations
        ):
            raise ValueError("failed_at_sweep debe identificar el siguiente barrido fallido")
        if self.residual_history[-1] <= self.stopping_threshold:
            raise ValueError("no se debe iniciar otro barrido tras converger")

    def _validar_solucion(self) -> None:
        if self.status != SolverStatus.CONVERGED:
            if self.solution is not None:
                raise ValueError("una ejecución no convergente no publica solution")
            return
        if self.solution is None:
            raise ValueError("una ejecución convergente debe conservar su solución")
        if (
            self.solution.ndim != 1
            or self.solution.size == 0
            or self.solution.dtype != np.dtype("float64")
            or not np.all(np.isfinite(self.solution))
        ):
            raise ValueError("solution debe ser un vector float64 finito no vacío")

    def validar_para_sistema(self, sistema: LinearSystem) -> None:
        """Comprueba la longitud de la solución cuando se dispone del sistema."""
        if self.solution is not None and self.solution.shape != (sistema.n,):
            raise ValueError("solution debe tener una entrada por incógnita")

    @property
    def converged(self) -> bool:
        return self.status == SolverStatus.CONVERGED
