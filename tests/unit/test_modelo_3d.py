"""Propiedades del sistema Random Walker 3D descritas en docs/modelo_matematico.md."""

import numpy as np
import pytest
from scipy.sparse import csr_array
from scipy.sparse.linalg import spsolve

from capa_4_metodos.residuo import norma_residuo, umbral_parada
from contratos.sistema import LinearSystem
from tests.apoyo.sistemas_3d import caso_poisson, caso_tumor_esferico, normalizar_min_max


@pytest.fixture(scope="module")
def caso_tumor():
    return caso_tumor_esferico(lado=10)


def test_matriz_es_simetrica_y_dispersa(caso_tumor) -> None:
    a = caso_tumor.sistema.A
    assert abs(a - a.T).max() < 1e-14
    assert a.nnz <= 7 * caso_tumor.sistema.n


def test_matriz_es_m_matriz_diagonal_dominante(caso_tumor) -> None:
    a = caso_tumor.sistema.A
    diagonal = a.diagonal()
    fuera = a.tocoo()
    fuera_diagonal = fuera.data[fuera.row != fuera.col]
    assert np.all(fuera_diagonal <= 0)
    suma_fuera = np.asarray(abs(a).sum(axis=1)).ravel() - diagonal
    assert np.all(diagonal >= suma_fuera - 1e-12)
    assert np.any(diagonal > suma_fuera + 1e-9)


def test_matriz_es_definida_positiva(caso_tumor) -> None:
    densa = caso_tumor.sistema.A.toarray()
    assert np.linalg.eigvalsh(densa).min() > 0


def test_poisson_tiene_estencil_de_siete_puntos() -> None:
    caso = caso_poisson(4)
    a = caso.sistema.A
    assert caso.sistema.n == 64
    np.testing.assert_allclose(a.diagonal(), 6.0)


def test_probabilidades_quedan_entre_cero_y_uno(caso_tumor) -> None:
    x = spsolve(caso_tumor.sistema.A.tocsc(), caso_tumor.sistema.b)
    assert x.min() >= -1e-12
    assert x.max() <= 1 + 1e-12
    volumen = caso_tumor.reconstruir(np.asarray(x))
    assert volumen.shape == (10, 10, 10)
    centro = volumen[5, 5, 5]
    assert centro == pytest.approx(1.0)


def test_pesos_son_positivos_y_normalizacion_en_cero_uno() -> None:
    volumen = np.array([[[10.0, 20.0], [30.0, 50.0]]], dtype=np.float32)
    g = normalizar_min_max(volumen)
    assert g.min() == 0.0
    assert g.max() == 1.0
    np.testing.assert_array_equal(normalizar_min_max(np.ones((2, 2, 2), np.float32)), 0.0)
    with pytest.raises(ValueError, match="beta"):
        caso_tumor_esferico(lado=8, beta=-1.0)


def test_residuo_y_umbral_del_caso_base() -> None:
    sistema = LinearSystem(
        A=csr_array(np.array([[2.0, -1.0], [-1.0, 2.0]])),
        b=np.array([0.0, 1.0]),
    )
    assert norma_residuo(sistema, np.array([1 / 3, 2 / 3])) == pytest.approx(0, abs=1e-15)
    assert norma_residuo(sistema, np.zeros(2)) == pytest.approx(1.0)
    assert umbral_parada(sistema, rtol=1e-6, atol=1e-10) == pytest.approx(1e-6)
    with pytest.raises(ValueError, match="incógnita"):
        norma_residuo(sistema, np.zeros(3))
