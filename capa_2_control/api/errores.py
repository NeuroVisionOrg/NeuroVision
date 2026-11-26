"""Errores HTTP v2: solo codigos y mensajes publicos controlados."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from capa_2_control.api.dto_entrada import (
    PreviewRequest,
    RequestDTO,
    SegmentRequest2D,
    SegmentRequest3D,
)
from capa_2_control.api.limites import parsear_preview_acotada, parsear_segmentacion_acotada
from capa_2_control.recursos import ResourceCode, ResourceLimitError, ResourceLimits


class DiagnosticMessage(RequestDTO):
    stage: str
    code: str
    message: str
    request_id: UUID | None


class ErrorDTO(RequestDTO):
    contract_version: Literal["2"] = "2"
    error: DiagnosticMessage


@dataclass(frozen=True, slots=True)
class PublicError:
    status: int
    code: str
    stage: str
    message: str

    def response(self, request_id: UUID | None = None) -> JSONResponse:
        dto = ErrorDTO(
            error=DiagnosticMessage(
                stage=self.stage, code=self.code, message=self.message, request_id=request_id
            )
        )
        return JSONResponse(
            status_code=self.status,
            content=dto.model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )


MALFORMED = PublicError(400, "MALFORMED_REQUEST", "request", "Solicitud no valida.")
UNSUPPORTED_VERSION = PublicError(
    400, "UNSUPPORTED_CONTRACT_VERSION", "request", "Version de contrato no soportada."
)
INTERNAL = PublicError(500, "INTERNAL_ERROR", "control", "Error interno de procesamiento.")

_RESOURCES = {
    ResourceCode.FILE_TOO_LARGE: PublicError(
        413, "FILE_TOO_LARGE", "request", "El archivo supera el limite permitido."
    ),
    ResourceCode.DECOMPRESSED_LIMIT: PublicError(
        413, "DECOMPRESSED_LIMIT", "input", "Los datos exceden el limite de admision."
    ),
    ResourceCode.ROI_LIMIT: PublicError(
        413, "ROI_LIMIT", "selection", "La seleccion supera el limite permitido."
    ),
    ResourceCode.PAYLOAD_LIMIT: PublicError(
        413, "PAYLOAD_LIMIT", "request", "Se excedio el presupuesto de bytes."
    ),
    ResourceCode.INVALID_SOLVER_CONFIG: PublicError(
        422, "INVALID_SOLVER_CONFIG", "solver", "Configuracion SOR fuera de la politica."
    ),
    ResourceCode.RESOURCE_BUSY: PublicError(
        503, "RESOURCE_BUSY", "control", "Capacidad ocupada. Intente nuevamente."
    ),
}

_FIELDS = {
    "model": PublicError(422, "INVALID_MODEL_CONFIG", "model", "Parametros de modelo invalidos."),
    "solver": PublicError(422, "INVALID_SOLVER_CONFIG", "solver", "Parametros SOR invalidos."),
    "roi": PublicError(422, "INVALID_ROI", "selection", "Region de interes no valida."),
}

_HTTP_ERRORS = {
    400: MALFORMED,
    413: _RESOURCES[ResourceCode.PAYLOAD_LIMIT],
    415: PublicError(415, "UNSUPPORTED_FORMAT", "input", "Formato no soportado."),
    503: _RESOURCES[ResourceCode.RESOURCE_BUSY],
    500: INTERNAL,
}


class RequestContractError(ValueError):
    """Error detectado exclusivamente al validar una solicitud del cliente."""

    def __init__(self, public: PublicError, request_id: UUID | None = None) -> None:
        super().__init__(public.message)
        self.public = public
        self.request_id = request_id


def error_recursos(error: ResourceLimitError) -> PublicError:
    return _RESOURCES[error.code]


def error_validacion(error: ValidationError) -> PublicError:
    """Usa metadatos, nunca valores, mensajes originales ni contexto del cliente."""
    details = error.errors(include_input=False, include_context=False, include_url=False)
    if any(
        d["loc"][-1:] == ("contract_version",) and d["type"] == "literal_error" for d in details
    ):
        return UNSUPPORTED_VERSION
    if any(d["type"] in {"extra_forbidden", "json_invalid", "union_tag_invalid"} for d in details):
        return MALFORMED
    for detail in details:
        location = detail["loc"]
        if location and location[0] in ("2d", "3d"):
            location = location[1:]
        field = location[0] if location else None
        if isinstance(field, str) and field in _FIELDS:
            return _FIELDS[field]
    # Las validaciones de composicion de raiz aun no tienen codigos tipados.
    return MALFORMED


def parsear_preview_http(content: bytes, limits: ResourceLimits) -> PreviewRequest:
    try:
        return parsear_preview_acotada(content, limits)
    except ValidationError as error:
        raise RequestContractError(error_validacion(error)) from None


def parsear_segmentacion_http(
    content: bytes, limits: ResourceLimits
) -> SegmentRequest2D | SegmentRequest3D:
    try:
        return parsear_segmentacion_acotada(content, limits)
    except ValidationError as error:
        raise RequestContractError(error_validacion(error)) from None


async def _error_http(_request: Request, error: Exception) -> JSONResponse:
    """No serializa detail, body, errores originales ni encabezados arbitrarios."""
    if isinstance(error, RequestValidationError):
        return MALFORMED.response()
    if isinstance(error, HTTPException):
        public = _HTTP_ERRORS.get(error.status_code)
        if public is not None:
            return public.response()
        response = PublicError(
            error.status_code, "HTTP_ERROR", "request", "Operacion HTTP no disponible."
        ).response()
        if (
            error.status_code == HTTPStatus.METHOD_NOT_ALLOWED
            and error.headers
            and "Allow" in error.headers
        ):
            response.headers["Allow"] = error.headers["Allow"]
        return response
    return INTERNAL.response()


def registrar_errores(app: FastAPI) -> None:
    """Los errores Pydantic internos no se confunden con entradas invalidas."""
    app.add_exception_handler(RequestValidationError, _error_http)
    app.add_exception_handler(HTTPException, _error_http)
