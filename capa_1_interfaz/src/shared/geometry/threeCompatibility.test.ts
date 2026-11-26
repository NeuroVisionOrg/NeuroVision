import { BufferGeometry, Float32BufferAttribute } from 'three'
import { describe, expect, it } from 'vitest'

describe('compatibilidad Three.js', () => {
  it('conserva vertices e indices y calcula normales y limites', () => {
    const geometry = new BufferGeometry()
    try {
      geometry.setAttribute(
        'position',
        new Float32BufferAttribute([28, 38, 72, 34, 38, 72, 28, 44, 72], 3),
      )
      geometry.setIndex([0, 1, 2])
      geometry.computeBoundingBox()
      geometry.computeVertexNormals()

      expect(geometry.getAttribute('position').count).toBe(3)
      expect(Array.from(geometry.getIndex()?.array ?? [])).toEqual([0, 1, 2])
      expect(geometry.boundingBox?.min.toArray()).toEqual([28, 38, 72])
      expect(geometry.boundingBox?.max.toArray()).toEqual([34, 44, 72])
      expect(Array.from(geometry.getAttribute('normal').array)).toEqual([0, 0, 1, 0, 0, 1, 0, 0, 1])
    } finally {
      geometry.dispose()
    }
  })
})
