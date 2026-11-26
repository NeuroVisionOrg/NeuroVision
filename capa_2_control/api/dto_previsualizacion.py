"""Respuesta de previsualizacion HTTP v2, a partir de datos de Traduccion."""

from typing import Annotated, Literal, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import ConfigDict, Field, model_validator

from capa_2_control.api.dto_arreglos import ArrayDTO, codificar_arreglo
from capa_2_control.api.dto_entrada import InputId, PositiveInt, PreparationVersion, RequestDTO
from contratos.datos import PreviewData
from contratos.geometria import InputGeometry, InputMode

type Shape2D = tuple[PositiveInt, PositiveInt]
type Shape3D = tuple[PositiveInt, PositiveInt, PositiveInt]
type FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
type StrictInt = Annotated[int, Field(strict=True)]
type FloatRow4 = tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
type IntRow4 = tuple[StrictInt, StrictInt, StrictInt, StrictInt]
type FloatMatrix4 = tuple[FloatRow4, FloatRow4, FloatRow4, FloatRow4]
type IntMatrix4 = tuple[IntRow4, IntRow4, IntRow4, IntRow4]
type PositiveFloat = Annotated[float, Field(gt=0, strict=True)]
type NonBlank = Annotated[str, Field(min_length=1, pattern=r"\S")]


class ImageGeometry2D(RequestDTO):
    mode: Literal["2d"]
    original_shape: Shape2D
    work_shape: Shape2D
    source_format: NonBlank

    @model_validator(mode="after")
    def validar_formas(self) -> Self:
        if self.original_shape != self.work_shape:
            raise ValueError("la geometria 2D no admite reescalado")
        return self


class ImageGeometry3D(RequestDTO):
    """Representacion de salida; la geometria se admite en Traduccion."""

    model_config = ConfigDict(serialize_by_alias=True)

    mode: Literal["3d"]
    original_shape: Shape3D
    work_shape: Shape3D
    source_format: NonBlank
    h_original: FloatMatrix4 = Field(alias="H_original")
    h_work: FloatMatrix4 = Field(alias="H_work")
    t_work_to_original: IntMatrix4 = Field(alias="T_work_to_original")
    spacing_mm: tuple[PositiveFloat, PositiveFloat, PositiveFloat]
    units: Literal["mm"]
    axis_codes: tuple[Literal["R"], Literal["A"], Literal["S"]]
    affine_source: NonBlank


type ImageGeometryDTO = Annotated[ImageGeometry2D | ImageGeometry3D, Field(discriminator="mode")]


class PreviewDTO(RequestDTO):
    """Salida HTTP; usar model_dump_json(by_alias=True) al serializar."""

    model_config = ConfigDict(serialize_by_alias=True)

    contract_version: Literal["2"]
    input_id: InputId
    preparation_version: PreparationVersion
    geometry: ImageGeometryDTO
    view: ArrayDTO
    display_min: float
    display_max: float
    warnings: tuple[str, ...]

    @model_validator(mode="after")
    def validar_vista(self) -> Self:
        if self.view.dtype != "uint8" or self.view.shape != self.geometry.work_shape:
            raise ValueError("vista uint8 incompatible con la geometria")
        if self.display_min > self.display_max:
            raise ValueError("rango de visualizacion invertido")
        return self


def _fila_float(row: NDArray[np.float64]) -> FloatRow4:
    return float(row[0]), float(row[1]), float(row[2]), float(row[3])


def _fila_int(row: NDArray[np.int64]) -> IntRow4:
    return int(row[0]), int(row[1]), int(row[2]), int(row[3])


def _matriz_float(matrix: NDArray[np.float64]) -> FloatMatrix4:
    return (
        _fila_float(matrix[0]),
        _fila_float(matrix[1]),
        _fila_float(matrix[2]),
        _fila_float(matrix[3]),
    )


def _matriz_int(matrix: NDArray[np.int64]) -> IntMatrix4:
    return (
        _fila_int(matrix[0]),
        _fila_int(matrix[1]),
        _fila_int(matrix[2]),
        _fila_int(matrix[3]),
    )


def a_dto_geometria(geometry: InputGeometry) -> ImageGeometry2D | ImageGeometry3D:
    """Copia metadatos sin reorientar ni aplicar una afin adicional."""
    original = geometry.original_shape
    work = geometry.work_shape
    if geometry.mode == InputMode.TWO_D:
        return ImageGeometry2D(
            mode="2d",
            original_shape=(original[0], original[1]),
            work_shape=(work[0], work[1]),
            source_format=geometry.source_format,
        )
    spatial = geometry.spatial
    if spatial is None:
        raise ValueError("faltan metadatos espaciales")
    return ImageGeometry3D(
        mode="3d",
        original_shape=(original[0], original[1], original[2]),
        work_shape=(work[0], work[1], work[2]),
        source_format=geometry.source_format,
        H_original=_matriz_float(spatial.h_original),
        H_work=_matriz_float(spatial.h_work),
        T_work_to_original=_matriz_int(spatial.t_work_to_original),
        spacing_mm=spatial.spacing_mm,
        units="mm",
        axis_codes=("R", "A", "S"),
        affine_source=spatial.affine_source,
    )


def a_dto_preview(preview: PreviewData, *, max_view_bytes: int) -> PreviewDTO:
    """Adapta la vista ya preparada; no decodifica ni normaliza el original."""
    return PreviewDTO(
        contract_version="2",
        input_id=preview.input_id,
        preparation_version=preview.preparation_version,
        geometry=a_dto_geometria(preview.geometry),
        view=codificar_arreglo(preview.uint8_view, max_bytes=max_view_bytes),
        display_min=preview.display_min,
        display_max=preview.display_max,
        warnings=preview.warnings,
    )
