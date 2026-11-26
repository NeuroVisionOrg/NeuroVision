"""Sistemas Random Walker 3D sintéticos para probar la capa de métodos.

Este módulo es solo de apoyo para pruebas: la construcción oficial del sistema pertenece a
la capa de traducción. Sigue ``docs/modelo_matematico.md`` (secciones 2 a 4): normalización
min-max de la ROI, 6 vecinos, pesos exp(-beta (g_i - g_j)^2) sin regularización y
A = L_UU, b = -L_UM p_M.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_array, csr_array

from contratos.sistema import LinearSystem


@dataclass(frozen=True, slots=True, eq=False)
class CasoRandomWalker3D:
    """Sistema reducido y datos para reconstruir el volumen de probabilidades."""

    sistema: LinearSystem
    forma: tuple[int, int, int]
    indices_incognitas: NDArray[np.int64]
    semillas_tumor: NDArray[np.bool_]
    semillas_fondo: NDArray[np.bool_]

    def reconstruir(self, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """Devuelve el volumen de probabilidades con las semillas reinsertadas."""
        volumen = np.zeros(int(np.prod(self.forma)), dtype=np.float64)
        volumen[self.semillas_tumor.ravel()] = 1.0
        volumen[self.indices_incognitas] = x
        return volumen.reshape(self.forma)


def normalizar_min_max(volumen: NDArray[np.float32]) -> NDArray[np.float64]:
    """Lleva la ROI a [0, 1]; si la intensidad es constante devuelve ceros."""
    intensidad = volumen.astype(np.float64)
    if not np.all(np.isfinite(intensidad)):
        raise ValueError("las intensidades deben ser finitas")
    minimo, maximo = intensidad.min(), intensidad.max()
    if maximo == minimo:
        return np.zeros_like(intensidad)
    return (intensidad - minimo) / (maximo - minimo)


def _aristas_6_vecinos(
    volumen: NDArray[np.float32], beta: float
) -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.float64]]:
    """Aristas (i, j, w) de la cuadrícula 3D con 6-conectividad."""
    if not np.isfinite(beta) or beta < 0:
        raise ValueError("beta debe ser finito y no negativo")
    indices = np.arange(volumen.size, dtype=np.int64).reshape(volumen.shape)
    intensidad = normalizar_min_max(volumen)
    origenes, destinos, pesos = [], [], []
    for eje in range(3):
        delante = [slice(None)] * 3
        detras = [slice(None)] * 3
        delante[eje] = slice(1, None)
        detras[eje] = slice(None, -1)
        diferencia = intensidad[tuple(delante)] - intensidad[tuple(detras)]
        origenes.append(indices[tuple(detras)].ravel())
        destinos.append(indices[tuple(delante)].ravel())
        pesos.append(np.exp(-beta * diferencia**2).ravel())
    w = np.concatenate(pesos)
    if not np.all(np.isfinite(w)) or not np.all(w > 0):
        raise ValueError("los pesos deben ser finitos y estrictamente positivos")
    return np.concatenate(origenes), np.concatenate(destinos), w


def laplaciano_3d(volumen: NDArray[np.float32], beta: float) -> csr_array:
    """Laplaciano ponderado L = D - W del volumen completo."""
    i, j, w = _aristas_6_vecinos(volumen, beta)
    n = volumen.size
    filas = np.concatenate([i, j])
    columnas = np.concatenate([j, i])
    adyacencia = coo_array((np.concatenate([w, w]), (filas, columnas)), shape=(n, n)).tocsr()
    grados = np.asarray(adyacencia.sum(axis=1)).ravel()
    diagonal = coo_array((grados, (np.arange(n), np.arange(n))), shape=(n, n)).tocsr()
    return csr_array(diagonal - adyacencia)


def construir_caso(
    volumen: NDArray[np.float32],
    semillas_tumor: NDArray[np.bool_],
    semillas_fondo: NDArray[np.bool_],
    beta: float,
) -> CasoRandomWalker3D:
    """Construye A = L_UU y b = -L_UM x_M para un volumen 3D."""
    if volumen.ndim != 3:
        raise ValueError("se esperaba un volumen 3D")
    if np.any(semillas_tumor & semillas_fondo):
        raise ValueError("un vóxel no puede ser semilla de ambas clases")
    if not semillas_tumor.any() or not semillas_fondo.any():
        raise ValueError("se necesitan semillas de tumor y de fondo")
    laplaciano = laplaciano_3d(volumen, beta)
    semilla = (semillas_tumor | semillas_fondo).ravel()
    incognitas = np.flatnonzero(~semilla)
    marcadas = np.flatnonzero(semilla)
    x_m = semillas_tumor.ravel()[marcadas].astype(np.float64)
    a = csr_array(laplaciano[incognitas][:, incognitas])
    a.sum_duplicates()
    a.sort_indices()
    b = -(laplaciano[incognitas][:, marcadas] @ x_m)
    return CasoRandomWalker3D(
        sistema=LinearSystem(A=a, b=np.asarray(b, dtype=np.float64)),
        forma=(volumen.shape[0], volumen.shape[1], volumen.shape[2]),
        indices_incognitas=incognitas.astype(np.int64),
        semillas_tumor=semillas_tumor,
        semillas_fondo=semillas_fondo,
    )


def caso_poisson(m: int) -> CasoRandomWalker3D:
    """Cubo interior m³ rodeado de semillas con beta = 0: Poisson 3D de 7 puntos."""
    lado = m + 2
    volumen = np.zeros((lado, lado, lado), dtype=np.float32)
    borde = np.ones_like(volumen, dtype=np.bool_)
    borde[1:-1, 1:-1, 1:-1] = False
    tumor = np.zeros_like(borde)
    tumor[0, 1:-1, 1:-1] = True
    return construir_caso(volumen, tumor, borde & ~tumor, beta=0.0)


def caso_tumor_esferico(
    lado: int, beta: float = 90.0, ruido: float = 0.05, semilla_aleatoria: int = 7
) -> CasoRandomWalker3D:
    """Esfera brillante con ruido gaussiano, semillas en su centro y en el borde."""
    generador = np.random.default_rng(semilla_aleatoria)
    z, y, x = np.indices((lado, lado, lado))
    centro = (lado - 1) / 2
    distancia = np.sqrt((z - centro) ** 2 + (y - centro) ** 2 + (x - centro) ** 2)
    radio = lado / 4
    volumen = np.where(distancia <= radio, 0.8, 0.2) + generador.normal(0, ruido, distancia.shape)
    volumen = np.clip(volumen, 0, 1).astype(np.float32)
    tumor = distancia <= radio / 2
    fondo = np.zeros_like(tumor)
    fondo[[0, -1], :, :] = True
    fondo[:, [0, -1], :] = True
    fondo[:, :, [0, -1]] = True
    return construir_caso(volumen, tumor, fondo, beta=beta)
