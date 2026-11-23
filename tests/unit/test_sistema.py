"""Pruebas estructurales del sistema lineal, sin implementar solvers."""

import numpy as np
import pytest
from scipy.sparse import csr_array

from contratos.sistema import LinearSystem


def test_sistema_de_referencia_tiene_dos_incognitas() -> None:
    matriz = csr_array(np.array([[2.0, -1.0], [-1.0, 2.0]], dtype=np.float64))
    vector = np.array([0.0, 1.0], dtype=np.float64)
    sistema = LinearSystem(A=matriz, b=vector)
    assert sistema.n == 2
    solucion_referencia = np.linalg.solve(matriz.toarray(), vector)
    np.testing.assert_allclose(solucion_referencia, [1 / 3, 2 / 3])


def test_rechaza_vector_con_dimension_incompatible() -> None:
    matriz = csr_array(np.eye(2, dtype=np.float64))
    with pytest.raises(ValueError, match="entrada por fila"):
        LinearSystem(A=matriz, b=np.zeros(3, dtype=np.float64))


def test_rechaza_diagonal_no_positiva() -> None:
    matriz = csr_array(np.array([[0.0, -1.0], [-1.0, 2.0]], dtype=np.float64))
    with pytest.raises(ValueError, match="diagonal"):
        LinearSystem(A=matriz, b=np.array([0.0, 1.0], dtype=np.float64))
