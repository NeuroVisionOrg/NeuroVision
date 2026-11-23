import { describe, expect, it } from 'vitest'

import { toImagePixel } from './coordinates'

describe('conversión de coordenadas', () => {
  it('conserva la posición original tras aplicar zoom y desplazamiento', () => {
    const point = { x: 34 * 2 + 10, y: 25 * 2 + 20 }
    expect(toImagePixel(point, { scale: 2, offsetX: 10, offsetY: 20 })).toEqual({ x: 34, y: 25 })
  })

  it('rechaza escala cero', () => {
    expect(() => toImagePixel({ x: 10, y: 20 }, { scale: 0, offsetX: 0, offsetY: 0 })).toThrow(
      RangeError,
    )
  })
})
