import {
  voxelIndex3D,
  VOLUME_NX,
  VOLUME_NY,
  VOLUME_NZ,
} from '../../shared/datasets/syntheticVolumes'
import type {
  Roi3D,
  Seed3D,
  SolverMethod,
  SolverRunResult,
  TumorMetrics3D,
  VolumeDataset,
} from '../../shared/types/contracts'

const METHOD_LABELS: Record<SolverMethod, string> = {
  jacobi: 'Jacobi',
  gauss_seidel: 'Gauss-Seidel',
  sor: 'SOR',
  ssor: 'SSOR',
}

export function solveRandomWalker3D(
  dataset: VolumeDataset,
  roi: Roi3D,
  seeds: readonly Seed3D[],
  method: SolverMethod,
  omega: number,
  tolerance: number,
  maxIterations: number,
): SolverRunResult {
  const usesOmega = method === 'sor' || method === 'ssor'
  if (usesOmega && (!Number.isFinite(omega) || omega <= 0 || omega >= 2)) {
    throw new RangeError('SOR y SSOR requieren 0 < omega < 2')
  }

  const t0 = performance.now()
  const rx = roi.xMax - roi.xMin + 1
  const ry = roi.yMax - roi.yMin + 1
  const rz = roi.zMax - roi.zMin + 1
  const n = rx * ry * rz

  const fixed = new Int8Array(n)
  fixed.fill(-1)
  const xVec = new Float64Array(n)
  const localIndex = (lx: number, ly: number, lz: number): number => lz * rx * ry + ly * rx + lx

  for (let lz = 0; lz < rz; lz++) {
    for (let ly = 0; ly < ry; ly++) {
      for (let lx = 0; lx < rx; lx++) {
        const isBoundary =
          lx === 0 || lx === rx - 1 || ly === 0 || ly === ry - 1 || lz === 0 || lz === rz - 1
        if (isBoundary) {
          const li = localIndex(lx, ly, lz)
          fixed[li] = 0
          xVec[li] = 0
        }
      }
    }
  }

  let hasFg = false
  let hasBg = false
  for (const s of seeds) {
    if (
      s.x >= roi.xMin &&
      s.x <= roi.xMax &&
      s.y >= roi.yMin &&
      s.y <= roi.yMax &&
      s.z >= roi.zMin &&
      s.z <= roi.zMax
    ) {
      const li = localIndex(s.x - roi.xMin, s.y - roi.yMin, s.z - roi.zMin)
      const val = s.label === 'foreground' ? 1 : 0
      fixed[li] = val
      xVec[li] = val
      if (val === 1) {
        hasFg = true
      } else {
        hasBg = true
      }
    }
  }

  const label = usesOmega
    ? `${METHOD_LABELS[method]} (ω=${omega.toFixed(2)})`
    : METHOD_LABELS[method]

  if (!hasFg || !hasBg) {
    return {
      method,
      label,
      status: 'NUMERICAL_FAILURE',
      iterations: 0,
      sweeps: 0,
      initialResidual: 0,
      finalResidual: 0,
      elapsedMs: Math.max(0.1, performance.now() - t0),
      omegaUsed: usesOmega ? omega : null,
      probabilities: new Float64Array(VOLUME_NX * VOLUME_NY * VOLUME_NZ),
    }
  }

  const wXm = new Float64Array(n)
  const wXp = new Float64Array(n)
  const wYm = new Float64Array(n)
  const wYp = new Float64Array(n)
  const wZm = new Float64Array(n)
  const wZp = new Float64Array(n)
  const diag = new Float64Array(n)
  const beta = 45.0
  const eps = 1e-4

  for (let lz = 0; lz < rz; lz++) {
    for (let ly = 0; ly < ry; ly++) {
      for (let lx = 0; lx < rx; lx++) {
        const li = localIndex(lx, ly, lz)
        if ((fixed[li] ?? -1) !== -1) {
          diag[li] = 1
          continue
        }
        const gx = roi.xMin + lx
        const gy = roi.yMin + ly
        const gz = roi.zMin + lz
        const i0 = dataset.intensities[voxelIndex3D(gx, gy, gz)] ?? 0

        const edgeWeight = (nx: number, ny: number, nz: number): number => {
          const iv = dataset.intensities[voxelIndex3D(nx, ny, nz)] ?? 0
          const diff = i0 - iv
          return Math.exp(-beta * diff * diff) + eps
        }

        const xm = lx > 0 ? edgeWeight(gx - 1, gy, gz) : 0
        const xp = lx < rx - 1 ? edgeWeight(gx + 1, gy, gz) : 0
        const ym = ly > 0 ? edgeWeight(gx, gy - 1, gz) : 0
        const yp = ly < ry - 1 ? edgeWeight(gx, gy + 1, gz) : 0
        const zm = lz > 0 ? edgeWeight(gx, gy, gz - 1) : 0
        const zp = lz < rz - 1 ? edgeWeight(gx, gy, gz + 1) : 0

        wXm[li] = xm
        wXp[li] = xp
        wYm[li] = ym
        wYp[li] = yp
        wZm[li] = zm
        wZp[li] = zp
        diag[li] = xm + xp + ym + yp + zm + zp + 1e-6
      }
    }
  }

  const nextVec = new Float64Array(n)
  nextVec.set(xVec)
  const strideY = rx
  const strideZ = rx * ry

  const updateNode = (li: number, source: Float64Array, target: Float64Array, w: number): void => {
    if ((fixed[li] ?? -1) !== -1) {
      return
    }
    const sumNeighbors =
      (wXm[li] ?? 0) * (source[li - 1] ?? 0) +
      (wXp[li] ?? 0) * (source[li + 1] ?? 0) +
      (wYm[li] ?? 0) * (source[li - strideY] ?? 0) +
      (wYp[li] ?? 0) * (source[li + strideY] ?? 0) +
      (wZm[li] ?? 0) * (source[li - strideZ] ?? 0) +
      (wZp[li] ?? 0) * (source[li + strideZ] ?? 0)

    const gsVal = sumNeighbors / (diag[li] ?? 1)
    const oldVal = source[li] ?? 0
    target[li] = oldVal + w * (gsVal - oldVal)
  }

  const computeResidual = (vec: Float64Array): number => {
    let sumSq = 0
    for (let li = 0; li < n; li++) {
      if ((fixed[li] ?? -1) !== -1) {
        continue
      }
      const ax =
        (diag[li] ?? 1) * (vec[li] ?? 0) -
        ((wXm[li] ?? 0) * (vec[li - 1] ?? 0) +
          (wXp[li] ?? 0) * (vec[li + 1] ?? 0) +
          (wYm[li] ?? 0) * (vec[li - strideY] ?? 0) +
          (wYp[li] ?? 0) * (vec[li + strideY] ?? 0) +
          (wZm[li] ?? 0) * (vec[li - strideZ] ?? 0) +
          (wZp[li] ?? 0) * (vec[li + strideZ] ?? 0))
      sumSq += ax * ax
    }
    return Math.sqrt(sumSq)
  }

  const initialResidual = computeResidual(xVec)
  let residual = initialResidual
  let iterations = 0
  let converged = residual <= tolerance

  while (iterations < maxIterations && !converged) {
    iterations++
    if (method === 'jacobi') {
      for (let li = 0; li < n; li++) {
        updateNode(li, xVec, nextVec, 1.0)
      }
      xVec.set(nextVec)
    } else if (method === 'gauss_seidel') {
      for (let li = 0; li < n; li++) {
        updateNode(li, xVec, xVec, 1.0)
      }
    } else if (method === 'sor') {
      for (let li = 0; li < n; li++) {
        updateNode(li, xVec, xVec, omega)
      }
    } else {
      for (let li = 0; li < n; li++) {
        updateNode(li, xVec, xVec, omega)
      }
      for (let li = n - 1; li >= 0; li--) {
        updateNode(li, xVec, xVec, omega)
      }
    }

    residual = computeResidual(xVec)
    if (residual <= tolerance) {
      converged = true
    }
  }

  const fullProb = new Float64Array(VOLUME_NX * VOLUME_NY * VOLUME_NZ)
  for (let lz = 0; lz < rz; lz++) {
    for (let ly = 0; ly < ry; ly++) {
      for (let lx = 0; lx < rx; lx++) {
        const li = localIndex(lx, ly, lz)
        const p = Math.min(1, Math.max(0, xVec[li] ?? 0))
        const gi = voxelIndex3D(roi.xMin + lx, roi.yMin + ly, roi.zMin + lz)
        fullProb[gi] = p
      }
    }
  }

  return {
    method,
    label,
    status: converged ? 'CONVERGED' : 'MAX_ITERATIONS',
    iterations,
    sweeps: method === 'ssor' ? iterations * 2 : iterations,
    initialResidual,
    finalResidual: residual,
    elapsedMs: Math.max(0.1, performance.now() - t0),
    omegaUsed: usesOmega ? omega : null,
    probabilities: fullProb,
  }
}

export function computeTumorMetrics3D(
  dataset: VolumeDataset,
  probabilities: Float64Array,
  threshold = 0.5,
): TumorMetrics3D {
  const [sx, sy, sz] = dataset.voxelSpacingMm
  const voxelVolMm3 = sx * sy * sz

  let minX = VOLUME_NX
  let maxX = 0
  let minY = VOLUME_NY
  let maxY = 0
  let minZ = VOLUME_NZ
  let maxZ = 0
  let sumX = 0
  let sumY = 0
  let sumZ = 0
  let count = 0

  for (let z = 0; z < VOLUME_NZ; z++) {
    for (let y = 0; y < VOLUME_NY; y++) {
      for (let x = 0; x < VOLUME_NX; x++) {
        if ((probabilities[voxelIndex3D(x, y, z)] ?? 0) >= threshold) {
          minX = Math.min(minX, x)
          maxX = Math.max(maxX, x)
          minY = Math.min(minY, y)
          maxY = Math.max(maxY, y)
          minZ = Math.min(minZ, z)
          maxZ = Math.max(maxZ, z)
          sumX += x
          sumY += y
          sumZ += z
          count++
        }
      }
    }
  }

  const volumeMm3 = count * voxelVolMm3
  return {
    tumorVoxels: count,
    volumeMm3,
    volumeCm3: volumeMm3 / 1000,
    dimensionsMm:
      count > 0
        ? [(maxX - minX + 1) * sx, (maxY - minY + 1) * sy, (maxZ - minZ + 1) * sz]
        : [0, 0, 0],
    centroidVoxel: count > 0 ? [sumX / count, sumY / count, sumZ / count] : null,
  }
}
