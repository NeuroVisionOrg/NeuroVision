/** Comprobaciones estaticas ejecutadas por tsc --noEmit, sin solver ni mocks. */
import type {
  ArrayDTO,
  EvaluationRequest,
  ExportRequest,
  ImageGeometryDTO,
  MeshDTO,
  NonConvergedDiagnostic,
  Reconstruction2D,
  ROISelection,
  RunResultDTO,
  RunSnapshotDTO,
  Seed,
  SegmentRequest,
  Shape3D,
  SolverDiagnosticDTO,
  SolverMethod,
  SolverParameters,
} from './contracts'

type Assert<T extends true> = T
type Reject<A, B> = [A] extends [B] ? false : true
type Request3D = Extract<SegmentRequest, { mode: '3d' }>
type Request2D = Extract<SegmentRequest, { mode: '2d' }>
type Geometry3D = Extract<ImageGeometryDTO, { mode: '3d' }>
type Run2D = Extract<RunResultDTO, { geometry: { mode: '2d' } }>
type Run3D = Extract<RunResultDTO, { geometry: { mode: '3d' } }>
type FailedSnapshot = Extract<RunSnapshotDTO, { solver: NonConvergedDiagnostic }>
type Valid3D = Extract<
  RunSnapshotDTO,
  { geometry: { mode: '3d' }; reconstruction: { status: 'OK' } }
>

/** Si una restriccion deja de cumplirse, falla la compilacion. */
export type ContractChecks = [
  Assert<Reject<'jacobi' | 'gauss_seidel' | 'ssor', SolverMethod>>,
  Assert<Reject<'1', SegmentRequest['contract_version']>>,
  Assert<Reject<Omit<Request3D, 'roi'> & { roi: ROISelection }, SegmentRequest>>,
  Assert<Reject<Omit<Request3D, 'seeds'> & { seeds: Seed[] }, SegmentRequest>>,
  Assert<Reject<Omit<Request2D, 'work_shape'> & { work_shape: Shape3D }, SegmentRequest>>,
  Assert<Reject<Omit<Geometry3D, 'H_work'>, ImageGeometryDTO>>,
  Assert<Reject<ArrayDTO<'float32_le'>, ArrayDTO<'uint8'>>>,
  Assert<Reject<Omit<SolverParameters, 'omega'>, SolverParameters>>,
  Assert<'solution' extends keyof SolverDiagnosticDTO ? false : true>,
  Assert<'method' extends keyof SolverParameters ? false : true>,
  Assert<'mesh' extends keyof RunSnapshotDTO ? false : true>,
  Assert<'graph' extends keyof RunSnapshotDTO ? false : true>,
  Assert<
    Reject<
      Omit<FailedSnapshot, 'reconstruction'> & { reconstruction: Reconstruction2D },
      RunSnapshotDTO
    >
  >,
  Assert<
    Reject<
      Omit<Run2D, 'mesh'> & { mesh: Extract<MeshDTO, { status: 'OK' | 'PARTIAL' }> },
      RunResultDTO
    >
  >,
  Assert<Reject<Omit<Run3D, 'mesh'> & { mesh: { status: 'NOT_APPLICABLE' } }, RunResultDTO>>,
  Assert<
    Reject<
      {
        contract_version: '2'
        snapshot: FailedSnapshot
        reference_policy: 'BRISC_BIN_128'
        reference_association: string
      },
      EvaluationRequest
    >
  >,
  Assert<
    Reject<
      { contract_version: '2'; snapshot: Valid3D; export_kind: 'processed_png' },
      ExportRequest
    >
  >,
]
