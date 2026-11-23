"""Pruebas pequeñas de contratos de imagen, ROI y semillas."""

import numpy as np
import pytest

from capa_2_control.validaciones import validar_seleccion
from contratos.imagen import ImageData, ROISelection, Seed, SeedLabel, SeedSelection


def _semillas_validas() -> SeedSelection:
    return SeedSelection((
        Seed(x=34, y=25, label=SeedLabel.FOREGROUND),
        Seed(x=22, y=12, label=SeedLabel.BACKGROUND),
    ))


def test_imagen_deriva_dimensiones_de_matriz() -> None:
    imagen = ImageData(
        pixels=np.zeros((80, 120), dtype=np.float32),
        source_format="PNG",
        normalization="grayscale_0_1",
    )
    assert (imagen.width, imagen.height) == (120, 80)


def test_imagen_rechaza_valores_fuera_del_rango() -> None:
    pixels = np.array([[0.0, 1.2]], dtype=np.float32)
    with pytest.raises(ValueError, match="normalizado"):
        ImageData(pixels=pixels, source_format="PNG", normalization="grayscale_0_1")


def test_roi_40x40_y_semillas_locales() -> None:
    roi = ROISelection(x_min=20, y_min=10, x_max=60, y_max=50)
    assert (roi.width, roi.height) == (40, 40)
    validar_seleccion(120, 80, roi, _semillas_validas())
    assert (34 - roi.x_min, 25 - roi.y_min) == (14, 15)
    assert (22 - roi.x_min, 12 - roi.y_min) == (2, 2)


def test_semillas_repetidas_se_rechazan() -> None:
    with pytest.raises(ValueError, match="repetidas"):
        SeedSelection((
            Seed(20, 20, SeedLabel.FOREGROUND),
            Seed(20, 20, SeedLabel.BACKGROUND),
        ))


def test_semilla_fuera_de_roi_se_rechaza() -> None:
    roi = ROISelection(20, 10, 60, 50)
    semillas = SeedSelection((
        Seed(61, 25, SeedLabel.FOREGROUND),
        Seed(22, 12, SeedLabel.BACKGROUND),
    ))
    with pytest.raises(ValueError, match="fuera de la ROI"):
        validar_seleccion(120, 80, roi, semillas)
