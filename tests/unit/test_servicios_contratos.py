"""Validación estructural de salidas de Servicios, sin Marching Cubes ni IO."""

from dataclasses import replace

import numpy as np
import pytest

from contratos.datos import ReferencePolicy
from contratos.geometria import InputMode
from contratos.servicios import ExportResult, MeshData, MeshResult, MeshStatus, MetricsResult


def malla() -> MeshData:
    return MeshData(
        vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64),
        faces=np.array([[0, 1, 2]], dtype=np.int64),
        touches_boundary=False,
    )


@pytest.mark.parametrize(
    "faces",
    [
        np.array([[0, 1, 3]], dtype=np.int64),
        np.array([[0, 1, -1]], dtype=np.int64),
        np.array([[0, 0, 1]], dtype=np.int64),
        np.array([[0, 1, 2]], dtype=np.float64),
        np.zeros((0, 3), dtype=np.int64),
    ],
)
def test_rechaza_caras_invalidas(faces: np.ndarray) -> None:
    with pytest.raises(ValueError):
        replace(malla(), faces=faces)


def test_rechaza_triangulo_colineal_y_no_finito() -> None:
    with pytest.raises(ValueError, match="degenerados"):
        replace(malla(), vertices=np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float64))
    with pytest.raises(ValueError, match="no finitos"):
        replace(malla(), vertices=np.full((3, 3), np.nan, dtype=np.float64))


def test_estados_malla() -> None:
    assert MeshResult(MeshStatus.OK, malla()).mesh is not None
    partial = replace(malla(), touches_boundary=True)
    assert MeshResult(MeshStatus.PARTIAL, partial).mesh is partial
    assert MeshResult(MeshStatus.UNAVAILABLE, reason="no_level_crossing").mesh is None
    assert MeshResult(MeshStatus.FAILED, reason="extraction_error").mesh is None
    with pytest.raises(ValueError, match="PARTIAL"):
        MeshResult(MeshStatus.OK, partial)
    with pytest.raises(ValueError, match="PARTIAL"):
        MeshResult(MeshStatus.PARTIAL, malla())
    with pytest.raises(ValueError, match="motivo"):
        MeshResult(MeshStatus.UNAVAILABLE)
    with pytest.raises(ValueError, match="motivo"):
        MeshResult(MeshStatus.FAILED, malla(), "error")
    with pytest.raises(ValueError, match="malla válida"):
        MeshResult(MeshStatus.OK)


def metricas() -> MetricsResult:
    return MetricsResult(
        mode=InputMode.TWO_D,
        reference_id="synthetic-reference",
        reference_policy=ReferencePolicy.BRISC_BIN_128,
        foreground_count=3,
        reference_count=4,
        true_positives=2,
        false_positives=1,
        false_negatives=2,
        dice=4 / 7,
        iou=2 / 5,
    )


def test_metricas_coherentes() -> None:
    result = metricas()
    assert result.domain == "roi"
    assert result.dice == pytest.approx(4 / 7)
    assert result.iou == pytest.approx(2 / 5)


@pytest.mark.parametrize(
    "changes",
    [
        {"foreground_count": 2},
        {"reference_count": 3},
        {"false_negatives": -1},
        {"true_positives": True},
        {"dice": 1.0},
        {"iou": float("nan")},
        {"iou": None},
        {"domain": "full"},
        {"volume_mm3": 5.0},
        {"reference_policy": ReferencePolicy.ITKSNAP_LABEL_2},
    ],
)
def test_metricas_invalidas(changes: dict) -> None:
    with pytest.raises(ValueError):
        replace(metricas(), **changes)


def test_metricas_vacias_no_inventan_perfeccion() -> None:
    empty = replace(
        metricas(),
        foreground_count=0,
        reference_count=0,
        true_positives=0,
        false_positives=0,
        false_negatives=0,
        dice=None,
        iou=None,
    )
    with pytest.raises(ValueError, match="vacías"):
        replace(empty, dice=1.0, iou=1.0)


def test_metricas_3d() -> None:
    result = replace(
        metricas(),
        mode=InputMode.THREE_D,
        reference_policy=ReferencePolicy.ITKSNAP_LABEL_2,
        volume_mm3=3.0,
    )
    assert result.volume_mm3 == 3.0


@pytest.mark.parametrize(
    "filename", ["../result.csv", "..", "a/b.csv", "a\\b.csv", "x\n.csv", "NUL.csv", "run."]
)
def test_exportacion_rechaza_nombre_inseguro(filename: str) -> None:
    with pytest.raises(ValueError, match="inseguro"):
        ExportResult(filename, "text/csv", b"a,b\n")


def test_exportacion_valida() -> None:
    assert ExportResult("run-1.csv", "text/csv", b"a,b\n").filename == "run-1.csv"
    with pytest.raises(ValueError, match="contenido"):
        ExportResult("run-1.csv", "text/csv", b"")
