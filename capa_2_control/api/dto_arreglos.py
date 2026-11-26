"""Transporte de arreglos HTTP v2; no transforma datos anatomicos."""

from base64 import b64decode, b64encode
from math import prod
from typing import Annotated, Literal, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, model_validator

from capa_2_control.api.dto_entrada import PositiveInt, RequestDTO

type ArrayDType = Literal["uint8", "float32_le", "uint32_le"]
type ArrayShape = Annotated[tuple[PositiveInt, ...], Field(min_length=1, max_length=3)]

_WIRE_DTYPES: dict[str, ArrayDType] = {
    "uint8": "uint8",
    "float32": "float32_le",
    "uint32": "uint32_le",
}
_SUPPORTED_RANKS = (1, 2, 3)
_NUMPY_DTYPES = {"uint8": "u1", "float32_le": "<f4", "uint32_le": "<u4"}


class PayloadLimitError(ValueError):
    """Un arreglo excede el presupuesto de bytes indicado por Control."""


def _comprobar_limite(nbytes: int, max_bytes: int) -> None:
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("el limite de bytes debe ser un entero positivo")
    if nbytes > max_bytes:
        raise PayloadLimitError("el arreglo supera el limite de bytes")


def _longitud_base64(nbytes: int) -> int:
    return 4 * ((nbytes + 2) // 3)


class ArrayDTO(RequestDTO):
    """Estructura de transporte. Para consumir bytes, usar decodificar_arreglo.

    La validacion del modelo comprueba metadatos y longitud codificada, no
    decodifica ni reserva memoria para el arreglo. El consumidor aplica un
    presupuesto explicito antes de decodificar y valida su semantica concreta.
    """

    dtype: ArrayDType
    shape: ArrayShape
    order: Literal["C"]
    encoding: Literal["base64"]
    data: str

    @property
    def nbytes(self) -> int:
        return prod(self.shape) * np.dtype(_NUMPY_DTYPES[self.dtype]).itemsize

    @model_validator(mode="after")
    def validar_longitud(self) -> Self:
        if len(self.data) != _longitud_base64(self.nbytes):
            raise ValueError("longitud Base64 incompatible con forma y dtype")
        return self


def codificar_arreglo(array: NDArray[np.generic], *, max_bytes: int) -> ArrayDTO:
    """Codifica sin mutar, en orden C y little-endian; no reduce precision."""
    if array.ndim not in _SUPPORTED_RANKS or array.size == 0:
        raise ValueError("se requiere un arreglo no vacio de uno a tres ejes")
    dtype = _WIRE_DTYPES.get(array.dtype.name)
    if dtype is None:
        raise ValueError("dtype no admitido para transporte")
    _comprobar_limite(array.nbytes, max_bytes)
    if dtype == "float32_le" and not np.all(np.isfinite(array)):
        raise ValueError("arreglo de transporte no finito")
    ordered = array.astype(_NUMPY_DTYPES[dtype], copy=False)
    return ArrayDTO(
        dtype=dtype,
        shape=array.shape,
        order="C",
        encoding="base64",
        data=b64encode(ordered.tobytes(order="C")).decode("ascii"),
    )


def decodificar_arreglo(dto: ArrayDTO, *, max_bytes: int) -> NDArray[np.generic]:
    """Limita bytes antes de decodificar; no valida semantica de mascara/malla.

    El limite del cuerpo JSON completo debe comprobarse antes de crear el DTO.
    Devuelve una vista de solo lectura sobre los bytes decodificados.
    """
    _comprobar_limite(dto.nbytes, max_bytes)
    if len(dto.data) != _longitud_base64(dto.nbytes):
        raise ValueError("longitud Base64 incompatible con forma y dtype")
    padding = (-dto.nbytes) % 3
    if not dto.data.endswith("=" * padding) or dto.data.endswith("=" * (padding + 1)):
        raise ValueError("relleno Base64 incompatible con la longitud esperada")
    try:
        raw = b64decode(dto.data, validate=True)
    except ValueError as exc:
        raise ValueError("Base64 invalido") from exc
    if len(raw) != dto.nbytes:
        raise ValueError("longitud decodificada incompatible con forma y dtype")
    array: NDArray[np.generic] = np.frombuffer(raw, dtype=_NUMPY_DTYPES[dto.dtype]).reshape(
        dto.shape
    )
    if dto.dtype == "float32_le" and not np.all(np.isfinite(array)):
        raise ValueError("arreglo de transporte no finito")
    return array
