"""Presupuestos explicitos de Control; no configura valores de produccion."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, fields
from enum import StrEnum
from math import prod
from threading import BoundedSemaphore
from typing import BinaryIO

from contratos.datos import DecodedData


class ResourceCode(StrEnum):
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    DECOMPRESSED_LIMIT = "DECOMPRESSED_LIMIT"
    ROI_LIMIT = "ROI_LIMIT"
    PAYLOAD_LIMIT = "PAYLOAD_LIMIT"
    INVALID_SOLVER_CONFIG = "INVALID_SOLVER_CONFIG"
    RESOURCE_BUSY = "RESOURCE_BUSY"


class ResourceLimitError(ValueError):
    """Rechazo previsto por politica de recursos, sin contenido de la solicitud."""

    def __init__(self, code: ResourceCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def _cantidad(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("se requiere una cantidad entera no negativa")


def _comprobar(value: int, maximum: int, code: ResourceCode, message: str) -> None:
    _cantidad(value)
    if value > maximum:
        raise ResourceLimitError(code, message)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResourceLimits:
    """Limites por operacion, todos obligatorios y positivos.

    Los bytes de cuerpo incluyen multipart; los de JSON, la parte request.
    Los bytes descomprimidos deben limitarse tambien durante la lectura real.
    Los limites de arreglo son de bytes crudos, no de caracteres Base64.
    La configuracion no constituye una cota de memoria total ni de latencia.
    """

    max_request_bytes: int
    max_file_bytes: int
    max_json_bytes: int
    max_decompressed_bytes: int
    max_axis_length: int
    max_domain_elements: int
    max_roi_elements: int
    max_unknowns: int
    max_seeds: int
    max_iterations: int
    max_array_bytes: int
    max_response_bytes: int
    max_concurrent_requests: int

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field.name} debe ser un entero positivo")

    def validar_cuerpo(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_request_bytes,
            ResourceCode.PAYLOAD_LIMIT,
            "el cuerpo HTTP supera el limite de bytes",
        )

    def validar_archivo(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_file_bytes,
            ResourceCode.FILE_TOO_LARGE,
            "el archivo supera el limite de bytes",
        )

    def validar_json(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_json_bytes,
            ResourceCode.PAYLOAD_LIMIT,
            "el JSON de solicitud supera el limite de bytes",
        )

    def validar_descompresion(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_decompressed_bytes,
            ResourceCode.DECOMPRESSED_LIMIT,
            "los datos descomprimidos superan el limite de bytes",
        )

    def validar_forma(self, shape: tuple[int, ...]) -> None:
        if len(shape) not in (2, 3) or any(type(n) is not int or n <= 0 for n in shape):
            raise ValueError("se requiere una forma espacial 2D o 3D positiva")
        _comprobar(
            max(shape),
            self.max_axis_length,
            ResourceCode.DECOMPRESSED_LIMIT,
            "un eje supera el limite de dimensiones",
        )
        _comprobar(
            prod(shape),
            self.max_domain_elements,
            ResourceCode.DECOMPRESSED_LIMIT,
            "el dominio supera el limite de elementos",
        )

    def validar_roi(self, elements: int, seeds: int) -> None:
        _cantidad(elements)
        _cantidad(seeds)
        if seeds >= elements:
            raise ValueError("la seleccion debe contener incognitas")
        _comprobar(
            elements,
            self.max_roi_elements,
            ResourceCode.ROI_LIMIT,
            "la ROI supera el limite de elementos",
        )
        _comprobar(
            seeds,
            self.max_seeds,
            ResourceCode.ROI_LIMIT,
            "la seleccion supera el limite de semillas",
        )
        _comprobar(
            elements - seeds,
            self.max_unknowns,
            ResourceCode.ROI_LIMIT,
            "el sistema supera el limite de incognitas",
        )

    def validar_iteraciones(self, iterations: int) -> None:
        _comprobar(
            iterations,
            self.max_iterations,
            ResourceCode.INVALID_SOLVER_CONFIG,
            "el maximo de iteraciones supera la politica del servidor",
        )

    def validar_arreglo(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_array_bytes,
            ResourceCode.PAYLOAD_LIMIT,
            "el arreglo supera el limite de bytes",
        )

    def validar_respuesta(self, nbytes: int) -> None:
        _comprobar(
            nbytes,
            self.max_response_bytes,
            ResourceCode.PAYLOAD_LIMIT,
            "la respuesta supera el limite de bytes",
        )


def validar_datos_decodificados(data: DecodedData, limits: ResourceLimits) -> None:
    """Segunda defensa; el lector debe limitar expansion antes de asignar."""
    limits.validar_forma(data.geometry.original_shape)
    limits.validar_forma(data.geometry.work_shape)
    limits.validar_descompresion(data.intensities.nbytes)


def leer_archivo_acotado(stream: BinaryIO, limits: ResourceLimits) -> bytes:
    """Lee desde la posicion actual, sin cerrar el stream ni leer sin cota.

    No sustituye un limite del cuerpo HTTP antes del parser multipart.
    Se inspecciona como maximo un byte por encima del presupuesto de archivo.
    """
    result = bytearray()
    while True:
        remaining = limits.max_file_bytes - len(result)
        chunk = stream.read(min(64 * 1024, remaining + 1))
        if not chunk:
            return bytes(result)
        limits.validar_archivo(len(result) + len(chunk))
        result.extend(chunk)


class ProcessingCapacity:
    """Cupo no bloqueante, propiedad de una instancia de la aplicacion."""

    def __init__(self, limits: ResourceLimits) -> None:
        self._slots = BoundedSemaphore(limits.max_concurrent_requests)

    @contextmanager
    def ocupar(self) -> Iterator[None]:
        if not self._slots.acquire(blocking=False):
            raise ResourceLimitError(ResourceCode.RESOURCE_BUSY, "capacidad de proceso ocupada")
        try:
            yield
        finally:
            self._slots.release()
