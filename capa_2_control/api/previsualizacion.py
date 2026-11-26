"""Ruta de previsualizacion disponible solo con operaciones reales configuradas."""

from typing import BinaryIO

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.responses import Response

from capa_2_control.api.dto_previsualizacion import PreviewDTO
from capa_2_control.api.errores import (
    MALFORMED,
    PublicError,
    RequestContractError,
    parsear_preview_http,
)
from capa_2_control.api.limites import serializar_preview_acotada
from capa_2_control.casos_uso.previsualizacion import PreviewOperations, preparar_previsualizacion
from capa_2_control.recursos import ProcessingCapacity, ResourceLimits, leer_archivo_acotado
from contratos.admision import DataReadCode, DataReadError
from contratos.geometria import InputMode

_READ_ERRORS = {
    DataReadCode.UNSUPPORTED_FORMAT: PublicError(
        415, "UNSUPPORTED_FORMAT", "input", "Formato no soportado."
    ),
    DataReadCode.INVALID_IMAGE: PublicError(
        422, "INVALID_IMAGE", "input", "Archivo de imagen no valido."
    ),
    DataReadCode.UNSUPPORTED_COLOR: PublicError(
        422, "UNSUPPORTED_COLOR", "input", "Se requiere intensidad escalar."
    ),
    DataReadCode.UNSUPPORTED_GEOMETRY: PublicError(
        422, "UNSUPPORTED_GEOMETRY", "input", "Geometria no admitida."
    ),
    DataReadCode.DECOMPRESSED_LIMIT: PublicError(
        413, "DECOMPRESSED_LIMIT", "input", "Los datos exceden el limite de admision."
    ),
}


def _procesar(
    stream: BinaryIO, request_json: str, limits: ResourceLimits, operations: PreviewOperations
) -> bytes:
    """Lectura, orquestacion y serializacion fuera del event loop."""
    dto = parsear_preview_http(request_json.encode("utf-8"), limits)
    content = leer_archivo_acotado(stream, limits)
    try:
        preview = preparar_previsualizacion(content, InputMode(dto.mode), limits, operations)
    except DataReadError as error:
        raise RequestContractError(_READ_ERRORS[error.code]) from None
    return serializar_preview_acotada(preview, limits)


def crear_router_preview(limits: ResourceLimits, operations: PreviewOperations) -> APIRouter:
    router = APIRouter(tags=["previsualizacion"])
    capacity = ProcessingCapacity(limits)

    @router.post(
        "/previsualizar",
        response_model=PreviewDTO,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["image", "request"],
                            "additionalProperties": False,
                            "properties": {
                                "image": {"type": "string", "format": "binary"},
                                "request": {
                                    "type": "string",
                                    "description": "JSON PreviewRequest v2",
                                },
                            },
                        }
                    }
                },
            }
        },
    )
    async def previsualizar(request: Request) -> Response:
        media_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
        if media_type != "multipart/form-data":
            raise RequestContractError(MALFORMED)
        with capacity.ocupar():
            async with request.form(
                max_files=1, max_fields=1, max_part_size=limits.max_request_bytes
            ) as form:
                if set(form) != {"image", "request"}:
                    raise RequestContractError(MALFORMED)
                image = form["image"]
                raw = form["request"]
                if not isinstance(image, UploadFile) or not isinstance(raw, str):
                    raise RequestContractError(MALFORMED)
                body = await run_in_threadpool(_procesar, image.file, raw, limits, operations)
        return Response(content=body, media_type="application/json")

    return router
