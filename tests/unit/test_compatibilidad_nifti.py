"""Comprobacion de NiBabel con datos sinteticos, sin lector del producto."""

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest


@pytest.mark.parametrize("extension", [".nii", ".nii.gz"])
def test_nifti_conserva_intensidades_y_geometria(tmp_path: Path, extension: str) -> None:
    datos = np.arange(60, dtype=np.float32).reshape((3, 4, 5))
    afin = np.array(
        [
            [0.0, -2.0, 0.0, 10.0],
            [2.0, 0.0, 0.0, -7.0],
            [0.0, 0.0, 2.0, 11.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    original = nib.Nifti1Image(datos, afin)
    original.header.set_xyzt_units("mm")
    ruta = tmp_path / f"fixture{extension}"
    nib.save(original, str(ruta))

    leido = nib.load(str(ruta))
    assert isinstance(leido, nib.Nifti1Image)
    assert leido.shape == (3, 4, 5)
    assert leido.header.get_xyzt_units()[0] == "mm"
    assert leido.header.get_zooms() == (2.0, 2.0, 2.0)
    assert leido.affine is not None
    np.testing.assert_array_equal(leido.affine, afin)
    np.testing.assert_array_equal(leido.get_fdata(dtype=np.dtype(np.float32)), datos)

    # Permutacion e inversion sin interpolar: componente del fixture FX-04.
    canonico = nib.as_closest_canonical(leido)
    assert isinstance(canonico, nib.Nifti1Image)
    assert canonico.shape == (4, 3, 5)
    assert canonico.affine is not None
    assert nib.aff2axcodes(canonico.affine) == ("R", "A", "S")
    np.testing.assert_array_equal(
        canonico.get_fdata(dtype=np.dtype(np.float32)), datos.transpose(1, 0, 2)[::-1]
    )
    np.testing.assert_array_equal(
        canonico.affine @ np.array([1.0, 1.0, 3.0, 1.0]),
        afin @ np.array([1.0, 2.0, 3.0, 1.0]),
    )
