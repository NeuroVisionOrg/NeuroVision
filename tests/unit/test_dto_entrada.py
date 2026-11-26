"""CT-01/02/03: estructura y seleccion declarada, no admision de archivos."""

import json
from uuid import UUID

import pytest
from pydantic import ValidationError

from capa_2_control.api.dto_entrada import (
    PreviewRequest,
    SegmentRequest2D,
    SegmentRequest3D,
    parsear_segment_request,
)
from contratos.imagen import SeedLabel
from contratos.solver import SolverMethod


def solicitud_2d() -> dict[str, object]:
    return {
        "contract_version": "2",
        "request_id": str(UUID(int=1, version=4)),
        "mode": "2d",
        "input_id": "0" * 64,
        "preparation_version": "1",
        "work_shape": [4, 6],
        "roi": {"x_min": 1, "y_min": 1, "x_max": 5, "y_max": 4},
        "seeds": [
            {"x": 1, "y": 1, "label": "background"},
            {"x": 4, "y": 3, "label": "foreground"},
        ],
        "model": {"beta": 0, "threshold": 0.5},
        "solver": {"omega": 1.2, "rtol": 1e-6, "atol": 1e-10, "max_iterations": 2000},
    }


def solicitud_3d() -> dict[str, object]:
    return solicitud_2d() | {
        "mode": "3d",
        "work_shape": [4, 5, 6],
        "roi": {"i_min": 1, "j_min": 2, "k_min": 3, "i_max": 4, "j_max": 5, "k_max": 6},
        "seeds": [
            {"i": 1, "j": 2, "k": 3, "label": "background"},
            {"i": 3, "j": 4, "k": 5, "label": "foreground"},
        ],
    }


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_preview_valido(mode: str) -> None:
    dto = PreviewRequest.model_validate_json(json.dumps({"contract_version": "2", "mode": mode}))
    assert dto.model_dump(mode="json") == {"contract_version": "2", "mode": mode}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"contract_version": "1", "mode": "2d"},
        {"contract_version": 2, "mode": "2d"},
        {"contract_version": "2", "mode": "4d"},
        {"contract_version": "2", "mode": "2d", "filename": "fixture.png"},
    ],
)
def test_preview_rechaza_contrato_invalido(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PreviewRequest.model_validate_json(json.dumps(payload))


def test_segmentacion_2d_convierte_a_contratos_internos() -> None:
    payload = solicitud_2d()
    dto = parsear_segment_request(json.dumps(payload))
    assert isinstance(dto, SegmentRequest2D)
    assert dto.model_dump(mode="json") == payload
    roi, seeds = dto.seleccion()
    assert (roi.height, roi.width) == (3, 4)
    assert seeds.seeds[1].label == SeedLabel.FOREGROUND
    assert dto.model.a_dominio().beta == 0
    config = dto.solver.a_dominio()
    assert config.method == SolverMethod.SOR
    assert config.x0 is None
    assert config.omega == 1.2


def test_segmentacion_3d_conserva_orden_y_coordenadas() -> None:
    payload = solicitud_3d()
    dto = parsear_segment_request(json.dumps(payload))
    assert isinstance(dto, SegmentRequest3D)
    assert dto.model_dump(mode="json") == payload
    roi, seeds = dto.seleccion()
    assert roi.origin == (1, 2, 3)
    assert roi.maximum == (4, 5, 6)
    assert seeds.seeds[1].position == (3, 4, 5)


@pytest.mark.parametrize(
    "changes",
    [
        {"contract_version": "1"},
        {"contract_version": 2},
        {"mode": "3d"},
        {"mode": "4d"},
        {"request_id": "no-uuid"},
        {"input_id": "A" * 64},
        {"input_id": "0" * 63},
        {"preparation_version": "  "},
        {"work_shape": [4, 6, 1]},
        {"work_shape": [4, 0]},
        {"work_shape": [True, 6]},
        {"work_shape": [4.0, 6]},
        {"work_shape": ["4", 6]},
        {"work_shape": [2, 6]},
        {"image_width": 6},
        {"roi": None},
        {"seeds": []},
        {"seeds": [{"x": 1, "y": 1, "label": "background"}]},
    ],
)
def test_rechaza_campos_invalidos_2d(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(solicitud_2d() | changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"work_shape": [4, 5]},
        {"work_shape": [4, 5, 5]},
        {"roi": {"x_min": 0, "y_min": 0, "x_max": 2, "y_max": 2}},
        {"seeds": solicitud_2d()["seeds"]},
        {
            "seeds": [
                {"i": 1, "j": 2, "k": 3, "label": "background"},
                {"i": 4, "j": 4, "k": 5, "label": "foreground"},
            ],
        },
    ],
)
def test_rechaza_campos_invalidos_3d(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(solicitud_3d() | changes))


@pytest.mark.parametrize(
    "field,value",
    [
        ("omega", 0),
        ("omega", 2),
        ("omega", float("nan")),
        ("omega", float("inf")),
        ("omega", True),
        ("omega", "1.2"),
        ("rtol", -1),
        ("atol", -1),
        ("max_iterations", 0),
        ("max_iterations", True),
        ("max_iterations", 2.0),
        ("method", "sor"),
        ("x0", [0]),
    ],
)
def test_rechaza_parametros_solver(field: str, value: object) -> None:
    payload = solicitud_2d()
    solver = payload["solver"]
    assert isinstance(solver, dict)
    solver[field] = value
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


def test_rechaza_tolerancias_ambas_cero() -> None:
    payload = solicitud_2d()
    solver = payload["solver"]
    assert isinstance(solver, dict)
    solver.update(rtol=0, atol=0)
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


@pytest.mark.parametrize(
    "field,value",
    [
        ("beta", -1),
        ("beta", True),
        ("beta", float("inf")),
        ("threshold", 0),
        ("threshold", 1),
        ("threshold", float("nan")),
        ("connectivity", 4),
    ],
)
def test_rechaza_parametros_modelo(field: str, value: object) -> None:
    payload = solicitud_2d()
    model = payload["model"]
    assert isinstance(model, dict)
    model[field] = value
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


@pytest.mark.parametrize("field,value", [("x_min", True), ("y_min", -1), ("x_max", 1)])
def test_rechaza_roi_invalida(field: str, value: object) -> None:
    payload = solicitud_2d()
    roi = payload["roi"]
    assert isinstance(roi, dict)
    roi[field] = value
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


@pytest.mark.parametrize(
    "seed",
    [
        {"x": 5, "y": 3, "label": "foreground"},
        {"x": 1, "y": 1, "label": "foreground"},
        {"x": True, "y": 3, "label": "foreground"},
        {"x": 4, "y": 3, "label": "background"},
        {"x": 4, "y": 3, "label": "tumor"},
        {"x": 4, "y": 3, "label": "foreground", "k": 0},
    ],
)
def test_rechaza_semilla_invalida(seed: dict[str, object]) -> None:
    payload = solicitud_2d()
    seeds = payload["seeds"]
    assert isinstance(seeds, list)
    seeds[1] = seed
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


def test_rechaza_roi_sin_incognitas() -> None:
    payload = solicitud_2d() | {
        "roi": {"x_min": 0, "y_min": 0, "x_max": 2, "y_max": 1},
        "seeds": [
            {"x": 0, "y": 0, "label": "background"},
            {"x": 1, "y": 0, "label": "foreground"},
        ],
    }
    with pytest.raises(ValidationError):
        parsear_segment_request(json.dumps(payload))


@pytest.mark.parametrize("content", ["{", "null", "[]", "{}"])
def test_rechaza_json_invalido_o_incompleto(content: str) -> None:
    with pytest.raises(ValidationError):
        parsear_segment_request(content)
