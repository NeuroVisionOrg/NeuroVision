import {
  voxelIndex3D,
  VOLUME_NX,
  VOLUME_NY,
  VOLUME_NZ,
} from '../../shared/datasets/syntheticVolumes'
import type { RenderMode3D, Roi3D, VolumeDataset } from '../../shared/types/contracts'

interface ProjectedVoxel {
  sx: number
  sy: number
  depth: number
  size: number
  color: string
  alpha: number
}

export class Tumor3DCanvasViewer {
  private readonly canvas: HTMLCanvasElement
  private readonly ctx: CanvasRenderingContext2D
  private yaw = 0.65
  private pitch = 0.42
  private zoom = 1.0
  private dragging = false
  private lastX = 0
  private lastY = 0
  private autoRotate = true
  private renderMode: RenderMode3D = 'voxels'
  private dataset: VolumeDataset
  private probabilities: Float64Array
  private roi: Roi3D
  private currentSliceZ = 12

  constructor(
    canvas: HTMLCanvasElement,
    dataset: VolumeDataset,
    probabilities: Float64Array,
    roi: Roi3D,
  ) {
    this.canvas = canvas
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('No se pudo inicializar el contexto 2D del canvas 3D')
    }
    this.ctx = context
    this.dataset = dataset
    this.probabilities = probabilities
    this.roi = roi
    this.bindEvents()
  }

  public updateData(
    dataset: VolumeDataset,
    probabilities: Float64Array,
    roi: Roi3D,
    currentSliceZ: number,
  ): void {
    this.dataset = dataset
    this.probabilities = probabilities
    this.roi = roi
    this.currentSliceZ = currentSliceZ
    this.render()
  }

  public setRenderMode(mode: RenderMode3D): void {
    this.renderMode = mode
    this.render()
  }

  public setAutoRotate(enabled: boolean): void {
    this.autoRotate = enabled
  }

  public resetCamera(): void {
    this.yaw = 0.65
    this.pitch = 0.42
    this.zoom = 1.0
    this.render()
  }

  public tick(): void {
    if (this.autoRotate && !this.dragging) {
      this.yaw += 0.012
      this.render()
    }
  }

  private bindEvents(): void {
    this.canvas.addEventListener('mousedown', (e) => {
      this.dragging = true
      this.lastX = e.clientX
      this.lastY = e.clientY
    })

    window.addEventListener('mousemove', (e) => {
      if (!this.dragging) {
        return
      }
      const dx = e.clientX - this.lastX
      const dy = e.clientY - this.lastY
      this.lastX = e.clientX
      this.lastY = e.clientY
      this.yaw += dx * 0.012
      this.pitch = Math.max(-1.35, Math.min(1.35, this.pitch + dy * 0.012))
      this.render()
    })

    window.addEventListener('mouseup', () => {
      this.dragging = false
    })

    this.canvas.addEventListener(
      'wheel',
      (e) => {
        e.preventDefault()
        const factor = e.deltaY > 0 ? 0.92 : 1.08
        this.zoom = Math.max(0.55, Math.min(2.4, this.zoom * factor))
        this.render()
      },
      { passive: false },
    )
  }

  private project(x: number, y: number, z: number): { sx: number; sy: number; depth: number } {
    const nx = (x - (VOLUME_NX - 1) / 2) / (VOLUME_NX / 2)
    const ny = (y - (VOLUME_NY - 1) / 2) / (VOLUME_NY / 2)
    const nz = ((z - (VOLUME_NZ - 1) / 2) / (VOLUME_NZ / 2)) * 0.85

    const cosY = Math.cos(this.yaw)
    const sinY = Math.sin(this.yaw)
    const x1 = nx * cosY - nz * sinY
    const z1 = nx * sinY + nz * cosY

    const cosP = Math.cos(this.pitch)
    const sinP = Math.sin(this.pitch)
    const y2 = ny * cosP - z1 * sinP
    const z2 = ny * sinP + z1 * cosP

    const fov = 2.6
    const perspective = (fov / (fov + z2 + 1.5)) * 165 * this.zoom
    const half = this.canvas.width / 2

    return {
      sx: half + x1 * perspective,
      sy: half + y2 * perspective,
      depth: z2,
    }
  }

  public render(): void {
    const w = this.canvas.width
    const h = this.canvas.height
    const ctx = this.ctx

    ctx.fillStyle = '#020617'
    ctx.fillRect(0, 0, w, h)

    this.drawRoiWireframe()
    this.drawActiveSlicePlane()

    const items: ProjectedVoxel[] = []

    for (let z = 0; z < VOLUME_NZ; z++) {
      for (let y = 0; y < VOLUME_NY; y++) {
        for (let x = 0; x < VOLUME_NX; x++) {
          const i = voxelIndex3D(x, y, z)
          const prob = this.probabilities[i] ?? 0
          const isBrain = (this.dataset.brainMask[i] ?? 0) === 1

          if (prob >= 0.5) {
            if (this.renderMode === 'contours') {
              const left = x > 0 ? (this.probabilities[voxelIndex3D(x - 1, y, z)] ?? 0) : 0
              const right =
                x < VOLUME_NX - 1 ? (this.probabilities[voxelIndex3D(x + 1, y, z)] ?? 0) : 0
              const up = y > 0 ? (this.probabilities[voxelIndex3D(x, y - 1, z)] ?? 0) : 0
              const down =
                y < VOLUME_NY - 1 ? (this.probabilities[voxelIndex3D(x, y + 1, z)] ?? 0) : 0
              if (left >= 0.5 && right >= 0.5 && up >= 0.5 && down >= 0.5) {
                continue
              }
            }

            const p = this.project(x, y, z)
            const shade = Math.min(1, Math.max(0.35, 0.72 - p.depth * 0.25))
            const r = Math.round(239 * shade + 16)
            const g = Math.round(68 * shade + (prob - 0.5) * 90)
            const b = Math.round(68 * shade + 24)
            const onCurrentSlice = z === this.currentSliceZ

            items.push({
              sx: p.sx,
              sy: p.sy,
              depth: p.depth,
              size: this.renderMode === 'points' ? 3.2 * this.zoom : 7.5 * this.zoom,
              color: onCurrentSlice ? '#facc15' : `rgb(${r}, ${g}, ${b})`,
              alpha: this.renderMode === 'points' ? 0.92 : 0.88,
            })
          } else if (isBrain && x % 3 === 0 && y % 3 === 0 && z % 3 === 0) {
            const p = this.project(x, y, z)
            items.push({
              sx: p.sx,
              sy: p.sy,
              depth: p.depth,
              size: 1.8 * this.zoom,
              color: '#38bdf8',
              alpha: 0.16,
            })
          }
        }
      }
    }

    items.sort((a, b) => b.depth - a.depth)

    for (const item of items) {
      ctx.globalAlpha = item.alpha
      ctx.fillStyle = item.color
      if (this.renderMode === 'voxels') {
        const half = item.size / 2
        ctx.fillRect(item.sx - half, item.sy - half, item.size, item.size)
        ctx.strokeStyle = 'rgba(15, 23, 42, 0.35)'
        ctx.lineWidth = 0.6
        ctx.strokeRect(item.sx - half, item.sy - half, item.size, item.size)
      } else {
        ctx.beginPath()
        ctx.arc(item.sx, item.sy, item.size / 2, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    ctx.globalAlpha = 1
    ctx.fillStyle = '#94a3b8'
    ctx.font = '11px system-ui, sans-serif'
    ctx.fillText(
      `Ángulo: ${(this.yaw % (Math.PI * 2)).toFixed(2)} rad | Zoom: ${this.zoom.toFixed(2)}x`,
      10,
      h - 10,
    )
  }

  private drawRoiWireframe(): void {
    const { xMin, xMax, yMin, yMax, zMin, zMax } = this.roi
    const corners = [
      this.project(xMin, yMin, zMin),
      this.project(xMax, yMin, zMin),
      this.project(xMax, yMax, zMin),
      this.project(xMin, yMax, zMin),
      this.project(xMin, yMin, zMax),
      this.project(xMax, yMin, zMax),
      this.project(xMax, yMax, zMax),
      this.project(xMin, yMax, zMax),
    ]
    const edges: [number, number][] = [
      [0, 1],
      [1, 2],
      [2, 3],
      [3, 0],
      [4, 5],
      [5, 6],
      [6, 7],
      [7, 4],
      [0, 4],
      [1, 5],
      [2, 6],
      [3, 7],
    ]

    this.ctx.save()
    this.ctx.strokeStyle = 'rgba(56, 189, 248, 0.38)'
    this.ctx.lineWidth = 1
    this.ctx.setLineDash([4, 3])
    for (const [a, b] of edges) {
      const ca = corners[a]
      const cb = corners[b]
      if (ca && cb) {
        this.ctx.beginPath()
        this.ctx.moveTo(ca.sx, ca.sy)
        this.ctx.lineTo(cb.sx, cb.sy)
        this.ctx.stroke()
      }
    }
    this.ctx.restore()
  }

  private drawActiveSlicePlane(): void {
    const z = this.currentSliceZ
    const p0 = this.project(0, 0, z)
    const p1 = this.project(VOLUME_NX - 1, 0, z)
    const p2 = this.project(VOLUME_NX - 1, VOLUME_NY - 1, z)
    const p3 = this.project(0, VOLUME_NY - 1, z)

    this.ctx.save()
    this.ctx.strokeStyle = 'rgba(250, 204, 21, 0.55)'
    this.ctx.fillStyle = 'rgba(250, 204, 21, 0.05)'
    this.ctx.lineWidth = 1
    this.ctx.beginPath()
    this.ctx.moveTo(p0.sx, p0.sy)
    this.ctx.lineTo(p1.sx, p1.sy)
    this.ctx.lineTo(p2.sx, p2.sy)
    this.ctx.lineTo(p3.sx, p3.sy)
    this.ctx.closePath()
    this.ctx.fill()
    this.ctx.stroke()
    this.ctx.restore()
  }
}
