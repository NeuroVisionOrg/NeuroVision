"""Pruebas de los contratos de reconstrucción, no del algoritmo segmentador."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.sparse import csr_array

from contratos.geometria import InputGeometry, InputMode, SpatialGeometry
from contratos.imagen import ImageData, ROISelection
from contratos.reconstruccion import (
    ModelConfig,
    NormalizationRecord,
    PreparedROI,
    ReconstructionContext,
    SystemBuildResult,
    calcular_digest_sistema,
)
from contratos.resultados import SolverResult, SolverStatus
from contratos.segmentacion import (
    SegmentationResult,
    VolumeSegmentationResult,
    validar_reconstruccion,
)
from contratos.sistema import LinearSystem
from contratos.solver import SolverMethod
from contratos.volumen import ROI3DSelection, VolumeData


def contexto_2d() -> ReconstructionContext:
    return ReconstructionContext(
        geometry=InputGeometry(InputMode.TWO_D, (5, 6), (5, 6), "PNG"),
        roi=ROISelection(1, 2, 3, 4),
        shape=(2, 2),
        seed_flat_indices=np.array([0, 1], dtype=np.int64),
        seed_values=np.array([0, 1], dtype=np.uint8),
        unknown_flat_indices=np.array([2, 3], dtype=np.int64),
        normalization_record=NormalizationRecord(0.0, 255.0),
        model_config=ModelConfig(beta=1.0),
    )


def contexto_3d() -> ReconstructionContext:
    spatial = SpatialGeometry(
        h_original=np.eye(4, dtype=np.float64),
        h_work=np.eye(4, dtype=np.float64),
        t_work_to_original=np.eye(4, dtype=np.int64),
        spacing_mm=(1.0, 1.0, 1.0),
        axis_codes=("R", "A", "S"),
        affine_source="synthetic",
        atol_mm=1e-8,
    )
    return ReconstructionContext(
        geometry=InputGeometry(InputMode.THREE_D, (4, 5, 6), (4, 5, 6), "NIFTI", spatial),
        roi=ROI3DSelection(1, 2, 3, 3, 4, 5),
        shape=(2, 2, 2),
        seed_flat_indices=np.array([0, 7], dtype=np.int64),
        seed_values=np.array([0, 1], dtype=np.uint8),
        unknown_flat_indices=np.arange(1, 7, dtype=np.int64),
        normalization_record=NormalizationRecord(0.0, 1000.0),
        model_config=ModelConfig(beta=1.0),
    )


def diagnostico(solution: np.ndarray) -> SolverResult:
    return SolverResult(
        method=SolverMethod.SOR,
        status=SolverStatus.CONVERGED,
        solution=solution,
        iterations=1,
        sweeps=1,
        initial_residual=1.0,
        final_residual=1e-8,
        residual_history=(1.0, 1e-8),
        elapsed_seconds=0.01,
        omega_used=1.2,
        rtol=1e-6,
        atol=1e-10,
        max_iterations=2000,
        stopping_threshold=1e-6,
        initialization="zero",
    )


def salida_2d(context: ReconstructionContext) -> SegmentationResult:
    assert isinstance(context.roi, ROISelection)
    return SegmentationResult(
        geometry=context.geometry,
        roi=context.roi,
        threshold=0.5,
        probability_map=np.array([[0.0, 1.0], [1 / 3, 2 / 3]], dtype=np.float64),
        mask=np.array([[False, True], [False, True]]),
        boundary_mask=np.array([[False, True], [False, True]]),
        solver_result=diagnostico(np.array([1 / 3, 2 / 3], dtype=np.float64)),
        touches_boundary=True,
    )


@pytest.mark.parametrize("beta", [-1.0, float("nan"), float("inf"), True])
def test_beta_invalido(beta: float) -> None:
    with pytest.raises(ValueError, match="beta"):
        ModelConfig(beta=beta)


@pytest.mark.parametrize("threshold", [0.0, 1.0, -0.1, float("nan"), True])
def test_threshold_invalido(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        ModelConfig(beta=0, threshold=threshold)


def test_politicas_versionadas() -> None:
    assert ModelConfig(0).threshold == 0.5
    with pytest.raises(ValueError, match="frontera"):
        ModelConfig(0, boundary_policy="outside_background")
    with pytest.raises(ValueError, match="pesos"):
        ModelConfig(0, weight_policy="unknown")


@pytest.mark.parametrize("minimum,maximum", [(2.0, 1.0), (0.0, float("inf")), (-1e308, 1e308)])
def test_normalizacion_invalida(minimum: float, maximum: float) -> None:
    with pytest.raises(ValueError, match="normalización"):
        NormalizationRecord(minimum, maximum)


def test_contexto_2d_y_3d() -> None:
    assert contexto_2d().shape == (2, 2)
    assert contexto_3d().shape == (2, 2, 2)


@pytest.mark.parametrize(
    "changes",
    [
        {"shape": (4, 1)},
        {"roi": ROISelection(5, 4, 7, 6)},
        {"seed_flat_indices": np.array([1, 0], dtype=np.int64)},
        {"seed_flat_indices": np.array([0, 0], dtype=np.int64)},
        {"seed_flat_indices": np.array([0, 1], dtype=np.int32)},
        {"seed_values": np.array([1, 1], dtype=np.uint8)},
        {"seed_values": np.array([0, 2], dtype=np.uint8)},
        {"unknown_flat_indices": np.array([1, 2], dtype=np.int64)},
        {"unknown_flat_indices": np.array([2, 4], dtype=np.int64)},
        {"unknown_flat_indices": np.array([2], dtype=np.int64)},
    ],
)
def test_contexto_rechaza_particion_invalida(changes: dict) -> None:
    with pytest.raises(ValueError):
        replace(contexto_2d(), **changes)


def test_contexto_no_conserva_alias_de_indices() -> None:
    indices = np.array([0, 1], dtype=np.int64)
    context = replace(contexto_2d(), seed_flat_indices=indices)
    indices[1] = 2
    np.testing.assert_array_equal(context.seed_flat_indices, [0, 1])
    assert not context.seed_flat_indices.flags.writeable


def test_preparacion_2d_constante() -> None:
    context = contexto_2d()
    record = NormalizationRecord(5, 5)
    prepared = PreparedROI(
        context.geometry,
        context.roi,
        ImageData(np.zeros((2, 2), dtype=np.float32), "PNG", "roi_minmax_v1"),
        record,
        context.seed_flat_indices,
        context.seed_values,
    )
    assert prepared.normalization_record.constant_intensity
    with pytest.raises(ValueError, match="constante"):
        replace(
            prepared,
            normalized=ImageData(np.ones((2, 2), dtype=np.float32), "PNG", "roi_minmax_v1"),
        )


def test_preparacion_3d_exige_origen() -> None:
    context = contexto_3d()
    assert isinstance(context.roi, ROI3DSelection)
    volume = VolumeData(
        np.zeros((2, 2, 2), dtype=np.float32),
        "NIFTI",
        "roi_minmax_v1",
        context.geometry,
        context.roi.origin,
    )
    prepared = PreparedROI(
        context.geometry,
        context.roi,
        volume,
        context.normalization_record,
        context.seed_flat_indices,
        context.seed_values,
    )
    with pytest.raises(ValueError, match="origen"):
        replace(prepared, normalized=replace(volume, roi_origin=(0, 0, 0)))


def test_sistema_con_contexto_no_conserva_alias() -> None:
    system = LinearSystem(csr_array(np.eye(2)), np.ones(2))
    result = SystemBuildResult(system, contexto_2d(), calcular_digest_sistema(system))
    system.b[0] = 9
    system.A.data[0] = 9
    assert result.system.b[0] == 1
    assert result.system.A.data[0] == 1
    assert not result.system.b.flags.writeable
    assert not result.system.A.data.flags.writeable
    with pytest.raises(ValueError, match="incógnitas"):
        replace(result, context=contexto_3d())
    with pytest.raises(ValueError, match="system_digest"):
        replace(result, system_digest="not-a-digest")
    with pytest.raises(ValueError, match="system_digest"):
        replace(result, system_digest="a" * 64)


def test_digest_canonico_es_reproducible_y_sensible_a_datos() -> None:
    system = LinearSystem(csr_array(np.array([[2.0, -1.0], [-1.0, 2.0]])), np.array([0.0, 1.0]))
    same = LinearSystem(system.A.copy(), system.b.copy())
    digest = calcular_digest_sistema(system)
    # SHA-256 de referencia de un sistema sintetico; no es una credencial.
    # pragma: allowlist nextline secret
    assert digest == "6a509a5fd459063db58f8fb12c8984470642602ce74f2edd226ecaa917535150"
    assert digest == calcular_digest_sistema(same)
    same.b[0] = 1.0
    assert digest != calcular_digest_sistema(same)


def test_reconstruccion_2d_y_correspondencia() -> None:
    context = contexto_2d()
    result = salida_2d(context)
    validar_reconstruccion(context, result, 1e-12)
    assert result.mask.shape == context.shape
    assert result.roi.x_min == 1
    assert result.roi.y_min == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"probability_map": np.zeros((2, 2), dtype=np.float32)},
        {"probability_map": np.array([[0, 1], [0, np.nan]])},
        {"probability_map": np.array([[0, 1], [0, 1.01]])},
        {"mask": np.ones((2, 2), dtype=np.uint8)},
        {"mask": np.zeros((2, 2), dtype=np.bool_)},
        {"boundary_mask": np.ones((2, 2), dtype=np.bool_)},
        {"touches_boundary": False},
        {"threshold": 1.0},
    ],
)
def test_salida_rechaza_datos_incoherentes(changes: dict) -> None:
    with pytest.raises(ValueError):
        replace(salida_2d(contexto_2d()), **changes)


def test_reconstruccion_no_convergente() -> None:
    result = salida_2d(contexto_2d())
    failure = replace(
        result.solver_result,
        status=SolverStatus.MAX_ITERATIONS,
        solution=None,
        max_iterations=1,
        final_residual=0.5,
        residual_history=(1.0, 0.5),
    )
    with pytest.raises(ValueError, match="CONVERGED"):
        replace(result, solver_result=failure)


def test_reconstruccion_rechaza_correspondencia_incorrecta() -> None:
    context = contexto_2d()
    result = salida_2d(context)
    with pytest.raises(ValueError, match="semillas"):
        validar_reconstruccion(
            replace(context, seed_values=np.array([1, 0], dtype=np.uint8)), result, 0.0
        )
    incorrect = replace(result, solver_result=diagnostico(np.array([0.1, 0.9])))
    with pytest.raises(ValueError, match="filas"):
        validar_reconstruccion(context, incorrect, 1e-12)
    incorrect = replace(result, solver_result=diagnostico(np.array([0.1])))
    with pytest.raises(ValueError, match="incógnita"):
        validar_reconstruccion(context, incorrect, 1e-12)


def test_reconstruccion_3d_preserva_orden_c() -> None:
    context = contexto_3d()
    assert isinstance(context.roi, ROI3DSelection)
    values = np.linspace(0, 1, 8, dtype=np.float64).reshape(context.shape)
    result = VolumeSegmentationResult(
        geometry=context.geometry,
        roi=context.roi,
        threshold=0.5,
        probability_map=values,
        mask=values >= 0.5,
        solver_result=diagnostico(values.ravel()[1:7].copy()),
        touches_boundary=True,
    )
    validar_reconstruccion(context, result, 1e-12)
    assert result.probability_map[1, 0, 0] == pytest.approx(4 / 7)
    assert result.roi.origin == (1, 2, 3)
