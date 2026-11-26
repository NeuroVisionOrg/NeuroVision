/** DTO HTTP v2 de NeuroVision. Los tipos no validan JSON en tiempo de ejecucion. */
export type ContractVersion = '2'
export type InputMode = '2d' | '3d'
export type SeedLabel = 'foreground' | 'background'
export type Shape2D = readonly [number, number]
export type Shape3D = readonly [number, number, number]
type Row4 = readonly [number, number, number, number]
export type Matrix4 = readonly [Row4, Row4, Row4, Row4]

export interface ROISelection {
  x_min: number
  y_min: number
  x_max: number
  y_max: number
}

export interface ROI3DSelection {
  i_min: number
  j_min: number
  k_min: number
  i_max: number
  j_max: number
  k_max: number
}

export interface Seed {
  x: number
  y: number
  label: SeedLabel
}

export interface Seed3D {
  i: number
  j: number
  k: number
  label: SeedLabel
}

export interface ImageGeometry2D {
  mode: '2d'
  original_shape: Shape2D
  work_shape: Shape2D
  source_format: string
}

/** Cuadricula RAS+ del piloto, con indices [i,j,k] y unidades mm. */
export interface ImageGeometry3D {
  mode: '3d'
  original_shape: Shape3D
  work_shape: Shape3D
  source_format: string
  H_original: Matrix4
  H_work: Matrix4
  T_work_to_original: Matrix4
  spacing_mm: Shape3D
  units: 'mm'
  axis_codes: readonly ['R', 'A', 'S']
  affine_source: string
}

export type ImageGeometryDTO = ImageGeometry2D | ImageGeometry3D
export type ArrayDType = 'uint8' | 'float32_le' | 'uint32_le'

/** Bytes contiguos en orden C; el consumidor debe validar forma y longitud. */
export interface ArrayDTO<D extends ArrayDType = ArrayDType> {
  dtype: D
  shape: readonly number[]
  order: 'C'
  encoding: 'base64'
  data: string
}

export interface PreviewRequest {
  contract_version: ContractVersion
  mode: InputMode
}

export interface PreviewDTO {
  contract_version: ContractVersion
  input_id: string
  preparation_version: string
  geometry: ImageGeometryDTO
  view: ArrayDTO<'uint8'>
  display_min: number
  display_max: number
  warnings: readonly string[]
}

export interface ModelParameters {
  beta: number
  threshold: number
}

/** El metodo se deriva en Control; x0 es interno, no se envia por HTTP. */
export interface SolverParameters {
  omega: number
  rtol: number
  atol: number
  max_iterations: number
}

interface SegmentRequestBase {
  contract_version: ContractVersion
  request_id: string
  input_id: string
  preparation_version: string
  model: ModelParameters
  solver: SolverParameters
}

export type SegmentRequest = SegmentRequestBase &
  (
    | {
        mode: '2d'
        work_shape: Shape2D
        roi: ROISelection
        seeds: readonly Seed[]
      }
    | {
        mode: '3d'
        work_shape: Shape3D
        roi: ROI3DSelection
        seeds: readonly Seed3D[]
      }
  )

export type SolverMethod = 'sor'
export type SolverStatus = 'CONVERGED' | 'MAX_ITERATIONS' | 'NUMERICAL_FAILURE'

export interface EffectiveSolverConfig extends SolverParameters {
  method: SolverMethod
  initialization: 'zero'
}

export interface EffectiveModelConfig extends ModelParameters {
  connectivity: 4 | 6
  boundary_policy: 'roi_only_v1'
  weight_policy: 'intensity_exponential_v1'
}

export interface NormalizationRecord {
  minimum: number
  maximum: number
  policy: 'roi_minmax_v1'
}

interface SolverDiagnosticBase {
  method: SolverMethod
  iterations: number
  sweeps: number
  residual_history: readonly number[]
  elapsed_seconds: number
  omega_used: number
  rtol: number
  atol: number
  max_iterations: number
  stopping_threshold: number
  initialization: 'zero'
}

export type ConvergedDiagnostic = SolverDiagnosticBase & {
  status: 'CONVERGED'
  initial_residual: number
  final_residual: number
  failure_code: null
  failed_at_sweep: null
}

export type NonConvergedDiagnostic = SolverDiagnosticBase &
  (
    | {
        status: 'MAX_ITERATIONS'
        initial_residual: number
        final_residual: number
        failure_code: null
        failed_at_sweep: null
      }
    | {
        status: 'NUMERICAL_FAILURE'
        initial_residual: number | null
        final_residual: number | null
        failure_code: string
        failed_at_sweep: number | null
      }
  )

export type SolverDiagnosticDTO = ConvergedDiagnostic | NonConvergedDiagnostic

export interface DiagnosticMessage {
  stage: string
  code: string
  message: string
  request_id: string | null
}

export interface ErrorDTO {
  contract_version: ContractVersion
  error: DiagnosticMessage
}

type ReconstructionNotRun = {
  status: 'NOT_RUN'
  warnings: readonly string[]
  mask?: never
  boundary_mask?: never
}

type ReconstructionFailed = {
  status: 'FAILED'
  warnings: readonly string[]
  mask?: never
  boundary_mask?: never
}

type ReconstructionOK = {
  status: 'OK'
  mask: ArrayDTO<'uint8'>
  touches_boundary: boolean
  warnings: readonly string[]
}

export type Reconstruction2D = ReconstructionOK & { boundary_mask: ArrayDTO<'uint8'> }
export type Reconstruction3D = ReconstructionOK & { boundary_mask?: never }

export type ReconstructionDTO =
  Reconstruction2D | Reconstruction3D | ReconstructionFailed | ReconstructionNotRun

export type MeshStatus = 'OK' | 'PARTIAL' | 'UNAVAILABLE' | 'FAILED' | 'NOT_APPLICABLE' | 'NOT_RUN'

type MeshWithoutData<S extends MeshStatus> = {
  status: S
  reason?: string
  vertices?: never
  faces?: never
}

export type MeshDTO =
  | {
      status: 'OK' | 'PARTIAL'
      vertices: ArrayDTO<'float32_le'>
      faces: ArrayDTO<'uint32_le'>
      frame: 'RAS+'
      units: 'mm'
      touches_boundary: boolean
      warnings: readonly string[]
    }
  | MeshWithoutData<'UNAVAILABLE' | 'FAILED'>
  | MeshWithoutData<'NOT_APPLICABLE' | 'NOT_RUN'>

export type GraphDTO =
  | { status: 'OK'; png_base64: string }
  | { status: 'UNAVAILABLE' | 'FAILED'; reason: string; png_base64?: never }

interface RunIdentity {
  contract_version: ContractVersion
  request_id: string
  run_id: string
  input_id: string
  preparation_version: string
  system_id: string
  effective_solver: EffectiveSolverConfig
  normalization_record: NormalizationRecord
}

type RunSelection2D = {
  geometry: ImageGeometry2D
  roi: ROISelection
  seeds: readonly Seed[]
  effective_model: EffectiveModelConfig & { connectivity: 4 }
}

type RunSelection3D = {
  geometry: ImageGeometry3D
  roi: ROI3DSelection
  seeds: readonly Seed3D[]
  effective_model: EffectiveModelConfig & { connectivity: 6 }
}

type RunNotReconstructed =
  | { solver: NonConvergedDiagnostic; reconstruction: ReconstructionNotRun }
  | { solver: ConvergedDiagnostic; reconstruction: ReconstructionFailed }

type RunReconstructed<R extends ReconstructionOK> = {
  solver: ConvergedDiagnostic
  reconstruction: R
}

/** El snapshot no contiene malla, grafica, CSR ni solucion del solver. */
type ReconstructedSnapshot2D = RunIdentity & RunSelection2D & RunReconstructed<Reconstruction2D>
type ReconstructedSnapshot3D = RunIdentity & RunSelection3D & RunReconstructed<Reconstruction3D>

export type RunSnapshotDTO =
  | ReconstructedSnapshot2D
  | ReconstructedSnapshot3D
  | (RunIdentity & (RunSelection2D | RunSelection3D) & RunNotReconstructed)

export type RunResultDTO = RunIdentity &
  (
    | (RunSelection2D &
        (RunReconstructed<Reconstruction2D> | RunNotReconstructed) & {
          mesh: MeshWithoutData<'NOT_APPLICABLE'>
        })
    | (RunSelection3D &
        (
          | (RunReconstructed<Reconstruction3D> & {
              mesh: Exclude<MeshDTO, MeshWithoutData<'NOT_APPLICABLE' | 'NOT_RUN'>>
            })
          | (RunNotReconstructed & { mesh: MeshWithoutData<'NOT_RUN'> })
        ))
  ) & {
    graph: GraphDTO
    errors: readonly DiagnosticMessage[]
    warnings: readonly DiagnosticMessage[]
  }

export type ReferencePolicy = 'BRISC_BIN_128' | 'ITKSNAP_LABEL_2'

export interface MetricsDTO {
  run_id: string
  mode: InputMode
  domain: 'roi'
  reference_id: string
  reference_policy: ReferencePolicy
  foreground_count: number
  reference_count: number
  true_positives: number
  false_positives: number
  false_negatives: number
  dice: number | null
  iou: number | null
}

export type EvaluationRequest = {
  contract_version: ContractVersion
  reference_association: string
} & (
  | { snapshot: ReconstructedSnapshot2D; reference_policy: 'BRISC_BIN_128' }
  | { snapshot: ReconstructedSnapshot3D; reference_policy: 'ITKSNAP_LABEL_2' }
)

export type ExportRequest = { contract_version: ContractVersion } & (
  | {
      export_kind: 'numeric_csv'
      snapshot: RunSnapshotDTO
      metrics?: MetricsDTO
      slice_index?: never
    }
  | {
      export_kind: 'processed_png'
      snapshot: ReconstructedSnapshot2D
      slice_index?: never
      metrics?: never
    }
  | {
      export_kind: 'processed_png'
      snapshot: ReconstructedSnapshot3D
      slice_index: number
      metrics?: never
    }
)
