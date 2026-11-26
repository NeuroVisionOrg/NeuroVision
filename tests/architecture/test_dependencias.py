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

    bibliotecas_3d = {
        "nibabel": "capa_3_traduccion",
        "skimage": "capa_5_servicios",
    }

    if destino == "capa_1_interfaz":
        return True

    if destino in bibliotecas_3d:
        return origen != bibliotecas_3d[destino]

    if origen == "contratos":
        return destino in CAPAS or destino in {"fastapi", "starlette"}

    if origen in ESPECIALIZADAS:
        return (destino in CAPAS and destino != origen) or (
            origen == "capa_4_metodos" and destino in {"fastapi", "starlette", "PIL", "matplotlib"}
        )

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
        ("capa_4_metodos", "nibabel"),
        ("capa_4_metodos", "skimage.measure"),
        ("capa_4_metodos", "matplotlib.pyplot"),
        ("contratos", "nibabel"),
        ("contratos", "skimage"),
        ("capa_2_control", "nibabel"),
        ("capa_2_control", "skimage.measure"),
        ("capa_3_traduccion", "skimage.measure"),
        ("capa_5_servicios", "nibabel"),
    ],
)
def test_regla_detecta_importacion_intencionalmente_prohibida(origen: str, importado: str) -> None:
    assert es_prohibida(origen, importado)


@pytest.mark.parametrize(
    "origen,importado",
    [
        ("capa_3_traduccion", "nibabel"),
        ("capa_5_servicios", "skimage.measure"),
        ("capa_4_metodos", "numpy"),
        ("capa_4_metodos", "scipy.sparse"),
        ("capa_4_metodos", "contratos.solver"),
        ("capa_2_control", "capa_3_traduccion.api_publica"),
        ("capa_2_control", "capa_5_servicios.api_publica"),
    ],
)
def test_regla_conserva_importacion_permitida(origen: str, importado: str) -> None:
    assert not es_prohibida(origen, importado)
