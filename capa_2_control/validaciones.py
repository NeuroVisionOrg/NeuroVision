"""Validaciones de composición que dependen de varios contratos."""

from contratos.geometria import InputGeometry, InputMode
from contratos.imagen import ROISelection, SeedSelection
from contratos.volumen import ROI3DSelection, Seed3DSelection


def validar_seleccion(
    image_width: int,
    image_height: int,
    roi: ROISelection,
    semillas: SeedSelection,
) -> None:
    """Valida dimensiones y semillas sin decodificar ni procesar imágenes."""
    if roi.x_max > image_width or roi.y_max > image_height:
        raise ValueError("la ROI excede las dimensiones de la imagen")
    for semilla in semillas.seeds:
        if not (roi.x_min <= semilla.x < roi.x_max and roi.y_min <= semilla.y < roi.y_max):
            raise ValueError("una semilla está fuera de la ROI")
    if len(semillas.seeds) >= roi.area:
        raise ValueError("no quedan píxeles desconocidos")


def validar_seleccion_3d(
    geometry: InputGeometry,
    roi: ROI3DSelection,
    semillas: Seed3DSelection,
) -> None:
    """Valida la selección contra la cuadrícula completa de trabajo."""
    if geometry.mode != InputMode.THREE_D:
        raise ValueError("se requiere geometría 3D")
    if any(hi > size for hi, size in zip(roi.maximum, geometry.work_shape, strict=True)):
        raise ValueError("la ROI excede las dimensiones del volumen")
    if any(not roi.contains(seed.position) for seed in semillas.seeds):
        raise ValueError("una semilla está fuera de la ROI")
    if len(semillas.seeds) >= roi.volume:
        raise ValueError("no quedan vóxeles desconocidos")
