import { toImagePixel, type Point, type ViewportTransform } from '../../shared/geometry/coordinates'
import type { Roi3D, ROISelection } from '../../shared/types/contracts'

export function clampRoi3D(roi: Roi3D, nx: number, ny: number, nz: number): Roi3D {
  const xMin = Math.max(0, Math.min(nx - 2, Math.floor(roi.xMin)))
  const yMin = Math.max(0, Math.min(ny - 2, Math.floor(roi.yMin)))
  const zMin = Math.max(0, Math.min(nz - 2, Math.floor(roi.zMin)))
  const xMax = Math.max(xMin + 1, Math.min(nx - 1, Math.floor(roi.xMax)))
  const yMax = Math.max(yMin + 1, Math.min(ny - 1, Math.floor(roi.yMax)))
  const zMax = Math.max(zMin + 1, Math.min(nz - 1, Math.floor(roi.zMax)))
  return { xMin, xMax, yMin, yMax, zMin, zMax }
}

export function createRoiFromDrag(
  startStage: Point,
  endStage: Point,
  viewport: ViewportTransform,
  currentRoi: Roi3D,
  nx: number,
  ny: number,
  nz: number,
): Roi3D {
  const p1 = toImagePixel(startStage, viewport)
  const p2 = toImagePixel(endStage, viewport)
  return clampRoi3D(
    {
      ...currentRoi,
      xMin: Math.min(p1.x, p2.x),
      xMax: Math.max(p1.x, p2.x),
      yMin: Math.min(p1.y, p2.y),
      yMax: Math.max(p1.y, p2.y),
    },
    nx,
    ny,
    nz,
  )
}

export function toSliceRoiSelection(roi: Roi3D): ROISelection {
  return {
    x_min: roi.xMin,
    y_min: roi.yMin,
    x_max: roi.xMax + 1,
    y_max: roi.yMax + 1,
  }
}
