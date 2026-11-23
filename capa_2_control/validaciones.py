"""Validaciones de composición que dependen de varios contratos."""

from contratos.imagen import ROISelection, SeedSelection


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
