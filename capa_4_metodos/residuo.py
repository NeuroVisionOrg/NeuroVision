"""Residuo y criterio de parada comunes a la capa de métodos.

El criterio es el acordado en ``docs/contratos.md``:
``||b - A x||_2 <= max(atol, rtol * ||b||_2)``.
"""

import numpy as np
from numpy.typing import NDArray

from contratos.sistema import LinearSystem


def norma_residuo(sistema: LinearSystem, x: NDArray[np.float64]) -> float:
    """Norma euclídea de ``b - A x`` calculada sobre el sistema original."""
    if x.shape != sistema.b.shape:
        raise ValueError("x debe tener una entrada por incógnita")
    residuo = sistema.b - sistema.A @ x
    return float(np.linalg.norm(residuo))


def umbral_parada(sistema: LinearSystem, rtol: float, atol: float) -> float:
    """Valor del residuo por debajo del cual una iteración se considera convergente."""
    return max(atol, rtol * float(np.linalg.norm(sistema.b)))


def es_finito(valor: float) -> bool:
    """Indica si un residuo sigue siendo un número válido."""
    return bool(np.isfinite(valor))
