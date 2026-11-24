import numpy as np
from PIL import Image

from capa_3_traduccion.imagenes import imagen_a_matriz, matriz_a_imagen


def test_conversion_conserva_los_pixeles() -> None:
    pixeles = np.array([[20, 30, 210], [25, 180, 220]], dtype=np.uint8)
    original = Image.fromarray(pixeles)

    matriz = imagen_a_matriz(original)
    reconstruida = matriz_a_imagen(matriz)

    np.testing.assert_array_equal(np.array(reconstruida), pixeles)
