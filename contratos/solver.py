"""Configuración interna del único método numérico de NeuroVision: SOR."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

import numpy as np
from numpy.typing import NDArray

from contratos.sistema import LinearSystem

_OMEGA_UPPER_BOUND = 2.0


class SolverMethod(StrEnum):
    """Identificador del método, conservado para trazabilidad."""

    SOR = "sor"


class InvalidSolverConfigError(ValueError):
    """Configuración inválida antes de iniciar la resolución."""


@dataclass(frozen=True, slots=True, eq=False)
class SolverConfig:
    method: SolverMethod
    omega: float
    rtol: float = 1e-6
    atol: float = 1e-10
    max_iterations: int = 2000
    x0: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.method, SolverMethod):
            raise InvalidSolverConfigError("solo se admite SOR")
        self._validar_criterio_parada()
        self._validar_relajacion()
        self._validar_aproximacion_inicial()

    def _validar_criterio_parada(self) -> None:
        if any(not _numero_finito(v) for v in (self.rtol, self.atol)):
            raise InvalidSolverConfigError("las tolerancias deben ser finitas y numéricas")
        if self.rtol < 0 or self.atol < 0 or self.rtol == self.atol == 0:
            raise InvalidSolverConfigError(
                "las tolerancias deben ser no negativas y alguna positiva"
            )
        if type(self.max_iterations) is not int or self.max_iterations <= 0:
            raise InvalidSolverConfigError("max_iterations debe ser entero positivo")

    def _validar_relajacion(self) -> None:
        if not _numero_finito(self.omega) or not 0 < self.omega < _OMEGA_UPPER_BOUND:
            raise InvalidSolverConfigError("SOR requiere 0 < omega < 2")

    def _validar_aproximacion_inicial(self) -> None:
        if self.x0 is None:
            return
        if self.x0.ndim != 1 or self.x0.dtype != np.dtype("float64"):
            raise InvalidSolverConfigError("x0 debe ser un vector float64")
        if not np.all(np.isfinite(self.x0)):
            raise InvalidSolverConfigError("x0 debe contener valores finitos")

    def validar_para_sistema(self, sistema: LinearSystem, stopping_threshold: float) -> None:
        """Valida la dimensión y el umbral efectivo calculado por Métodos.

        Métodos calcula max(atol, rtol*||b||_2) una sola vez antes de iterar.
        Este contrato no implementa el cálculo del residuo ni el solver.
        """
        if self.x0 is not None and self.x0.shape != (sistema.n,):
            raise InvalidSolverConfigError("x0 debe tener una entrada por incógnita")
        validar_umbral_parada(stopping_threshold)


def validar_umbral_parada(stopping_threshold: float) -> None:
    """Un sistema aceptado requiere un umbral efectivo finito y positivo."""
    if not _numero_finito(stopping_threshold) or stopping_threshold <= 0:
        raise InvalidSolverConfigError("el umbral efectivo de parada debe ser finito y positivo")


def _numero_finito(valor: object) -> bool:
    """Rechaza booleanos y valores no numéricos en los parámetros escalares."""
    if not isinstance(valor, (float, int)) or isinstance(valor, bool):
        return False
    try:
        return isfinite(valor)
    except OverflowError:
        return False
