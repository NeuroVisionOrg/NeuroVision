"""Contratos de mallas, métricas y exportaciones; no generan resultados."""

from dataclasses import dataclass
from enum import StrEnum
from math import isclose, isfinite
from re import fullmatch

import numpy as np
from numpy.typing import NDArray

from contratos.datos import ReferencePolicy, validar_politica_referencia
from contratos.geometria import InputMode

_TRIANGLE_SIZE = 3
_MESH_DIMENSIONS = 2


class MeshStatus(StrEnum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True, eq=False)
class MeshData:
    vertices: NDArray[np.float64]
    faces: NDArray[np.int64]
    touches_boundary: bool
    warnings: tuple[str, ...] = ()
    frame: str = "RAS+"
    units: str = "mm"

    def __post_init__(self) -> None:
        if self.frame != "RAS+" or self.units != "mm":
            raise ValueError("malla debe estar en RAS+ y mm")
        if type(self.touches_boundary) is not bool:
            raise ValueError("indicador de contacto inválido")
        self._validar_vertices()
        self._validar_caras()

    def _validar_vertices(self) -> None:
        if (
            self.vertices.ndim != _MESH_DIMENSIONS
            or self.vertices.shape[1] != _TRIANGLE_SIZE
            or self.vertices.shape[0] < _TRIANGLE_SIZE
            or self.vertices.dtype != np.dtype("float64")
        ):
            raise ValueError("vértices deben tener forma (m,3) y dtype float64")
        if not np.all(np.isfinite(self.vertices)):
            raise ValueError("vértices no finitos")

    def _validar_caras(self) -> None:
        if (
            self.faces.ndim != _MESH_DIMENSIONS
            or self.faces.shape[1] != _TRIANGLE_SIZE
            or not self.faces.size
            or self.faces.dtype != np.dtype("int64")
        ):
            raise ValueError("caras deben tener forma (f,3) y dtype int64")
        if np.any(self.faces < 0) or np.any(self.faces >= len(self.vertices)):
            raise ValueError("índices de caras fuera de rango")
        triangles = self.vertices[self.faces]
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        if not np.all(np.isfinite(cross)) or np.any(np.all(cross == 0, axis=1)):
            raise ValueError("triángulos degenerados o no finitos")


@dataclass(frozen=True, slots=True, eq=False)
class MeshResult:
    status: MeshStatus
    mesh: MeshData | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, MeshStatus):
            raise ValueError("estado de malla desconocido")
        if self.status in {MeshStatus.OK, MeshStatus.PARTIAL}:
            if self.mesh is None:
                raise ValueError("OK/PARTIAL exige una malla válida")
            if self.mesh.touches_boundary != (self.status == MeshStatus.PARTIAL):
                raise ValueError("PARTIAL debe reflejar contacto con la frontera")
        elif self.mesh is not None or not self.reason or not self.reason.strip():
            raise ValueError("malla no disponible o fallida exige motivo y ninguna malla")


@dataclass(frozen=True, slots=True)
class MetricsResult:
    """Conteos y métricas de una referencia alineada, exclusivamente en ROI."""

    mode: InputMode
    reference_id: str
    reference_policy: ReferencePolicy
    foreground_count: int
    reference_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    dice: float | None
    iou: float | None
    domain: str = "roi"
    volume_mm3: float | None = None

    def __post_init__(self) -> None:
        self._validar_contexto()
        self._validar_conteos()
        self._validar_metricas()

    def _validar_contexto(self) -> None:
        if not isinstance(self.mode, InputMode) or self.domain != "roi":
            raise ValueError("modo o dominio de evaluación inválido")
        if not self.reference_id.strip():
            raise ValueError("identidad de referencia inválida")
        validar_politica_referencia(self.mode, self.reference_policy)
        if self.volume_mm3 is not None and (
            self.mode != InputMode.THREE_D or not isfinite(self.volume_mm3) or self.volume_mm3 < 0
        ):
            raise ValueError("volumen físico inválido")

    def _validar_conteos(self) -> None:
        counts = (
            self.foreground_count,
            self.reference_count,
            self.true_positives,
            self.false_positives,
            self.false_negatives,
        )
        if any(type(count) is not int or count < 0 for count in counts):
            raise ValueError("conteos deben ser enteros no negativos")
        if self.foreground_count != self.true_positives + self.false_positives:
            raise ValueError("conteo de primer plano incoherente")
        if self.reference_count != self.true_positives + self.false_negatives:
            raise ValueError("conteo de referencia incoherente")

    def _validar_metricas(self) -> None:
        tp = self.true_positives
        union = tp + self.false_positives + self.false_negatives
        if union == 0:
            if self.dice is not None or self.iou is not None:
                raise ValueError("máscaras ambas vacías: Dice e IoU deben ser None")
            return
        _validar_cociente(self.dice, 2 * tp / (self.foreground_count + self.reference_count))
        _validar_cociente(self.iou, tp / union)


def _validar_cociente(value: float | None, expected: float) -> None:
    if (
        value is None
        or isinstance(value, bool)
        or not isfinite(value)
        or not 0 <= value <= 1
        or not isclose(value, expected, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise ValueError("métrica incoherente con los conteos")


@dataclass(frozen=True, slots=True)
class ExportResult:
    filename: str
    media_type: str
    content: bytes

    def __post_init__(self) -> None:
        stem = self.filename.split(".", maxsplit=1)[0].upper()
        reserved = fullmatch(r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", stem)
        if (
            fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", self.filename) is None
            or self.filename.endswith(".")
            or reserved is not None
        ):
            raise ValueError("nombre de exportación inseguro")
        if not self.media_type.strip() or not isinstance(self.content, bytes) or not self.content:
            raise ValueError("exportación requiere tipo y contenido no vacío")
