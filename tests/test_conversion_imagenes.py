from pathlib import Path

import numpy as np
import pytest
from PIL import Image, UnidentifiedImageError

# Las pruebas llaman al lector desde la misma entrada que usará Control.
from capa_3_traduccion.api_publica import cargar_imagen_gris
from capa_3_traduccion.imagenes import (
    imagen_a_matriz,
    leer_png_gris,
    matriz_a_imagen,
)


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


@pytest.mark.parametrize(
    ("nombre", "modo", "formato_esperado"),
    [
        ("resonancia.jpg", "RGB", "JPEG"),
        ("resonancia.png", "L", "PNG"),
    ],
)
def test_cargar_imagen_gris(tmp_path: Path, nombre: str, modo: str, formato_esperado: str) -> None:
    ruta = tmp_path / nombre
    imagen = Image.new("L", (3, 2), color=128)
    imagen.convert(modo).save(ruta)

    datos = cargar_imagen_gris(ruta)

    assert datos.source_format == formato_esperado
    assert datos.pixels.shape == (2, 3)
    assert datos.pixels.dtype == np.float32
    np.testing.assert_allclose(datos.pixels, 128 / 255)


def test_cargar_imagen_gris_rechaza_png_ilegible(tmp_path: Path) -> None:
    ruta = tmp_path / "resonancia.png"
    ruta.write_bytes(b"archivo de prueba sin datos de imagen")

    with pytest.raises(UnidentifiedImageError):
        cargar_imagen_gris(ruta)


def test_cargar_imagen_gris_rechaza_modo_rgba(tmp_path: Path) -> None:
    """Comprueba que el lector rechaza un PNG válido con canal de transparencia."""
    ruta = tmp_path / "imagen_con_transparencia.png"

    # El cuarto valor es la opacidad. Pillow guardará el PNG en modo RGBA.
    imagen = Image.new("RGBA", (3, 2), color=(128, 128, 128, 100))
    imagen.save(ruta)

    # Verificamos que el rechazo se deba al modo de color que valida nuestra función.
    with pytest.raises(ValueError, match="modo L o RGB"):
        cargar_imagen_gris(ruta)
