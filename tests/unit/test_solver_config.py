"""Pruebas de contrato de SOR; no implementan el algoritmo numérico."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.sparse import csr_array

from contratos.resultados import SolverResult, SolverStatus
from contratos.sistema import LinearSystem
from contratos.solver import InvalidSolverConfigError, SolverConfig, SolverMethod


def test_sor_es_el_unico_metodo_y_conserva_tolerancias_provisionales() -> None:
    config = SolverConfig(method=SolverMethod.SOR, omega=1.2)
    assert tuple(SolverMethod) == (SolverMethod.SOR,)
    assert config.rtol == 1e-6
    assert config.atol == 1e-10
    assert config.max_iterations == 2000
    assert config.x0 is None


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel", "ssor"])
def test_rechaza_metodos_retirados(method: str) -> None:
    with pytest.raises(ValueError):
        SolverMethod(method)


@pytest.mark.parametrize("omega", [0.0, 2.0, -0.1, float("nan"), float("inf"), True, None])
def test_sor_requiere_omega_valido(omega: float) -> None:
    with pytest.raises(InvalidSolverConfigError, match="omega"):
        SolverConfig(method=SolverMethod.SOR, omega=omega)


def test_omega_uno_es_configuracion_de_sor() -> None:
    assert SolverConfig(method=SolverMethod.SOR, omega=1.0).method is SolverMethod.SOR


@pytest.mark.parametrize(
    ("rtol", "atol"),
    [(0.0, 0.0), (-1.0, 0.0), (0.0, -1.0), (float("nan"), 1e-10), (1e-6, float("inf"))],
)
def test_rechaza_tolerancias_invalidas(rtol: float, atol: float) -> None:
    with pytest.raises(InvalidSolverConfigError, match="tolerancias"):
        SolverConfig(method=SolverMethod.SOR, omega=1.2, rtol=rtol, atol=atol)


@pytest.mark.parametrize("max_iterations", [0, -1, True, 2.5])
def test_rechaza_maximo_invalido(max_iterations: int) -> None:
    with pytest.raises(InvalidSolverConfigError, match="max_iterations"):
        SolverConfig(method=SolverMethod.SOR, omega=1.2, max_iterations=max_iterations)


def sistema_identidad() -> LinearSystem:
    return LinearSystem(A=csr_array(np.eye(2)), b=np.zeros(2))


@pytest.mark.parametrize(
    "x0",
    [np.zeros((2, 1)), np.zeros(2, dtype=np.float32), np.array([0.0, float("nan")])],
)
def test_rechaza_x0_invalido(x0: np.ndarray) -> None:
    with pytest.raises(InvalidSolverConfigError, match="x0"):
        SolverConfig(method=SolverMethod.SOR, omega=1.2, x0=x0)


def test_valida_longitud_de_x0_con_el_sistema() -> None:
    config = SolverConfig(method=SolverMethod.SOR, omega=1.2, x0=np.zeros(3))
    with pytest.raises(InvalidSolverConfigError, match="incógnita"):
        config.validar_para_sistema(sistema_identidad(), 1e-10)


@pytest.mark.parametrize("tau", [0.0, -1.0, float("inf"), float("nan")])
def test_rechaza_umbral_efectivo_invalido(tau: float) -> None:
    config = SolverConfig(method=SolverMethod.SOR, omega=1.2, atol=0.0)
    with pytest.raises(InvalidSolverConfigError, match="umbral efectivo"):
        config.validar_para_sistema(sistema_identidad(), tau)


def test_b_cero_admite_umbral_absoluto_positivo() -> None:
    config = SolverConfig(method=SolverMethod.SOR, omega=1.2, x0=np.zeros(2))
    config.validar_para_sistema(sistema_identidad(), config.atol)


def resultado_convergente() -> SolverResult:
    """Fixture de diagnóstico; no corresponde a una ejecución real de SOR."""
    return SolverResult(
        method=SolverMethod.SOR,
        status=SolverStatus.CONVERGED,
        solution=np.array([1 / 3, 2 / 3], dtype=np.float64),
        iterations=2,
        sweeps=2,
        initial_residual=1.0,
        final_residual=1e-7,
        residual_history=(1.0, 1e-3, 1e-7),
        elapsed_seconds=0.02,
        omega_used=1.2,
        rtol=1e-6,
        atol=1e-10,
        max_iterations=2,
        stopping_threshold=1e-6,
        initialization="zero",
    )


def test_sor_informa_un_barrido_por_iteracion() -> None:
    resultado = resultado_convergente()
    assert resultado.converged
    assert resultado.sweeps == resultado.iterations == 2
    resultado.validar_para_sistema(sistema_identidad())


def test_sor_rechaza_barridos_incoherentes() -> None:
    with pytest.raises(ValueError, match="un barrido"):
        replace(resultado_convergente(), sweeps=4)


def test_convergencia_inicial_no_requiere_barridos() -> None:
    resultado = replace(
        resultado_convergente(),
        solution=np.zeros(2),
        iterations=0,
        sweeps=0,
        initial_residual=0.0,
        final_residual=0.0,
        residual_history=(0.0,),
    )
    assert resultado.converged


def test_rechaza_convergencia_con_residuo_alto() -> None:
    with pytest.raises(ValueError, match="umbral"):
        replace(resultado_convergente(), final_residual=0.1, residual_history=(1.0, 0.5, 0.1))


@pytest.mark.parametrize("solution", [None, np.array([float("nan")]), np.zeros(0)])
def test_convergencia_exige_solucion_finita(solution: np.ndarray | None) -> None:
    with pytest.raises(ValueError, match=r"solución|solution"):
        replace(resultado_convergente(), solution=solution)


def test_convergencia_valida_longitud_de_solucion() -> None:
    resultado = replace(resultado_convergente(), solution=np.zeros(3))
    with pytest.raises(ValueError, match="incógnita"):
        resultado.validar_para_sistema(sistema_identidad())


def resultado_maximo() -> SolverResult:
    return replace(
        resultado_convergente(),
        status=SolverStatus.MAX_ITERATIONS,
        solution=None,
        final_residual=0.1,
        residual_history=(1.0, 0.5, 0.1),
    )


def test_maximo_de_iteraciones_sin_solucion() -> None:
    resultado = resultado_maximo()
    assert not resultado.converged
    assert resultado.solution is None


def test_maximo_no_puede_publicar_solucion() -> None:
    with pytest.raises(ValueError, match="no convergente"):
        replace(resultado_maximo(), solution=np.zeros(2))


def test_maximo_exige_agotar_iteraciones() -> None:
    with pytest.raises(ValueError, match="MAX_ITERATIONS"):
        replace(resultado_maximo(), max_iterations=3)


def test_maximo_no_puede_reportar_residuo_convergente() -> None:
    with pytest.raises(ValueError, match="MAX_ITERATIONS"):
        replace(resultado_maximo(), final_residual=0.0, residual_history=(1.0, 0.5, 0.0))


def resultado_fallo_inicial() -> SolverResult:
    return replace(
        resultado_convergente(),
        status=SolverStatus.NUMERICAL_FAILURE,
        solution=None,
        iterations=0,
        sweeps=0,
        initial_residual=None,
        final_residual=None,
        residual_history=(),
        failure_code="NONFINITE_INITIAL_RESIDUAL",
    )


def test_fallo_inicial_no_inventa_residuos() -> None:
    resultado = resultado_fallo_inicial()
    assert resultado.residual_history == ()
    assert resultado.final_residual is None
    assert not resultado.converged


def test_fallo_inicial_rechaza_residuo_ficticio() -> None:
    with pytest.raises(ValueError, match="historial vacío"):
        replace(resultado_fallo_inicial(), initial_residual=0.0)


def resultado_fallo_intermedio() -> SolverResult:
    return replace(
        resultado_convergente(),
        status=SolverStatus.NUMERICAL_FAILURE,
        solution=None,
        iterations=1,
        sweeps=1,
        final_residual=0.5,
        residual_history=(1.0, 0.5),
        failure_code="NONFINITE_RESIDUAL",
        failed_at_sweep=2,
    )


def test_fallo_intermedio_conserva_historial_finito() -> None:
    resultado = resultado_fallo_intermedio()
    assert resultado.failed_at_sweep == 2
    assert resultado.residual_history == (1.0, 0.5)
    assert resultado.solution is None


def test_fallo_intermedio_rechaza_barrido_incoherente() -> None:
    with pytest.raises(ValueError, match="failed_at_sweep"):
        replace(resultado_fallo_intermedio(), failed_at_sweep=1)


def test_fallo_exige_codigo() -> None:
    with pytest.raises(ValueError, match="failure_code"):
        replace(resultado_fallo_inicial(), failure_code=None)


def test_historial_no_admite_nan() -> None:
    with pytest.raises(ValueError, match="finito"):
        replace(resultado_fallo_intermedio(), residual_history=(1.0, float("nan")))
