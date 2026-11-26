"""Orquestacion de previsualizacion, sin decodificar ni normalizar imagenes."""

from hashlib import sha256
from typing import Protocol

import numpy as np

from capa_2_control.recursos import ResourceLimits, validar_datos_decodificados
from contratos.admision import DataReadLimits
from contratos.datos import DecodedData, PreviewData
from contratos.geometria import InputGeometry, InputMode


class PreviewOperations(Protocol):
    """Puerto de Control para las dos operaciones publicas de Traduccion."""

    def leer_datos(
        self, content: bytes, mode: InputMode, *, limits: DataReadLimits
    ) -> DecodedData: ...

    def previsualizar(self, data: DecodedData) -> PreviewData: ...


def _misma_geometria(left: InputGeometry, right: InputGeometry) -> bool:
    """Compara identidad geometrica sin depender de los DTO HTTP."""
    if (left.mode, left.original_shape, left.work_shape, left.source_format) != (
        right.mode,
        right.original_shape,
        right.work_shape,
        right.source_format,
    ):
        return False
    a, b = left.spatial, right.spatial
    if a is None or b is None:
        return a is b
    return (
        a.spacing_mm == b.spacing_mm
        and a.axis_codes == b.axis_codes
        and a.affine_source == b.affine_source
        and a.atol_mm == b.atol_mm
        and np.array_equal(a.h_original, b.h_original)
        and np.array_equal(a.h_work, b.h_work)
        and np.array_equal(a.t_work_to_original, b.t_work_to_original)
    )


def preparar_previsualizacion(
    content: bytes, mode: InputMode, limits: ResourceLimits, operations: PreviewOperations
) -> PreviewData:
    """Revalida identidad y geometria; no sustituye la admision previa del lector."""
    limits.validar_archivo(len(content))
    read_limits = DataReadLimits(
        max_decompressed_bytes=limits.max_decompressed_bytes,
        max_axis_length=limits.max_axis_length,
        max_domain_elements=limits.max_domain_elements,
    )
    digest = sha256(content).hexdigest()
    data = operations.leer_datos(content, mode, limits=read_limits)
    validar_datos_decodificados(data, limits)
    if data.source_digest != digest or data.geometry.mode != mode:
        raise RuntimeError("Traduccion devolvio una identidad o modo incompatible")
    preview = operations.previsualizar(data)
    if preview.input_id != digest or not _misma_geometria(preview.geometry, data.geometry):
        raise RuntimeError("Traduccion devolvio una vista de otro dominio")
    return preview
