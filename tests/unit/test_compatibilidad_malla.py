"""Comprobacion de Marching Cubes con el fixture sintetico FX-06."""

import numpy as np
from skimage.measure import marching_cubes


def test_marching_cubes_superficie_y_escala() -> None:
    mascara = np.zeros((8, 9, 7), dtype=np.float32)
    mascara[2:5, 3:6, 1:4] = 1.0
    vertices, caras, normales, _ = marching_cubes(
        mascara, level=0.5, spacing=(1.0, 1.0, 1.0), allow_degenerate=False
    )
    assert vertices.ndim == 2 and vertices.shape[1] == 3 and len(vertices) > 0
    assert caras.ndim == 2 and caras.shape[1] == 3 and len(caras) > 0
    assert np.issubdtype(caras.dtype, np.integer)
    assert caras.min() >= 0 and caras.max() < len(vertices)
    assert np.all(np.isfinite(vertices))
    assert normales.shape == vertices.shape and np.all(np.isfinite(normales))
    np.testing.assert_array_equal(vertices.min(axis=0), [1.5, 2.5, 0.5])
    np.testing.assert_array_equal(vertices.max(axis=0), [4.5, 5.5, 3.5])

    triangulos = vertices[caras]
    dobles_areas = np.linalg.norm(
        np.cross(triangulos[:, 1] - triangulos[:, 0], triangulos[:, 2] - triangulos[:, 0]), axis=1
    )
    assert np.all(dobles_areas > 0)

    # Oraculo fisico del fixture: offset ROI y afin se aplican una sola vez.
    desplazamiento = np.array([10, 20, 30], dtype=np.float64)
    traslacion = np.array([5, -7, 11], dtype=np.float64)
    fisicos = (vertices.astype(np.float64) + desplazamiento) * 2 + traslacion
    np.testing.assert_array_equal(fisicos.min(axis=0), [28, 38, 72])
    np.testing.assert_array_equal(fisicos.max(axis=0), [34, 44, 78])
