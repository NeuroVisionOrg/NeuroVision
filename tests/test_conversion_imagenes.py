from pathlib import Path

import numpy as np
from PIL import Image

from capa_3_traduccion.imagenes import imagen_a_matriz, leer_png_gris, matriz_a_imagen


def test_conversion_conserva_los_pixeles() -> None:
    pixeles = np.array([[20, 30, 210], [25, 180, 220]], dtype=np.uint8)
    original = Image.fromarray(pixeles)

    matriz = imagen_a_matriz(original)
    reconstruida = matriz_a_imagen(matriz)

    np.testing.assert_array_equal(np.array(reconstruida), pixeles)


def test_leer_png_gris_normaliza_los_pixeles(tmp_path: Path) -> None:
    pixeles = np.array([[0, 51, 102], [153, 204, 255]], dtype=np.uint8)
    ruta = tmp_path / "imagen_gris.png"
    Image.fromarray(pixeles).save(ruta)

    resultado = leer_png_gris(ruta)

    esperado = np.array([[0.0, 0.2, 0.4], [0.6, 0.8, 1.0]], dtype=np.float32)
    assert resultado.dtype == np.float32
    np.testing.assert_allclose(resultado, esperado)
