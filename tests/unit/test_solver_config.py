"""Pruebas de parámetros y estados de ejecución."""

import numpy as np
import pytest

from contratos.resultados import SolverResult, SolverStatus
from contratos.solver import SolverConfig, SolverMethod


def test_jacobi_tiene_tolerancias_iniciales() -> None:
    config = SolverConfig(method=SolverMethod.JACOBI)
    assert config.rtol == 1e-6
    assert config.max_iterations == 2000


def test_sor_requiere_omega_valido() -> None:
    with pytest.raises(ValueError, match="omega"):
        SolverConfig(method=SolverMethod.SOR, omega=2.0)


def test_ssor_informa_dos_barridos_por_iteracion() -> None:
    resultado = SolverResult(
        method=SolverMethod.SSOR,
        status=SolverStatus.CONVERGED,
        solution=np.array([1 / 3, 2 / 3], dtype=np.float64),
        iterations=2,
        sweeps=4,
        initial_residual=1.0,
        final_residual=1e-7,
        residual_history=(1.0, 1e-3, 1e-7),
        elapsed_seconds=0.02,
        omega_used=1.2,
    )
    assert resultado.converged
    assert resultado.sweeps == 4


def test_ssor_rechaza_barridos_incoherentes() -> None:
    with pytest.raises(ValueError, match="dos barridos"):
        SolverResult(
            method=SolverMethod.SSOR,
            status=SolverStatus.MAX_ITERATIONS,
            solution=None,
            iterations=2,
            sweeps=2,
            initial_residual=1.0,
            final_residual=0.1,
            residual_history=(1.0, 0.5, 0.1),
            elapsed_seconds=0.02,
            omega_used=1.2,
        )
