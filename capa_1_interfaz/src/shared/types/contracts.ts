/** Datos que intercambiará la interfaz con Control; no incluye matrices dispersas. */
export type SeedLabel = 'foreground' | 'background'

export interface ROISelection {
  x_min: number
  y_min: number
  x_max: number
  y_max: number
}

export interface Seed {
  x: number
  y: number
  label: SeedLabel
}

export interface SelectionPayload {
  contract_version: '1'
  image_width: number
  image_height: number
  roi: ROISelection
  seeds: Seed[]
}

export type SolverMethod = 'jacobi' | 'gauss_seidel' | 'sor' | 'ssor'
export type SolverStatus = 'CONVERGED' | 'MAX_ITERATIONS' | 'NUMERICAL_FAILURE'
export type DatasetId = 'esferico' | 'lobulado' | 'multifocal'
export type RenderMode3D = 'voxels' | 'points' | 'contours'
export type ToolMode = 'roi' | 'seed-tumor' | 'seed-healthy'

export interface Roi3D {
  xMin: number
  xMax: number
  yMin: number
  yMax: number
  zMin: number
  zMax: number
}

export interface Seed3D {
  x: number
  y: number
  z: number
  label: SeedLabel
}

export interface VolumeDataset {
  id: DatasetId
  name: string
  description: string
  nx: number
  ny: number
  nz: number
  voxelSpacingMm: [number, number, number]
  intensities: Float64Array
  brainMask: Uint8Array
  defaultRoi: Roi3D
  defaultSeeds: Seed3D[]
}

export interface SolverRunResult {
  method: SolverMethod
  label: string
  status: SolverStatus
  iterations: number
  sweeps: number
  initialResidual: number
  finalResidual: number
  elapsedMs: number
  omegaUsed: number | null
  probabilities: Float64Array
}

export interface TumorMetrics3D {
  tumorVoxels: number
  volumeMm3: number
  volumeCm3: number
  dimensionsMm: [number, number, number]
  centroidVoxel: [number, number, number] | null
}
