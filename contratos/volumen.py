"""Tipos volumétricos compartidos; no decodifican archivos ni calculan máscaras."""

from dataclasses import dataclass
from math import prod

import numpy as np
from numpy.typing import NDArray

from contratos.geometria import InputGeometry, InputMode
from contratos.imagen import SeedLabel

_VOLUME_DIMENSIONS = 3


def _validar_coordenadas(values: tuple[int, ...]) -> None:
    if len(values) != _VOLUME_DIMENSIONS or any(type(v) is not int or v < 0 for v in values):
        raise ValueError("las coordenadas 3D deben ser enteros no negativos")


@dataclass(frozen=True, slots=True, eq=False)
class VolumeData:
    """Intensidades escalares float32 en [0,1], orden [i,j,k].

    `geometry` describe el dominio completo; `roi_origin` identifica el origen
    del arreglo recibido. El arreglo puede representar un recorte. El receptor
    no debe mutar los voxels de otra capa; frozen no vuelve inmutable el ndarray.
    """

    voxels: NDArray[np.float32]
    source_format: str
    normalization: str
    geometry: InputGeometry
    roi_origin: tuple[int, int, int] = (0, 0, 0)

    def __post_init__(self) -> None:
        if self.geometry.mode != InputMode.THREE_D:
            raise ValueError("VolumeData exige geometría 3D")
        if self.voxels.ndim != _VOLUME_DIMENSIONS or not all(self.voxels.shape):
            raise ValueError("voxels debe ser un arreglo escalar 3D no vacío")
        if self.voxels.dtype != np.dtype("float32"):
            raise ValueError("voxels debe utilizar float32")
        if not np.all(np.isfinite(self.voxels)):
            raise ValueError("voxels contiene valores no finitos")
        if np.any(self.voxels < 0) or np.any(self.voxels > 1):
            raise ValueError("voxels debe estar normalizado en [0, 1]")
        if self.source_format != self.geometry.source_format or not self.normalization.strip():
            raise ValueError("formato o normalización incoherentes")
        self._validar_dominio()

    def _validar_dominio(self) -> None:
        _validar_coordenadas(self.roi_origin)
        if any(
            start + size > full
            for start, size, full in zip(
                self.roi_origin, self.shape, self.geometry.work_shape, strict=True
            )
        ):
            raise ValueError("el volumen preparado excede el dominio de trabajo")

    @property
    def shape(self) -> tuple[int, int, int]:
        return int(self.voxels.shape[0]), int(self.voxels.shape[1]), int(self.voxels.shape[2])


@dataclass(frozen=True, slots=True)
class ROI3DSelection:
    """Cuboide en índices de trabajo, con máximos exclusivos."""

    i_min: int
    j_min: int
    k_min: int
    i_max: int
    j_max: int
    k_max: int

    def __post_init__(self) -> None:
        _validar_coordenadas(self.origin)
        _validar_coordenadas(self.maximum)
        if any(lo >= hi for lo, hi in zip(self.origin, self.maximum, strict=True)):
            raise ValueError("la ROI debe tener volumen positivo")

    @property
    def origin(self) -> tuple[int, int, int]:
        return self.i_min, self.j_min, self.k_min

    @property
    def maximum(self) -> tuple[int, int, int]:
        return self.i_max, self.j_max, self.k_max

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.i_max - self.i_min, self.j_max - self.j_min, self.k_max - self.k_min

    @property
    def volume(self) -> int:
        """Cantidad de vóxeles, no volumen físico."""
        return prod(self.shape)

    def contains(self, position: tuple[int, int, int]) -> bool:
        _validar_coordenadas(position)
        return all(
            lo <= value < hi
            for lo, value, hi in zip(self.origin, position, self.maximum, strict=True)
        )


@dataclass(frozen=True, slots=True)
class Seed3D:
    """Semilla en índices globales de trabajo, nunca coordenadas de pantalla."""

    i: int
    j: int
    k: int
    label: SeedLabel

    def __post_init__(self) -> None:
        _validar_coordenadas(self.position)
        if not isinstance(self.label, SeedLabel):
            raise ValueError("la etiqueta de una semilla no es válida")

    @property
    def position(self) -> tuple[int, int, int]:
        return self.i, self.j, self.k


@dataclass(frozen=True, slots=True)
class Seed3DSelection:
    """Semillas de las dos clases, sin posiciones duplicadas."""

    seeds: tuple[Seed3D, ...]

    def __post_init__(self) -> None:
        coordinates = [seed.position for seed in self.seeds]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError("no puede haber semillas repetidas en un mismo vóxel")
        labels = {seed.label for seed in self.seeds}
        if labels != {SeedLabel.FOREGROUND, SeedLabel.BACKGROUND}:
            raise ValueError("se necesitan semillas de primer plano y fondo")
