"""Contrato de sistema lineal disperso compartido con los cuatro métodos."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csr_array


@dataclass(frozen=True, slots=True, eq=False)
class LinearSystem:
    """Ax=b, validado estructuralmente (sin hacer comprobación costosa de SPD).

    La conectividad y la positividad definida del Laplaciano corresponden al
    proceso de construcción y a pruebas específicas de Traducción.
    """

    A: csr_array
    b: NDArray[np.float64]

    def __post_init__(self) -> None:
        if not isinstance(self.A, csr_array):
            raise ValueError("A debe ser scipy.sparse.csr_array")
        rows, columns = self.A.shape
        if rows == 0 or rows != columns:
            raise ValueError("A debe ser cuadrada y no vacía")
        if self.A.dtype != np.dtype("float64") or self.b.dtype != np.dtype("float64"):
            raise ValueError("A y b deben utilizar float64")
        if self.b.shape != (rows,):
            raise ValueError("b debe tener exactamente una entrada por fila")
        if not np.all(np.isfinite(self.A.data)) or not np.all(np.isfinite(self.b)):
            raise ValueError("A y b deben contener valores finitos")
        if not np.all(self.A.diagonal() > 0):
            raise ValueError("la diagonal de A debe ser estrictamente positiva")
        if not self.A.has_canonical_format:
            raise ValueError("A debe ser CSR canónica sin índices duplicados")

    @property
    def n(self) -> int:
        return int(self.A.shape[0])
