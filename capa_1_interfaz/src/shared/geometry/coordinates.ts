/** Transformación de un punto visual a coordenadas de la imagen original. */
export interface Point {
  x: number
  y: number
}

export interface ViewportTransform {
  scale: number
  offsetX: number
  offsetY: number
}

export function toImagePixel(point: Point, viewport: ViewportTransform): Point {
  if (!Number.isFinite(viewport.scale) || viewport.scale <= 0) {
    throw new RangeError('La escala debe ser finita y positiva')
  }
  if (![point.x, point.y, viewport.offsetX, viewport.offsetY].every(Number.isFinite)) {
    throw new RangeError('Las coordenadas deben ser finitas')
  }

  return {
    x: Math.floor((point.x - viewport.offsetX) / viewport.scale),
    y: Math.floor((point.y - viewport.offsetY) / viewport.scale),
  }
}
