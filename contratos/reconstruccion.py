"""Contratos de preparación y correspondencia entre ROI y sistema lineal."""

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite, prod
from re import fullmatch
from struct import pack

import numpy as np
from numpy.typing import NDArray

from contratos.geometria import InputGeometry, InputMode
from contratos.imagen import ImageData, ROISelection
from contratos.sistema import LinearSystem
from contratos.volumen import ROI3DSelection, VolumeData

type ROI = ROISelection | ROI3DSelection


def forma_roi(geometry: InputGeometry, roi: ROI) -> tuple[int, ...]:
    """Valida modo y límites; devuelve la forma local en orden de arreglo."""
    maximum: tuple[int, ...]
    shape: tuple[int, ...]
    if isinstance(roi, ROISelection) and geometry.mode == InputMode.TWO_D:
        maximum = (roi.y_max, roi.x_max)
        shape = (roi.height, roi.width)
    elif isinstance(roi, ROI3DSelection) and geometry.mode == InputMode.THREE_D:
        maximum = roi.maximum
        shape = roi.shape
    else:
        raise ValueError("ROI incompatible con el modo de la geometría")
    if any(hi > size for hi, size in zip(maximum, geometry.work_shape, strict=True)):
        raise ValueError("la ROI excede el dominio de trabajo")
    return shape


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Modelo binario; conectividad 4/6 derivada del modo, no del usuario."""

    beta: float
    threshold: float = 0.5
    boundary_policy: str = "roi_only_v1"
    weight_policy: str = "intensity_exponential_v1"

    def __post_init__(self) -> None:
        if isinstance(self.beta, bool) or not isfinite(self.beta) or self.beta < 0:
            raise ValueError("beta debe ser finito y no negativo")
        if isinstance(self.threshold, bool) or not isfinite(self.threshold):
            raise ValueError("threshold debe ser finito")
        if not 0 < self.threshold < 1:
            raise ValueError("threshold debe estar estrictamente entre 0 y 1")
        if self.boundary_policy != "roi_only_v1":
            raise ValueError("política de frontera no admitida")
        if self.weight_policy != "intensity_exponential_v1":
            raise ValueError("política de pesos no admitida")


@dataclass(frozen=True, slots=True)
class NormalizationRecord:
    """Metadatos de min-max global de ROI, no de la vista de pantalla."""

    minimum: float
    maximum: float
    policy: str = "roi_minmax_v1"

    def __post_init__(self) -> None:
        if not isfinite(self.minimum) or not isfinite(self.maximum):
            raise ValueError("extremos de normalización no finitos")
        if self.minimum > self.maximum or not isfinite(self.maximum - self.minimum):
            raise ValueError("rango de normalización inválido")
        if self.policy != "roi_minmax_v1":
            raise ValueError("política de normalización no admitida")

    @property
    def constant_intensity(self) -> bool:
        return self.minimum == self.maximum


def _validar_indices(indices: NDArray[np.int64], size: int) -> None:
    if indices.dtype != np.dtype("int64") or indices.ndim != 1 or indices.size == 0:
        raise ValueError("índices deben ser un vector int64 no vacío")
    if indices[0] < 0 or indices[-1] >= size or np.any(indices[1:] <= indices[:-1]):
        raise ValueError("índices fuera de rango, duplicados o no ordenados")


def _validar_semillas(indices: NDArray[np.int64], values: NDArray[np.uint8], size: int) -> None:
    _validar_indices(indices, size)
    if values.dtype != np.dtype("uint8") or values.shape != indices.shape:
        raise ValueError("valores de semillas deben ser uint8 y corresponder a índices")
    if set(np.unique(values).tolist()) != {0, 1}:
        raise ValueError("se requieren semillas binarias de ambas clases")
    if indices.size >= size:
        raise ValueError("la ROI debe contener al menos una incógnita")


@dataclass(frozen=True, slots=True, eq=False)
class PreparedROI:
    geometry: InputGeometry
    roi: ROI
    normalized: ImageData | VolumeData
    normalization_record: NormalizationRecord
    seed_flat_indices: NDArray[np.int64]
    seed_values: NDArray[np.uint8]

    def __post_init__(self) -> None:
        shape = forma_roi(self.geometry, self.roi)
        if isinstance(self.normalized, ImageData) and isinstance(self.roi, ROISelection):
            values = self.normalized.pixels
        elif isinstance(self.normalized, VolumeData) and isinstance(self.roi, ROI3DSelection):
            if self.normalized.geometry is not self.geometry:
                raise ValueError("se requiere la misma geometría de trabajo")
            if self.normalized.roi_origin != self.roi.origin:
                raise ValueError("origen de volumen preparado incompatible con ROI")
            values = self.normalized.voxels
        else:
            raise ValueError("datos preparados incompatibles con el modo")
        if values.shape != shape or self.normalized.source_format != self.geometry.source_format:
            raise ValueError("forma o formato de datos preparados incompatible")
        if self.normalization_record.constant_intensity and np.any(values != 0):
            raise ValueError("una ROI de intensidad constante debe normalizarse a cero")
        _validar_semillas(self.seed_flat_indices, self.seed_values, prod(shape))
        indices = self.seed_flat_indices.copy()
        seeds = self.seed_values.copy()
        indices.setflags(write=False)
        seeds.setflags(write=False)
        object.__setattr__(self, "seed_flat_indices", indices)
        object.__setattr__(self, "seed_values", seeds)


@dataclass(frozen=True, slots=True, eq=False)
class ReconstructionContext:
    """Índices locales orden C; fila r corresponde a unknown_flat_indices[r]."""

    geometry: InputGeometry
    roi: ROI
    shape: tuple[int, ...]
    seed_flat_indices: NDArray[np.int64]
    seed_values: NDArray[np.uint8]
    unknown_flat_indices: NDArray[np.int64]
    normalization_record: NormalizationRecord
    model_config: ModelConfig

    def __post_init__(self) -> None:
        if self.shape != forma_roi(self.geometry, self.roi):
            raise ValueError("forma del contexto incompatible con ROI")
        size = prod(self.shape)
        _validar_semillas(self.seed_flat_indices, self.seed_values, size)
        _validar_indices(self.unknown_flat_indices, size)
        if self.seed_flat_indices.size + self.unknown_flat_indices.size != size:
            raise ValueError("la partición no cubre toda la ROI")
        if np.intersect1d(self.seed_flat_indices, self.unknown_flat_indices).size:
            raise ValueError("semillas e incógnitas deben ser disjuntas")
        for name in ("seed_flat_indices", "seed_values", "unknown_flat_indices"):
            array = getattr(self, name).copy()
            array.setflags(write=False)
            object.__setattr__(self, name, array)


def calcular_digest_sistema(system: LinearSystem) -> str:
    """SHA-256 v1: etiquetas fijas, longitudes uint64 LE y datos C little-endian.

    Identifica A,b y su orden; no autentica el resultado de una ejecución.
    """
    digest = sha256(b"neurovision-csr-v1\x00")
    digest.update(b"n\x00" + pack("<Q", system.n))
    blocks = (
        (b"indptr\x00", system.A.indptr.astype("<i8", copy=False)),
        (b"indices\x00", system.A.indices.astype("<i8", copy=False)),
        (b"data\x00", system.A.data.astype("<f8", copy=False)),
        (b"b\x00", system.b.astype("<f8", copy=False)),
    )
    for label, array in blocks:
        payload = array.tobytes(order="C")
        digest.update(label)
        digest.update(pack("<Q", len(payload)))
        digest.update(payload)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True, eq=False)
class SystemBuildResult:
    """Sistema y contexto de Traducción; digest estructural, no autenticación.

    Se copian A y b para que el constructor no pueda alterar el candidato por
    alias. Los consumidores no deben modificar ni reasignar atributos de CSR.
    Se verifica el digest canónico sobre la copia que reciben las capas.
    """

    system: LinearSystem
    context: ReconstructionContext
    system_digest: str

    def __post_init__(self) -> None:
        if self.system.n != self.context.unknown_flat_indices.size:
            raise ValueError("n debe coincidir con el número de incógnitas")
        if fullmatch(r"[0-9a-f]{64}", self.system_digest) is None:
            raise ValueError("system_digest debe ser SHA-256 hexadecimal minúsculo")
        system = LinearSystem(A=self.system.A.copy(), b=self.system.b.copy())
        if calcular_digest_sistema(system) != self.system_digest:
            raise ValueError("system_digest no coincide con A y b")
        system.A.data.setflags(write=False)
        system.A.indices.setflags(write=False)
        system.A.indptr.setflags(write=False)
        system.b.setflags(write=False)
        object.__setattr__(self, "system", system)
