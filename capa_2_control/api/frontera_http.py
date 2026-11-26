"""Frontera ASGI: presupuesto del cuerpo antes del parser y errores seguros."""

from collections.abc import Sequence
from logging import getLogger

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from capa_2_control.api.errores import INTERNAL, MALFORMED, RequestContractError, error_recursos
from capa_2_control.recursos import ResourceLimitError, ResourceLimits

_LOG = getLogger(__name__)


def _longitud_declarada(
    headers: Sequence[tuple[bytes, bytes]], limits: ResourceLimits
) -> int | None:
    values = [value for name, value in headers if name.lower() == b"content-length"]
    if not values:
        return None
    if len(values) != 1 or not values[0].isdigit():
        raise RequestContractError(MALFORMED)
    # Evita convertir enteros de longitud arbitraria.
    digits = values[0].lstrip(b"0") or b"0"
    if len(digits) > len(str(limits.max_request_bytes)):
        limits.validar_cuerpo(limits.max_request_bytes + 1)
    size = int(digits)
    limits.validar_cuerpo(size)
    return size


async def _recibir_acotado(
    scope: Scope, receive: Receive, limits: ResourceLimits
) -> Receive | None:
    declared = _longitud_declarada(scope["headers"], limits)
    body = bytearray()
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return None
        if message["type"] != "http.request":
            raise RequestContractError(MALFORMED)
        chunk: bytes = message.get("body", b"")
        limits.validar_cuerpo(len(body) + len(chunk))
        body.extend(chunk)
        if not message.get("more_body", False):
            break
    if declared is not None and declared != len(body):
        raise RequestContractError(MALFORMED)
    data = bytes(body)
    replayed = False

    async def replay() -> Message:
        nonlocal replayed
        if replayed:
            return await receive()
        replayed = True
        return {"type": "http.request", "body": data, "more_body": False}

    return replay


def _respuesta_error(error: ResourceLimitError | RequestContractError) -> JSONResponse:
    """Convierte errores previstos a una respuesta HTTP segura."""
    if isinstance(error, ResourceLimitError):
        return error_recursos(error).response()
    return error.public.response(error.request_id)


class HTTPBoundary:
    """La aplicacion de limites requiere configuracion explicita.

    Se almacena un cuerpo acotado antes del parser multipart. Esto puede
    requerir copias adicionales y no limita el buffer del servidor ASGI.
    No sustituye los limites de archivo, descompresion ni concurrencia.
    """

    def __init__(self, app: ASGIApp, *, limits: ResourceLimits | None) -> None:
        self.app = app
        self.limits = limits

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return
        started = False

        async def send_safe(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-store"
                started = True
            await send(message)

        try:
            if self.limits is not None and scope["method"] == "POST":
                bounded = await _recibir_acotado(scope, receive, self.limits)
                if bounded is None:
                    return
                receive = bounded
            await self.app(scope, receive, send_safe)
        except (ResourceLimitError, RequestContractError) as error:
            if started:
                raise
            response = _respuesta_error(error)
            await response(scope, receive, send_safe)
        except Exception:
            if started:
                raise
            # No registrar contenido de la solicitud, excepcion ni traceback.
            _LOG.error("INTERNAL_ERROR")
            await INTERNAL.response()(scope, receive, send_safe)
