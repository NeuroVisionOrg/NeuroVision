import Konva from 'konva'

import { voxelIndex3D, VOLUME_NX, VOLUME_NY } from '../../shared/datasets/syntheticVolumes'
import type { Point, ViewportTransform } from '../../shared/geometry/coordinates'
import type { Roi3D, Seed3D, VolumeDataset } from '../../shared/types/contracts'

export const CANVAS_2D_SIZE = 360
const SCALE_2D = CANVAS_2D_SIZE / VOLUME_NX

export interface Slice2DCallbacks {
  onPointerDown: (stagePoint: Point) => void
  onPointerMove: (stagePoint: Point) => void
  onPointerUp: () => void
}

export class Slice2DKonvaViewer {
  private readonly stage: Konva.Stage
  private readonly baseLayer: Konva.Layer
  private readonly overlayLayer: Konva.Layer
  private readonly offscreen: HTMLCanvasElement
  private readonly offCtx: CanvasRenderingContext2D

  constructor(container: HTMLDivElement, callbacks: Slice2DCallbacks) {
    this.stage = new Konva.Stage({
      container,
      width: CANVAS_2D_SIZE,
      height: CANVAS_2D_SIZE,
    })
    this.baseLayer = new Konva.Layer()
    this.overlayLayer = new Konva.Layer()
    this.stage.add(this.baseLayer)
    this.stage.add(this.overlayLayer)

    this.offscreen = document.createElement('canvas')
    this.offscreen.width = VOLUME_NX
    this.offscreen.height = VOLUME_NY
    const ctx = this.offscreen.getContext('2d')
    if (!ctx) {
      throw new Error('No se pudo crear contexto 2D auxiliar para Konva')
    }
    this.offCtx = ctx

    this.stage.on('mousedown touchstart', () => {
      const pos = this.stage.getPointerPosition()
      if (pos) {
        callbacks.onPointerDown(pos)
      }
    })

    this.stage.on('mousemove touchmove', () => {
      const pos = this.stage.getPointerPosition()
      if (pos) {
        callbacks.onPointerMove(pos)
      }
    })

    this.stage.on('mouseup touchend', () => {
      callbacks.onPointerUp()
    })
  }

  public getViewportTransform(): ViewportTransform {
    return { scale: SCALE_2D, offsetX: 0, offsetY: 0 }
  }

  public render(
    dataset: VolumeDataset,
    sliceZ: number,
    roi: Roi3D,
    seeds: readonly Seed3D[],
    probabilities: Float64Array | null,
    maskOpacity: number,
  ): void {
    const imgData = this.offCtx.createImageData(VOLUME_NX, VOLUME_NY)

    for (let y = 0; y < VOLUME_NY; y++) {
      for (let x = 0; x < VOLUME_NX; x++) {
        const i = voxelIndex3D(x, y, sliceZ)
        const gray = Math.round((dataset.intensities[i] ?? 0) * 255)
        const prob = probabilities ? (probabilities[i] ?? 0) : 0
        const pIdx = (y * VOLUME_NX + x) * 4

        if (prob >= 0.5 && maskOpacity > 0) {
          const a = maskOpacity
          imgData.data[pIdx] = Math.round(gray * (1 - a) + 239 * a)
          imgData.data[pIdx + 1] = Math.round(gray * (1 - a) + 68 * a)
          imgData.data[pIdx + 2] = Math.round(gray * (1 - a) + 68 * a)
          imgData.data[pIdx + 3] = 255
        } else {
          imgData.data[pIdx] = gray
          imgData.data[pIdx + 1] = gray
          imgData.data[pIdx + 2] = gray
          imgData.data[pIdx + 3] = 255
        }
      }
    }

    this.offCtx.putImageData(imgData, 0, 0)
    this.baseLayer.destroyChildren()
    this.baseLayer.add(
      new Konva.Image({
        image: this.offscreen,
        x: 0,
        y: 0,
        width: CANVAS_2D_SIZE,
        height: CANVAS_2D_SIZE,
      }),
    )
    this.baseLayer.batchDraw()

    this.overlayLayer.destroyChildren()
    const inZRange = sliceZ >= roi.zMin && sliceZ <= roi.zMax
    this.overlayLayer.add(
      new Konva.Rect({
        x: roi.xMin * SCALE_2D,
        y: roi.yMin * SCALE_2D,
        width: (roi.xMax - roi.xMin + 1) * SCALE_2D,
        height: (roi.yMax - roi.yMin + 1) * SCALE_2D,
        stroke: inZRange ? '#38bdf8' : 'rgba(148, 163, 184, 0.45)',
        strokeWidth: 2,
        dash: [6, 4],
        listening: false,
      }),
    )

    for (const s of seeds) {
      if (s.z !== sliceZ) {
        continue
      }
      this.overlayLayer.add(
        new Konva.Circle({
          x: (s.x + 0.5) * SCALE_2D,
          y: (s.y + 0.5) * SCALE_2D,
          radius: 4.5,
          fill: s.label === 'foreground' ? '#ef4444' : '#06b6d4',
          stroke: '#ffffff',
          strokeWidth: 1.2,
          listening: false,
        }),
      )
    }

    this.overlayLayer.batchDraw()
  }
}
