"""Contratos internos para imágenes, regiones de interés y semillas."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class SeedLabel(str, Enum):
    """Valores conocidos para el modelo binario Random Walker."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"


@dataclass(frozen=True, slots=True, eq=False)
class ImageData:
    """Imagen gris normalizada, con dimensiones derivadas de ``pixels``."""

    pixels: NDArray[np.float32]
    source_format: str
    normalization: str

    def __post_init__(self) -> None:
        if self.pixels.ndim != 2 or not all(self.pixels.shape):
            raise ValueError("pixels debe ser una matriz 2D no vacía")
        if self.pixels.dtype != np.dtype("float32"):
            raise ValueError("pixels debe utilizar float32")
        if not np.all(np.isfinite(self.pixels)):
            raise ValueError("pixels contiene valores no finitos")
        if np.any(self.pixels < 0) or np.any(self.pixels > 1):
            raise ValueError("pixels debe estar normalizado en [0, 1]")
        if not self.source_format or not self.normalization:
            raise ValueError("debe documentarse el formato y la normalización")

    @property
    def height(self) -> int:
        """Número de filas."""
        return int(self.pixels.shape[0])

    @property
    def width(self) -> int:
        """Número de columnas."""
        return int(self.pixels.shape[1])


@dataclass(frozen=True, slots=True)
class ROISelection:
    """Rectángulo en coordenadas originales, con máximos exclusivos."""

    x_min: int
    y_min: int
    x_max: int
    y_max: int

    def __post_init__(self) -> None:
        if any(type(value) is not int for value in (
            self.x_min, self.y_min, self.x_max, self.y_max
        )):
            raise ValueError("las coordenadas de ROI deben ser enteros")
        if self.x_min < 0 or self.y_min < 0:
            raise ValueError("la ROI no puede tener coordenadas negativas")
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("la ROI debe tener un área positiva")

    @property
    def width(self) -> int:
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        return self.y_max - self.y_min

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True, slots=True)
class Seed:
    """Píxel marcado en coordenadas originales."""

    x: int
    y: int
    label: SeedLabel

    def __post_init__(self) -> None:
        if type(self.x) is not int or type(self.y) is not int:
            raise ValueError("las coordenadas de una semilla deben ser enteros")
        if self.x < 0 or self.y < 0:
            raise ValueError("las coordenadas de una semilla deben ser no negativas")
        if not isinstance(self.label, SeedLabel):
            raise ValueError("la etiqueta de una semilla no es válida")


@dataclass(frozen=True, slots=True)
class SeedSelection:
    """Colección de semillas de las dos clases sin posiciones duplicadas."""

    seeds: tuple[Seed, ...]

    def __post_init__(self) -> None:
        coordinates = [(seed.x, seed.y) for seed in self.seeds]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError("no puede haber semillas repetidas en un mismo píxel")
        labels = {seed.label for seed in self.seeds}
        if labels != {SeedLabel.FOREGROUND, SeedLabel.BACKGROUND}:
            raise ValueError("se necesitan semillas de primer plano y fondo")
