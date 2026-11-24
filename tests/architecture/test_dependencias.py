"""Reglas directas entre paquetes; Import Linter complementa las transitivas."""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CAPAS = frozenset(
    {
        "capa_2_control",
        "capa_3_traduccion",
        "capa_4_metodos",
        "capa_5_servicios",
    }
)
ESPECIALIZADAS = frozenset({"capa_3_traduccion", "capa_4_metodos", "capa_5_servicios"})


def importaciones_absolutas(codigo: str) -> list[str]:
    """Nombres importados explícitamente sin analizar semántica dinámica."""
    arbol = ast.parse(codigo)
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            nombres.append(nodo.module)
    return nombres


def es_prohibida(origen: str, importado: str) -> bool:
    """Aplica la matriz de dependencias de NeuroVision."""
    destino = importado.split(".", maxsplit=1)[0]
    if destino == "capa_1_interfaz":
        return True
    if origen == "contratos":
        return destino in CAPAS or destino in {"fastapi", "starlette"}
    if origen in ESPECIALIZADAS:
        if destino in CAPAS and destino != origen:
            return True
        if origen == "capa_4_metodos" and destino in {"fastapi", "starlette", "PIL"}:
            return True
    if origen == "capa_2_control" and destino in ESPECIALIZADAS:
        partes = importado.split(".")
        return len(partes) > 1 and partes[1] != "api_publica"
    return False


@pytest.mark.parametrize("origen", sorted(CAPAS | {"contratos"}))
def test_estructura_no_contiene_dependencias_prohibidas(origen: str) -> None:
    violaciones: list[str] = []
    for ruta in sorted((RAIZ / origen).rglob("*.py")):
        for importado in importaciones_absolutas(ruta.read_text(encoding="utf-8")):
            if es_prohibida(origen, importado):
                violaciones.append(f"{ruta.relative_to(RAIZ)}: {importado}")
    assert not violaciones, "Dependencias prohibidas:\n" + "\n".join(violaciones)


@pytest.mark.parametrize(
    "origen,importado",
    [
        ("capa_4_metodos", "capa_3_traduccion.grafo"),
        ("capa_3_traduccion", "capa_5_servicios.metricas"),
        ("contratos", "capa_2_control.validaciones"),
        ("capa_2_control", "capa_3_traduccion.grafo"),
    ],
)
def test_regla_detecta_importacion_intencionalmente_prohibida(origen: str, importado: str) -> None:
    assert es_prohibida(origen, importado)
