"""DTO de entrada HTTP v2. Validacion estructural, no admision de archivos."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from capa_2_control.validaciones import validar_seleccion, validar_seleccion_3d_forma
from contratos.imagen import ROISelection, Seed, SeedLabel, SeedSelection
from contratos.reconstruccion import ModelConfig
from contratos.solver import SolverConfig, SolverMethod
from contratos.volumen import ROI3DSelection, Seed3D, Seed3DSelection

type PositiveInt = Annotated[int, Field(gt=0, strict=True)]
type Coordinate = Annotated[int, Field(ge=0, strict=True)]
type NonNegativeFloat = Annotated[float, Field(ge=0, strict=True)]
type Threshold = Annotated[float, Field(gt=0, lt=1, strict=True)]
type Omega = Annotated[float, Field(gt=0, lt=2, strict=True)]
type InputId = Annotated[str, Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
type PreparationVersion = Annotated[str, Field(min_length=1, pattern=r"\S")]
type Label = Literal["foreground", "background"]


class RequestDTO(BaseModel):
    """No convierte cadenas a numeros ni acepta campos adicionales."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)


class PreviewRequest(RequestDTO):
    contract_version: Literal["2"]
    mode: Literal["2d", "3d"]


class ROI2DDTO(RequestDTO):
    x_min: Coordinate
    y_min: Coordinate
    x_max: PositiveInt
    y_max: PositiveInt

    def a_dominio(self) -> ROISelection:
        return ROISelection(self.x_min, self.y_min, self.x_max, self.y_max)


class ROI3DDTO(RequestDTO):
    i_min: Coordinate
    j_min: Coordinate
    k_min: Coordinate
    i_max: PositiveInt
    j_max: PositiveInt
    k_max: PositiveInt

    def a_dominio(self) -> ROI3DSelection:
        return ROI3DSelection(
            self.i_min, self.j_min, self.k_min, self.i_max, self.j_max, self.k_max
        )


class Seed2DDTO(RequestDTO):
    x: Coordinate
    y: Coordinate
    label: Label

    def a_dominio(self) -> Seed:
        return Seed(self.x, self.y, SeedLabel(self.label))


class Seed3DDTO(RequestDTO):
    i: Coordinate
    j: Coordinate
    k: Coordinate
    label: Label

    def a_dominio(self) -> Seed3D:
        return Seed3D(self.i, self.j, self.k, SeedLabel(self.label))


class ModelParameters(RequestDTO):
    beta: NonNegativeFloat
    threshold: Threshold

    def a_dominio(self) -> ModelConfig:
        return ModelConfig(beta=self.beta, threshold=self.threshold)


class SolverParameters(RequestDTO):
    omega: Omega
    rtol: NonNegativeFloat
    atol: NonNegativeFloat
    max_iterations: PositiveInt

    def a_dominio(self) -> SolverConfig:
        return SolverConfig(
            method=SolverMethod.SOR,
            omega=self.omega,
            rtol=self.rtol,
            atol=self.atol,
            max_iterations=self.max_iterations,
        )

    @model_validator(mode="after")
    def validar_tolerancias(self) -> Self:
        self.a_dominio()
        return self


class SegmentRequestBase(RequestDTO):
    contract_version: Literal["2"]
    request_id: UUID
    input_id: InputId
    preparation_version: PreparationVersion
    model: ModelParameters
    solver: SolverParameters


class SegmentRequest2D(SegmentRequestBase):
    mode: Literal["2d"]
    work_shape: tuple[PositiveInt, PositiveInt]
    roi: ROI2DDTO
    seeds: tuple[Seed2DDTO, ...]

    def seleccion(self) -> tuple[ROISelection, SeedSelection]:
        return self.roi.a_dominio(), SeedSelection(tuple(seed.a_dominio() for seed in self.seeds))

    @model_validator(mode="after")
    def validar_seleccion_declarada(self) -> Self:
        roi, seeds = self.seleccion()
        height, width = self.work_shape
        validar_seleccion(width, height, roi, seeds)
        return self


class SegmentRequest3D(SegmentRequestBase):
    mode: Literal["3d"]
    work_shape: tuple[PositiveInt, PositiveInt, PositiveInt]
    roi: ROI3DDTO
    seeds: tuple[Seed3DDTO, ...]

    def seleccion(self) -> tuple[ROI3DSelection, Seed3DSelection]:
        return self.roi.a_dominio(), Seed3DSelection(tuple(seed.a_dominio() for seed in self.seeds))

    @model_validator(mode="after")
    def validar_seleccion_declarada(self) -> Self:
        roi, seeds = self.seleccion()
        validar_seleccion_3d_forma(self.work_shape, roi, seeds)
        return self


type SegmentRequest = Annotated[SegmentRequest2D | SegmentRequest3D, Field(discriminator="mode")]

_SEGMENT_REQUEST_ADAPTER: TypeAdapter[SegmentRequest] = TypeAdapter(SegmentRequest)


def parsear_segment_request(content: str | bytes) -> SegmentRequest2D | SegmentRequest3D:
    """Valida JSON v2; el llamador debe aplicar limites de bytes antes de invocarla.

    La seleccion declarada es provisional hasta cotejarla con datos decodificados.
    No exponer las excepciones de Pydantic sin filtrar en respuestas o logs HTTP.
    """
    return _SEGMENT_REQUEST_ADAPTER.validate_json(content, strict=True)
