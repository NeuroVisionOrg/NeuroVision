from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

DIMENSIONES_IMAGEN_GRIS = 2


def imagen_a_matriz(imagen: Image.Image) -> NDArray[np.float32]:
    """Convierte una imagen gris de 8 bits en una matriz de intensidades entre 0 y 1."""
    if imagen.mode != "L":
        raise ValueError("Se esperaba una imagen en escala de grises de 8 bits.")

    pixeles = np.array(imagen, dtype=np.float32)
    return pixeles / np.float32(255.0)


def matriz_a_imagen(matriz: NDArray[np.float32]) -> Image.Image:
    """Reconstruye una imagen gris de 8 bits a partir de una matriz normalizada."""
    if matriz.ndim != DIMENSIONES_IMAGEN_GRIS or matriz.size == 0:
        raise ValueError("Se esperaba una matriz de píxeles de dos dimensiones, con datos.")

    if not np.isfinite(matriz).all():
        raise ValueError("La matriz contiene valores no finitos.")

    if np.any(matriz < 0) or np.any(matriz > 1):
        raise ValueError("Las intensidades deben estar entre 0 y 1.")

    pixeles = np.rint(matriz * 255).astype(np.uint8)
    return Image.fromarray(pixeles)


def leer_png_gris(ruta: Path) -> NDArray[np.float32]:
    """Lee un archivo PNG en escala de grises de 8 bits y devuelve su matriz normalizada."""
    with Image.open(ruta, formats=("PNG",)) as imagen:
        return imagen_a_matriz(imagen)
