"""Composicion de presupuestos y DTO; aun no registra rutas HTTP."""

from capa_2_control.api.dto_entrada import (
    PreviewRequest,
    SegmentRequest2D,
    SegmentRequest3D,
    parsear_segment_request,
)
from capa_2_control.api.dto_previsualizacion import a_dto_preview
from capa_2_control.recursos import ResourceLimits
from contratos.datos import PreviewData


def parsear_preview_acotada(content: bytes, limits: ResourceLimits) -> PreviewRequest:
    """Verifica bytes JSON antes de validar el modelo Pydantic."""
    limits.validar_json(len(content))
    return PreviewRequest.model_validate_json(content, strict=True)


def parsear_segmentacion_acotada(
    content: bytes, limits: ResourceLimits
) -> SegmentRequest2D | SegmentRequest3D:
    """Preflight de lo declarado; no acredita la geometria del archivo."""
    limits.validar_json(len(content))
    request = parsear_segment_request(content)
    limits.validar_forma(request.work_shape)
    if isinstance(request, SegmentRequest2D):
        elements = request.roi.a_dominio().area
    else:
        elements = request.roi.a_dominio().volume
    limits.validar_roi(elements, len(request.seeds))
    limits.validar_iteraciones(request.solver.max_iterations)
    return request


def serializar_preview_acotada(preview: PreviewData, limits: ResourceLimits) -> bytes:
    """Verifica vista cruda, cota inferior Base64 y bytes JSON finales.

    Los metadatos agregan bytes al Base64; la comprobacion exacta final no
    evita todas las asignaciones de serializacion. No se trunca la respuesta.
    """
    limits.validar_forma(preview.geometry.original_shape)
    limits.validar_forma(preview.geometry.work_shape)
    nbytes = preview.uint8_view.nbytes
    limits.validar_arreglo(nbytes)
    limits.validar_respuesta(4 * ((nbytes + 2) // 3))
    dto = a_dto_preview(preview, max_view_bytes=limits.max_array_bytes)
    response = dto.model_dump_json(by_alias=True).encode("utf-8")
    limits.validar_respuesta(len(response))
    return response
