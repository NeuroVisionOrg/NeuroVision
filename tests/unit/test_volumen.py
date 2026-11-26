"""Pruebas estructurales con geometrías sintéticas; no usan archivos médicos."""

from dataclasses import replace

import numpy as np
import pytest

from capa_2_control.validaciones import validar_seleccion_3d
from contratos.geometria import InputGeometry, InputMode, SpatialGeometry
from contratos.imagen import SeedLabel
from contratos.volumen import ROI3DSelection, Seed3D, Seed3DSelection, VolumeData


def geometria_3d() -> InputGeometry:
    h_work = np.diag([2.0, 2.0, 2.0, 1.0])
    h_work[:3, 3] = [10, -4, 8]
    return InputGeometry(
        mode=InputMode.THREE_D,
        original_shape=(5, 6, 7),
        work_shape=(5, 6, 7),
        source_format="NIfTI",
        spatial=SpatialGeometry(
            h_original=h_work.copy(),
            h_work=h_work,
            t_work_to_original=np.eye(4, dtype=np.int64),
            spacing_mm=(2.0, 2.0, 2.0),
            axis_codes=("R", "A", "S"),
            affine_source="synthetic",
            atol_mm=1e-9,
        ),
    )


def geometria_2d() -> InputGeometry:
    return InputGeometry(InputMode.TWO_D, (6, 5), (6, 5), "PNG")


def datos() -> VolumeData:
    return VolumeData(
        voxels=np.zeros((3, 3, 3), dtype=np.float32),
        source_format="NIfTI",
        normalization="synthetic",
        geometry=geometria_3d(),
        roi_origin=(2, 3, 4),
    )


def semillas_validas() -> Seed3DSelection:
    return Seed3DSelection(
        (Seed3D(1, 2, 3, SeedLabel.FOREGROUND), Seed3D(2, 3, 4, SeedLabel.BACKGROUND))
    )


def test_geometria_2d_no_inventa_afin() -> None:
    geometry = geometria_2d()
    assert geometry.spatial is None
    assert geometry.work_shape == (6, 5)


def test_geometria_2d_rechaza_reescalado() -> None:
    with pytest.raises(ValueError, match="reescalado"):
        replace(geometria_2d(), work_shape=(12, 10))


def test_geometria_2d_rechaza_metadatos_3d() -> None:
    with pytest.raises(ValueError, match="afín física"):
        replace(geometria_2d(), spatial=geometria_3d().spatial)


@pytest.mark.parametrize("shape", [(5, 6), (5, 6, 7, 1), (0, 6, 7), (True, 6, 7)])
def test_geometria_rechaza_forma_invalida(shape: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="forma"):
        replace(geometria_3d(), work_shape=shape)


def test_geometria_3d_exige_metadatos() -> None:
    with pytest.raises(ValueError, match="metadatos"):
        replace(geometria_3d(), spatial=None)


def test_geometria_permutada_e_invertida_conserva_punto_fisico() -> None:
    base = geometria_3d().spatial
    assert base is not None
    transform = np.array([[0, -1, 0, 5], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    transform = transform.astype(np.int64)
    original = base.h_work @ np.linalg.inv(transform.astype(np.float64))
    spatial = replace(base, h_original=original, t_work_to_original=transform)
    geometry = InputGeometry(InputMode.THREE_D, (6, 5, 7), (5, 6, 7), "NIfTI", spatial)
    p = np.array([2, 3, 4, 1], dtype=np.float64)
    np.testing.assert_array_equal(transform @ p, [2, 2, 4, 1])
    np.testing.assert_allclose(spatial.h_original @ (transform @ p), spatial.h_work @ p)
    with pytest.raises(ValueError, match="formas completas"):
        replace(geometry, original_shape=(5, 6, 7))


def test_afin_copiada_sin_alias_mutable() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    original = spatial.h_original.copy()
    copied = replace(spatial, h_original=original)
    original[0, 3] = 99
    assert copied.h_original[0, 3] == 10
    assert not copied.h_original.flags.writeable


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf")])
def test_rechaza_espaciado_invalido(value: float) -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    with pytest.raises(ValueError, match="espaciamiento"):
        replace(spatial, spacing_mm=(value, 2.0, 2.0))


def test_rechaza_anisotropia() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    with pytest.raises(ValueError, match="isotrópico"):
        replace(spatial, spacing_mm=(2.0, 2.0, 3.0))


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf"), 2.0])
def test_rechaza_tolerancia_invalida(value: float) -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    with pytest.raises(ValueError, match="tolerancia"):
        replace(spatial, atol_mm=value)


@pytest.mark.parametrize("field", ["h_original", "h_work"])
@pytest.mark.parametrize("case", ["shape", "dtype", "nan", "last_row", "singular"])
def test_rechaza_afin_invalida(field: str, case: str) -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    affine = spatial.h_work.copy()
    if case == "shape":
        affine = affine[:3, :3]
    elif case == "dtype":
        affine = affine.astype(np.float32)
    elif case == "nan":
        affine[0, 0] = np.nan
    elif case == "last_row":
        affine[3, 0] = 1
    else:
        affine[0, 0] = 0
    with pytest.raises(ValueError, match="afín"):
        replace(spatial, **{field: affine})


def test_rechaza_afin_inconsistente() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    original = spatial.h_original.copy()
    original[0, 3] += 1
    with pytest.raises(ValueError, match="h_work no coincide"):
        replace(spatial, h_original=original)


def test_rechaza_cizalla_en_dominio_trabajo() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    h_work = spatial.h_work.copy()
    h_work[0, 1] = 0.1
    with pytest.raises(ValueError, match="ejes y el espaciamiento"):
        replace(spatial, h_work=h_work, h_original=h_work.copy())


def test_rechaza_orientacion_no_ras() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    with pytest.raises(ValueError, match=r"RAS\+"):
        replace(spatial, axis_codes=("L", "A", "S"))


def test_rechaza_transformacion_no_permutacion() -> None:
    spatial = geometria_3d().spatial
    assert spatial is not None
    transform = np.eye(4, dtype=np.int64)
    transform[0, 1] = 1
    with pytest.raises(ValueError, match="permutación"):
        replace(spatial, t_work_to_original=transform)


def test_rechaza_desplazamiento_incompatible_con_cuadricula() -> None:
    geometry = geometria_3d()
    spatial = geometry.spatial
    assert spatial is not None
    transform = np.eye(4, dtype=np.int64)
    transform[0, 3] = 1
    h_work = spatial.h_original @ transform
    updated = replace(spatial, h_work=h_work, t_work_to_original=transform)
    with pytest.raises(ValueError, match="formas completas"):
        replace(geometry, spatial=updated)


def test_volumen_recortado_conserva_origen_y_forma() -> None:
    volume = datos()
    assert volume.roi_origin == (2, 3, 4)
    assert volume.shape == (3, 3, 3)
    assert volume.geometry.work_shape == (5, 6, 7)
    np.testing.assert_array_equal(volume.voxels, 0)


@pytest.mark.parametrize(
    "voxels",
    [
        np.zeros((3, 3), dtype=np.float32),
        np.zeros((3, 3, 3, 1), dtype=np.float32),
        np.zeros((0, 3, 3), dtype=np.float32),
        np.zeros((3, 3, 3), dtype=np.float64),
        np.full((3, 3, 3), np.nan, dtype=np.float32),
        np.full((3, 3, 3), -0.1, dtype=np.float32),
        np.full((3, 3, 3), 1.1, dtype=np.float32),
    ],
)
def test_volumen_rechaza_intensidades_invalidas(voxels: np.ndarray) -> None:
    with pytest.raises(ValueError, match="voxels"):
        replace(datos(), voxels=voxels)


def test_volumen_rechaza_recorte_fuera_de_dominio() -> None:
    with pytest.raises(ValueError, match="excede el dominio"):
        replace(datos(), roi_origin=(3, 3, 4))


def test_volumen_rechaza_formato_incoherente() -> None:
    with pytest.raises(ValueError, match="formato"):
        replace(datos(), source_format="PNG")


def test_volumen_rechaza_geometria_2d() -> None:
    with pytest.raises(ValueError, match="geometría 3D"):
        replace(datos(), geometry=geometria_2d())


def test_roi_y_semillas_en_coordenadas_de_trabajo() -> None:
    roi = ROI3DSelection(1, 2, 3, 5, 6, 7)
    assert roi.shape == (4, 4, 4)
    assert roi.volume == 64
    assert roi.contains((1, 2, 3))
    assert not roi.contains((5, 2, 3))
    validar_seleccion_3d(geometria_3d(), roi, semillas_validas())


@pytest.mark.parametrize("origin", [(-1, 2, 3), (True, 2, 3), (5, 2, 3), (6, 2, 3)])
def test_roi_rechaza_limites_invalidos(origin: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError):
        ROI3DSelection(*origin, 5, 6, 7)


def test_semilla_rechaza_booleano_y_negativo() -> None:
    with pytest.raises(ValueError, match="coordenadas"):
        Seed3D(True, 2, 3, SeedLabel.FOREGROUND)
    with pytest.raises(ValueError, match="coordenadas"):
        Seed3D(1, -1, 3, SeedLabel.FOREGROUND)


def test_semillas_rechazan_clase_ausente_y_duplicados() -> None:
    a = Seed3D(1, 2, 3, SeedLabel.FOREGROUND)
    b = Seed3D(1, 2, 3, SeedLabel.BACKGROUND)
    with pytest.raises(ValueError, match="primer plano y fondo"):
        Seed3DSelection((a,))
    with pytest.raises(ValueError, match="repetidas"):
        Seed3DSelection((a, b))


def test_control_rechaza_roi_fuera_de_volumen() -> None:
    with pytest.raises(ValueError, match="excede las dimensiones"):
        validar_seleccion_3d(geometria_3d(), ROI3DSelection(1, 2, 3, 6, 6, 7), semillas_validas())


def test_control_rechaza_semilla_en_limite_exclusivo() -> None:
    with pytest.raises(ValueError, match="fuera de la ROI"):
        validar_seleccion_3d(geometria_3d(), ROI3DSelection(1, 2, 3, 2, 6, 7), semillas_validas())


def test_control_rechaza_roi_sin_incognitas() -> None:
    seeds = Seed3DSelection(
        (Seed3D(1, 2, 3, SeedLabel.FOREGROUND), Seed3D(1, 2, 4, SeedLabel.BACKGROUND))
    )
    with pytest.raises(ValueError, match="desconocidos"):
        validar_seleccion_3d(geometria_3d(), ROI3DSelection(1, 2, 3, 2, 3, 5), seeds)
