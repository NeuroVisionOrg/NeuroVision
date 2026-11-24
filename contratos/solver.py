"""Contrato de configuración para Jacobi, Gauss-Seidel, SOR y SSOR."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

import numpy as np
from numpy.typing import NDArray

_OMEGA_UPPER_BOUND = 2.0


class SolverMethod(StrEnum):
    JACOBI = "jacobi"
    GAUSS_SEIDEL = "gauss_seidel"
    SOR = "sor"
    SSOR = "ssor"


@dataclass(frozen=True, slots=True, eq=False)
class SolverConfig:
    method: SolverMethod
    rtol: float = 1e-6
    atol: float = 1e-10
    max_iterations: int = 2000
    omega: float | None = None
    x0: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.method, SolverMethod):
            raise ValueError("método numérico desconocido")
        self._validar_criterio_parada()
        self._validar_relajacion()
        self._validar_aproximacion_inicial()

    def _validar_criterio_parada(self) -> None:
        if not isfinite(self.rtol) or not isfinite(self.atol):
            raise ValueError("las tolerancias deben ser finitas")
        if self.rtol < 0 or self.atol < 0 or self.rtol == self.atol == 0:
            raise ValueError("las tolerancias deben ser no negativas y alguna positiva")
        if type(self.max_iterations) is not int or self.max_iterations <= 0:
            raise ValueError("max_iterations debe ser entero positivo")

    def _validar_relajacion(self) -> None:
        relaxed = self.method in {SolverMethod.SOR, SolverMethod.SSOR}
        if relaxed:
            if (
                self.omega is None
                or not isfinite(self.omega)
                or not 0 < self.omega < _OMEGA_UPPER_BOUND
            ):
                raise ValueError("SOR y SSOR requieren 0 < omega < 2")
        elif self.omega is not None:
            raise ValueError("Jacobi y Gauss-Seidel no utilizan omega")

    def _validar_aproximacion_inicial(self) -> None:
        if self.x0 is None:
            return
        if self.x0.ndim != 1 or self.x0.dtype != np.dtype("float64"):
            raise ValueError("x0 debe ser un vector float64")
        if not np.all(np.isfinite(self.x0)):
            raise ValueError("x0 debe contener valores finitos")
