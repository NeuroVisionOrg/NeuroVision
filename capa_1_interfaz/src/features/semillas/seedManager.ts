import { toImagePixel, type Point, type ViewportTransform } from '../../shared/geometry/coordinates'
import type { Roi3D, Seed3D, SeedLabel, SelectionPayload } from '../../shared/types/contracts'

export function stagePointToSeed3D(
  stagePoint: Point,
  viewport: ViewportTransform,
  z: number,
  label: SeedLabel,
  nx: number,
  ny: number,
): Seed3D {
  const pixel = toImagePixel(stagePoint, viewport)
  return {
    x: Math.max(0, Math.min(nx - 1, pixel.x)),
    y: Math.max(0, Math.min(ny - 1, pixel.y)),
    z,
    label,
  }
}

export function upsertSeed3D(seeds: readonly Seed3D[], candidate: Seed3D): Seed3D[] {
  const next = seeds.map((s) => ({ ...s }))
  const idx = next.findIndex(
    (s) => s.x === candidate.x && s.y === candidate.y && s.z === candidate.z,
  )
  if (idx >= 0) {
    next[idx] = { ...candidate }
  } else {
    next.push({ ...candidate })
  }
  return next
}

export function countSeedsByClass(seeds: readonly Seed3D[]): {
  foreground: number
  background: number
} {
  let foreground = 0
  let background = 0
  for (const s of seeds) {
    if (s.label === 'foreground') {
      foreground++
    } else {
      background++
    }
  }
  return { foreground, background }
}

export function toSliceSelectionPayload(
  seeds: readonly Seed3D[],
  roi: Roi3D,
  sliceZ: number,
  width: number,
  height: number,
): SelectionPayload {
  return {
    contract_version: '1',
    image_width: width,
    image_height: height,
    roi: {
      x_min: roi.xMin,
      y_min: roi.yMin,
      x_max: roi.xMax + 1,
      y_max: roi.yMax + 1,
    },
    seeds: seeds.filter((s) => s.z === sliceZ).map((s) => ({ x: s.x, y: s.y, label: s.label })),
  }
}
