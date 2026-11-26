import { renderComparisonRows } from './features/comparacion/comparisonTable'
import { computeTumorMetrics3D, solveRandomWalker3D } from './features/ejecucion/solver3d'
import { createRoiFromDrag } from './features/roi/roiManager'
import {
  countSeedsByClass,
  stagePointToSeed3D,
  upsertSeed3D,
} from './features/semillas/seedManager'
import { Slice2DKonvaViewer } from './features/visor/slice2dKonva'
import { Tumor3DCanvasViewer } from './features/visor/tumor3dCanvas'
import {
  SYNTHETIC_DATASETS,
  VOLUME_NX,
  VOLUME_NY,
  VOLUME_NZ,
} from './shared/datasets/syntheticVolumes'
import type { Point } from './shared/geometry/coordinates'
import type {
  DatasetId,
  RenderMode3D,
  Roi3D,
  Seed3D,
  SolverMethod,
  SolverRunResult,
  ToolMode,
  VolumeDataset,
} from './shared/types/contracts'

import './styles/base.css'

function bootstrapApp(): void {
  const root = document.getElementById('app')
  if (!root) {
    throw new Error('No existe el contenedor principal de NeuroVision')
  }

  let activeDataset: VolumeDataset = SYNTHETIC_DATASETS.esferico
  let currentSliceZ = 12
  let activeTool: ToolMode = 'seed-tumor'
  let activeMethod: SolverMethod = 'sor'
  let omega = 1.55
  let tolerance = 1e-4
  let maskOpacity = 0.55
  let roi: Roi3D = { ...activeDataset.defaultRoi }
  let seeds: Seed3D[] = activeDataset.defaultSeeds.map((s) => ({ ...s }))
  let comparisonResults: SolverRunResult[] = []

  root.innerHTML = `
    <div class="nv-shell">
      <header class="nv-header">
        <div class="nv-brand">
          <span class="nv-badge">PROTOTIPO 3D v0.2</span>
          <div>
            <h1 class="nv-title">NeuroVision — Segmentación Cerebral y Modelado Tumoral 3D</h1>
            <p class="nv-subtitle">Visor 2D (Konva) · Reconstrucción Volumétrica 3D (Canvas) · Comparativa Ax = b</p>
          </div>
        </div>
        <div class="nv-api-bar">
          <span id="nv-api-dot" class="nv-status-dot"></span>
          <span id="nv-api-text">Verificando FastAPI (/api/v1/health)...</span>
        </div>
      </header>

      <main class="nv-grid">
        <aside class="nv-panel">
          <h2 class="nv-panel-title">1. Dataset y Anotación 2D</h2>

          <div class="nv-section">
            <label class="nv-label" for="nv-dataset">Volumen cerebral sintético</label>
            <select id="nv-dataset" class="nv-select">
              <option value="esferico">Caso 1 — Glioma Esférico Sintético</option>
              <option value="lobulado">Caso 2 — Tumor Lobulado Irregular</option>
              <option value="multifocal">Caso 3 — Lesión Multifocal Bilateral</option>
            </select>
            <small id="nv-dataset-desc" class="nv-hint" style="text-align:left;"></small>
          </div>

          <div class="nv-section">
            <label class="nv-label" for="nv-slice-z">
              <span>Corte Axial (Z)</span>
              <strong id="nv-slice-z-val">12 / ${VOLUME_NZ - 1}</strong>
            </label>
            <input id="nv-slice-z" class="nv-range" type="range" min="0" max="${VOLUME_NZ - 1}" value="12" />
          </div>

          <div class="nv-section">
            <span class="nv-label">
              <span>Herramienta Konva</span>
              <strong id="nv-seed-count">0 FG · 0 BG</strong>
            </span>
            <div class="nv-btn-group">
              <button id="tool-roi" class="nv-btn" type="button">ROI</button>
              <button id="tool-tumor" class="nv-btn tumor active" type="button">+ Tumor</button>
              <button id="tool-healthy" class="nv-btn healthy" type="button">- Sano</button>
            </div>
            <div class="nv-btn-group-2" style="margin-top:0.25rem;">
              <button id="btn-demo-seeds" class="nv-btn" type="button">Restaurar Demo</button>
              <button id="btn-clear-seeds" class="nv-btn" type="button">Limpiar Semillas</button>
            </div>
          </div>

          <div class="nv-section">
            <label class="nv-label" for="nv-opacity">
              <span>Opacidad máscara 2D</span>
              <strong id="nv-opacity-val">55%</strong>
            </label>
            <input id="nv-opacity" class="nv-range" type="range" min="0" max="100" value="55" />
          </div>

          <h2 class="nv-panel-title">2. Solucionador Numérico</h2>

          <div class="nv-section">
            <label class="nv-label" for="nv-method">Método principal activo</label>
            <select id="nv-method" class="nv-select">
              <option value="sor" selected>SOR (Sobrerrelajación Sucesiva)</option>
              <option value="ssor">SSOR (SOR Simétrico)</option>
              <option value="gauss_seidel">Gauss-Seidel</option>
              <option value="jacobi">Jacobi</option>
            </select>
          </div>

          <div class="nv-section">
            <label class="nv-label" for="nv-omega">
              <span>Factor de relajación (ω)</span>
              <strong id="nv-omega-val">1.55</strong>
            </label>
            <input id="nv-omega" class="nv-range" type="range" min="1.05" max="1.90" step="0.05" value="1.55" />
          </div>

          <div class="nv-section">
            <label class="nv-label" for="nv-tol">Tolerancia residual</label>
            <select id="nv-tol" class="nv-select">
              <option value="0.001">1e-3 (Rápida)</option>
              <option value="0.0001" selected>1e-4 (Estándar)</option>
              <option value="0.00001">1e-5 (Alta precisión)</option>
            </select>
          </div>

          <button id="btn-run" class="nv-btn-primary" type="button">
            Segmentar y Reconstruir 3D
          </button>
        </aside>

        <section class="nv-panel">
          <h2 class="nv-panel-title">Visores Sincronizados 2D (Konva) y 3D (Canvas)</h2>

          <div class="nv-viewports">
            <div class="nv-viewport-card">
              <div class="nv-viewport-header">
                <span>Corte Axial 2D — Konva Stage</span>
                <span id="nv-roi-badge" style="color:var(--accent);font-size:0.75rem;"></span>
              </div>
              <div id="konva-container" class="nv-canvas-frame"></div>
              <div class="nv-legend">
                <span class="nv-legend-item"><i class="nv-swatch" style="background:#ef4444;"></i>Tumor</span>
                <span class="nv-legend-item"><i class="nv-swatch" style="background:#06b6d4;"></i>Sano</span>
                <span class="nv-legend-item"><i class="nv-swatch" style="border:1px dashed #38bdf8;"></i>ROI</span>
              </div>
              <p class="nv-hint">Clic o arrastre para marcar semillas o delimitar el ROI.</p>
            </div>

            <div class="nv-viewport-card">
              <div class="nv-viewport-header">
                <span>Modelo Volumétrico 3D — Tumor</span>
                <div style="display:flex;gap:0.35rem;">
                  <button id="btn-rotate-toggle" class="nv-btn active" type="button" style="padding:0.2rem 0.45rem;font-size:0.72rem;">Auto-giro</button>
                  <button id="btn-reset-cam" class="nv-btn" type="button" style="padding:0.2rem 0.45rem;font-size:0.72rem;">Centrar</button>
                </div>
              </div>
              <div class="nv-canvas-frame">
                <canvas id="canvas-3d" width="360" height="360"></canvas>
              </div>
              <div class="nv-btn-group" style="width:100%;">
                <button id="mode-voxels" class="nv-btn active" type="button">Vóxeles 3D</button>
                <button id="mode-points" class="nv-btn" type="button">Nube Puntos</button>
                <button id="mode-contours" class="nv-btn" type="button">Contorno</button>
              </div>
              <p class="nv-hint">Arrastra para rotar 3D · Rueda para zoom · Amarillo = corte Z activo.</p>
            </div>
          </div>
        </section>

        <aside class="nv-panel">
          <h2 class="nv-panel-title">Métricas Tumorales 3D</h2>

          <div class="nv-kpi-grid">
            <div class="nv-kpi">
              <span class="nv-kpi-label">Volumen Tumor</span>
              <span id="kpi-volume" class="nv-kpi-value">—</span>
            </div>
            <div class="nv-kpi">
              <span class="nv-kpi-label">Vóxeles Activos</span>
              <span id="kpi-voxels" class="nv-kpi-value">—</span>
            </div>
            <div class="nv-kpi">
              <span class="nv-kpi-label">Dimensiones (X×Y×Z)</span>
              <span id="kpi-dims" class="nv-kpi-value">—</span>
            </div>
            <div class="nv-kpi">
              <span class="nv-kpi-label">Centroide 3D</span>
              <span id="kpi-centroid" class="nv-kpi-value">—</span>
            </div>
          </div>

          <h2 class="nv-panel-title">Comparativa Métodos (Ax = b)</h2>

          <div class="nv-table-wrap">
            <table class="nv-table">
              <thead>
                <tr>
                  <th>Método</th>
                  <th>Iter (Barr.)</th>
                  <th>Tiempo</th>
                  <th>Residual</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody id="nv-comp-tbody"></tbody>
            </table>
          </div>

          <p class="nv-hint" style="text-align:left;">
            Comparación ejecutada sobre el mismo sistema Laplaciano discreto dentro del ROI 3D.
          </p>
        </aside>
      </main>
    </div>
  `

  const konvaContainer = document.getElementById('konva-container') as HTMLDivElement | null
  const canvas3d = document.getElementById('canvas-3d') as HTMLCanvasElement | null
  if (!konvaContainer || !canvas3d) {
    return
  }

  let isDrawing2D = false
  let dragStartStage: Point | null = null

  const getActiveResult = (): SolverRunResult | undefined =>
    comparisonResults.find((r) => r.method === activeMethod) ?? comparisonResults[0]

  const viewer2d = new Slice2DKonvaViewer(konvaContainer, {
    onPointerDown: (pos) => {
      isDrawing2D = true
      if (activeTool === 'roi') {
        dragStartStage = pos
      } else {
        const label = activeTool === 'seed-tumor' ? 'foreground' : 'background'
        const seed = stagePointToSeed3D(
          pos,
          viewer2d.getViewportTransform(),
          currentSliceZ,
          label,
          VOLUME_NX,
          VOLUME_NY,
        )
        seeds = upsertSeed3D(seeds, seed)
        refresh2D()
      }
    },
    onPointerMove: (pos) => {
      if (!isDrawing2D) {
        return
      }
      if (activeTool === 'roi' && dragStartStage) {
        roi = createRoiFromDrag(
          dragStartStage,
          pos,
          viewer2d.getViewportTransform(),
          roi,
          VOLUME_NX,
          VOLUME_NY,
          VOLUME_NZ,
        )
        refresh2D()
      } else if (activeTool !== 'roi') {
        const label = activeTool === 'seed-tumor' ? 'foreground' : 'background'
        const seed = stagePointToSeed3D(
          pos,
          viewer2d.getViewportTransform(),
          currentSliceZ,
          label,
          VOLUME_NX,
          VOLUME_NY,
        )
        seeds = upsertSeed3D(seeds, seed)
        refresh2D()
      }
    },
    onPointerUp: () => {
      if (!isDrawing2D) {
        return
      }
      isDrawing2D = false
      dragStartStage = null
      runSegmentationPipeline()
    },
  })

  const viewer3d = new Tumor3DCanvasViewer(
    canvas3d,
    activeDataset,
    new Float64Array(VOLUME_NX * VOLUME_NY * VOLUME_NZ),
    roi,
  )

  const refresh2D = (): void => {
    const activeRes = getActiveResult()
    const validProbs =
      activeRes && activeRes.status !== 'NUMERICAL_FAILURE' ? activeRes.probabilities : null
    viewer2d.render(activeDataset, currentSliceZ, roi, seeds, validProbs, maskOpacity)

    const roiBadge = document.getElementById('nv-roi-badge')
    if (roiBadge) {
      roiBadge.textContent = `ROI [${roi.xMin}..${roi.xMax}, ${roi.yMin}..${roi.yMax}]`
    }

    const seedCount = document.getElementById('nv-seed-count')
    if (seedCount) {
      const counts = countSeedsByClass(seeds)
      seedCount.textContent = `${counts.foreground} FG · ${counts.background} BG`
    }
  }

  const refreshMetricsAndTable = (): void => {
    const activeRes = getActiveResult()
    if (!activeRes) {
      return
    }

    const metrics = computeTumorMetrics3D(activeDataset, activeRes.probabilities)
    const kpiVol = document.getElementById('kpi-volume')
    const kpiVox = document.getElementById('kpi-voxels')
    const kpiDims = document.getElementById('kpi-dims')
    const kpiCent = document.getElementById('kpi-centroid')

    if (kpiVol) {
      kpiVol.textContent = `${metrics.volumeCm3.toFixed(2)} cm³`
    }
    if (kpiVox) {
      kpiVox.textContent = `${metrics.tumorVoxels} vóxeles`
    }
    if (kpiDims) {
      const [dx, dy, dz] = metrics.dimensionsMm
      kpiDims.textContent = `${dx.toFixed(1)}×${dy.toFixed(1)}×${dz.toFixed(1)} mm`
    }
    if (kpiCent) {
      kpiCent.textContent = metrics.centroidVoxel
        ? `(${metrics.centroidVoxel[0].toFixed(1)}, ${metrics.centroidVoxel[1].toFixed(1)}, ${metrics.centroidVoxel[2].toFixed(1)})`
        : '—'
    }

    const tbody = document.getElementById('nv-comp-tbody')
    if (tbody) {
      tbody.innerHTML = renderComparisonRows(comparisonResults, activeMethod)
    }

    viewer3d.updateData(activeDataset, activeRes.probabilities, roi, currentSliceZ)
  }

  const runSegmentationPipeline = (): void => {
    const methods: SolverMethod[] = ['jacobi', 'gauss_seidel', 'sor', 'ssor']
    comparisonResults = methods.map((m) =>
      solveRandomWalker3D(activeDataset, roi, seeds, m, omega, tolerance, 90),
    )
    refresh2D()
    refreshMetricsAndTable()
  }

  const datasetSelect = document.getElementById('nv-dataset') as HTMLSelectElement | null
  const datasetDesc = document.getElementById('nv-dataset-desc')
  const sliceSlider = document.getElementById('nv-slice-z') as HTMLInputElement | null
  const sliceVal = document.getElementById('nv-slice-z-val')
  const opacitySlider = document.getElementById('nv-opacity') as HTMLInputElement | null
  const opacityVal = document.getElementById('nv-opacity-val')
  const methodSelect = document.getElementById('nv-method') as HTMLSelectElement | null
  const omegaSlider = document.getElementById('nv-omega') as HTMLInputElement | null
  const omegaVal = document.getElementById('nv-omega-val')
  const tolSelect = document.getElementById('nv-tol') as HTMLSelectElement | null

  if (datasetDesc) {
    datasetDesc.textContent = activeDataset.description
  }

  datasetSelect?.addEventListener('change', () => {
    const key = datasetSelect.value as DatasetId
    activeDataset = SYNTHETIC_DATASETS[key]
    roi = { ...activeDataset.defaultRoi }
    seeds = activeDataset.defaultSeeds.map((s) => ({ ...s }))
    if (datasetDesc) {
      datasetDesc.textContent = activeDataset.description
    }
    runSegmentationPipeline()
  })

  sliceSlider?.addEventListener('input', () => {
    currentSliceZ = Number(sliceSlider.value)
    if (sliceVal) {
      sliceVal.textContent = `${currentSliceZ} / ${VOLUME_NZ - 1}`
    }
    refresh2D()
    const activeRes = getActiveResult()
    if (activeRes) {
      viewer3d.updateData(activeDataset, activeRes.probabilities, roi, currentSliceZ)
    }
  })

  opacitySlider?.addEventListener('input', () => {
    maskOpacity = Number(opacitySlider.value) / 100
    if (opacityVal) {
      opacityVal.textContent = `${opacitySlider.value}%`
    }
    refresh2D()
  })

  methodSelect?.addEventListener('change', () => {
    activeMethod = methodSelect.value as SolverMethod
    refresh2D()
    refreshMetricsAndTable()
  })

  omegaSlider?.addEventListener('input', () => {
    omega = Number(omegaSlider.value)
    if (omegaVal) {
      omegaVal.textContent = omega.toFixed(2)
    }
  })

  omegaSlider?.addEventListener('change', () => {
    runSegmentationPipeline()
  })

  tolSelect?.addEventListener('change', () => {
    tolerance = Number(tolSelect.value)
    runSegmentationPipeline()
  })

  const setActiveToolButton = (tool: ToolMode): void => {
    activeTool = tool
    document.getElementById('tool-roi')?.classList.toggle('active', tool === 'roi')
    document.getElementById('tool-tumor')?.classList.toggle('active', tool === 'seed-tumor')
    document.getElementById('tool-healthy')?.classList.toggle('active', tool === 'seed-healthy')
  }

  document.getElementById('tool-roi')?.addEventListener('click', () => setActiveToolButton('roi'))
  document
    .getElementById('tool-tumor')
    ?.addEventListener('click', () => setActiveToolButton('seed-tumor'))
  document
    .getElementById('tool-healthy')
    ?.addEventListener('click', () => setActiveToolButton('seed-healthy'))

  document.getElementById('btn-demo-seeds')?.addEventListener('click', () => {
    roi = { ...activeDataset.defaultRoi }
    seeds = activeDataset.defaultSeeds.map((s) => ({ ...s }))
    runSegmentationPipeline()
  })

  document.getElementById('btn-clear-seeds')?.addEventListener('click', () => {
    seeds = []
    runSegmentationPipeline()
  })

  document.getElementById('btn-run')?.addEventListener('click', () => {
    runSegmentationPipeline()
  })

  const rotateToggle = document.getElementById('btn-rotate-toggle')
  let isAutoRotating = true
  rotateToggle?.addEventListener('click', () => {
    isAutoRotating = !isAutoRotating
    viewer3d.setAutoRotate(isAutoRotating)
    rotateToggle.classList.toggle('active', isAutoRotating)
  })

  document.getElementById('btn-reset-cam')?.addEventListener('click', () => {
    viewer3d.resetCamera()
  })

  const setMode3D = (mode: RenderMode3D): void => {
    viewer3d.setRenderMode(mode)
    document.getElementById('mode-voxels')?.classList.toggle('active', mode === 'voxels')
    document.getElementById('mode-points')?.classList.toggle('active', mode === 'points')
    document.getElementById('mode-contours')?.classList.toggle('active', mode === 'contours')
  }

  document.getElementById('mode-voxels')?.addEventListener('click', () => setMode3D('voxels'))
  document.getElementById('mode-points')?.addEventListener('click', () => setMode3D('points'))
  document.getElementById('mode-contours')?.addEventListener('click', () => setMode3D('contours'))

  const checkBackendHealth = async (): Promise<void> => {
    const dot = document.getElementById('nv-api-dot')
    const text = document.getElementById('nv-api-text')
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/health')
      if (res.ok) {
        dot?.classList.add('online')
        if (text) {
          text.textContent = 'FastAPI conectado (/api/v1/health OK)'
        }
        return
      }
    } catch {
      // Backend inactivo durante demostración local
    }
    if (text) {
      text.textContent = 'Modo prototipo local (datos sintéticos 3D activos)'
    }
  }

  void checkBackendHealth()
  runSegmentationPipeline()

  const animate = (): void => {
    viewer3d.tick()
    requestAnimationFrame(animate)
  }
  requestAnimationFrame(animate)
}

bootstrapApp()
