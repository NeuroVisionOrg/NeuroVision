"""Presupuesto y errores de admision; sin HTTP ni implementacion de lectores."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True, kw_only=True)
class DataReadLimits:
    """El lector debe comprobar estos limites antes de expandir o asignar datos."""

    max_decompressed_bytes: int
    max_axis_length: int
    max_domain_elements: int

    def __post_init__(self) -> None:
        values = (self.max_decompressed_bytes, self.max_axis_length, self.max_domain_elements)
        if any(type(value) is not int or value <= 0 for value in values):
            raise ValueError("los limites de lectura deben ser enteros positivos")


class DataReadCode(StrEnum):
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    INVALID_IMAGE = "INVALID_IMAGE"
    UNSUPPORTED_COLOR = "UNSUPPORTED_COLOR"
    UNSUPPORTED_GEOMETRY = "UNSUPPORTED_GEOMETRY"
    DECOMPRESSED_LIMIT = "DECOMPRESSED_LIMIT"


class DataReadError(ValueError):
    """Fallo previsto de admision; no incluye el archivo ni su ruta."""

    def __init__(self, code: DataReadCode) -> None:
        super().__init__(code.value)
        self.code = code
