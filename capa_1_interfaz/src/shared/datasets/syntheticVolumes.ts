import type { DatasetId, Roi3D, Seed3D, VolumeDataset } from '../types/contracts'

export const VOLUME_NX = 36
export const VOLUME_NY = 36
export const VOLUME_NZ = 24

export function voxelIndex3D(x: number, y: number, z: number): number {
  return z * VOLUME_NX * VOLUME_NY + y * VOLUME_NX + x
}

function createSyntheticVolume(
  id: DatasetId,
  name: string,
  description: string,
  tumorIntensityFn: (x: number, y: number, z: number) => number,
  defaultRoi: Roi3D,
  defaultSeeds: Seed3D[],
): VolumeDataset {
  const total = VOLUME_NX * VOLUME_NY * VOLUME_NZ
  const intensities = new Float64Array(total)
  const brainMask = new Uint8Array(total)
  const cx = (VOLUME_NX - 1) / 2
  const cy = (VOLUME_NY - 1) / 2
  const cz = (VOLUME_NZ - 1) / 2

  for (let z = 0; z < VOLUME_NZ; z++) {
    for (let y = 0; y < VOLUME_NY; y++) {
      for (let x = 0; x < VOLUME_NX; x++) {
        const i = voxelIndex3D(x, y, z)
        const dx = (x - cx) / 14.5
        const dy = (y - cy) / 16.0
        const dz = (z - cz) / 10.2
        const brainDist = dx * dx + dy * dy + dz * dz

        if (brainDist <= 1.0) {
          brainMask[i] = 1
          const vDx = (x - cx) / 2.6
          const vDy = (y - cy) / 5.2
          const vDz = (z - cz) / 3.5
          const isVentricle = vDx * vDx + vDy * vDy + vDz * vDz < 0.85
          const wave = 0.03 * Math.sin(x * 0.65 + z * 0.4) + 0.02 * Math.cos(y * 0.55 - z * 0.3)
          const baseTissue = isVentricle ? 0.18 : 0.42 + wave
          const tumorBoost = tumorIntensityFn(x, y, z)
          intensities[i] = Math.min(0.99, Math.max(0.05, baseTissue + tumorBoost))
        } else {
          brainMask[i] = 0
          intensities[i] = 0.04
        }
      }
    }
  }

  return {
    id,
    name,
    description,
    nx: VOLUME_NX,
    ny: VOLUME_NY,
    nz: VOLUME_NZ,
    voxelSpacingMm: [1.5, 1.5, 2.0],
    intensities,
    brainMask,
    defaultRoi,
    defaultSeeds,
  }
}

export const SYNTHETIC_DATASETS: Record<DatasetId, VolumeDataset> = {
  esferico: createSyntheticVolume(
    'esferico',
    'Caso 1 — Glioma Esférico Sintético',
    'Masa compacta hiperintensa en hemisferio derecho (ideal para validar convergencia).',
    (x, y, z) => {
      const d2 = (x - 22) ** 2 + (y - 16) ** 2 + ((z - 12) * 1.35) ** 2
      return d2 <= 28 ? 0.48 * Math.exp(-d2 / 36) : 0
    },
    { xMin: 13, xMax: 30, yMin: 8, yMax: 25, zMin: 6, zMax: 18 },
    [
      { x: 22, y: 16, z: 12, label: 'foreground' },
      { x: 21, y: 15, z: 11, label: 'foreground' },
      { x: 23, y: 17, z: 13, label: 'foreground' },
      { x: 15, y: 10, z: 12, label: 'background' },
      { x: 28, y: 22, z: 12, label: 'background' },
      { x: 16, y: 23, z: 10, label: 'background' },
    ],
  ),
  lobulado: createSyntheticVolume(
    'lobulado',
    'Caso 2 — Tumor Lobulado Irregular',
    'Lesión con dos lóbulos fusionados y bordes difusos en región frontotemporal.',
    (x, y, z) => {
      const lobeA = (x - 14) ** 2 + (y - 14) ** 2 + ((z - 11) * 1.4) ** 2
      const lobeB = (x - 18) ** 2 + (y - 19) ** 2 + ((z - 13) * 1.4) ** 2
      const valA = lobeA <= 24 ? 0.46 * Math.exp(-lobeA / 32) : 0
      const valB = lobeB <= 22 ? 0.44 * Math.exp(-lobeB / 28) : 0
      return Math.max(valA, valB)
    },
    { xMin: 7, xMax: 26, yMin: 7, yMax: 26, zMin: 5, zMax: 18 },
    [
      { x: 14, y: 14, z: 11, label: 'foreground' },
      { x: 18, y: 19, z: 13, label: 'foreground' },
      { x: 9, y: 9, z: 11, label: 'background' },
      { x: 24, y: 10, z: 12, label: 'background' },
      { x: 10, y: 24, z: 13, label: 'background' },
    ],
  ),
  multifocal: createSyntheticVolume(
    'multifocal',
    'Caso 3 — Lesión Multifocal Bilateral',
    'Dos focos tumorales independientes separados por tejido sano.',
    (x, y, z) => {
      const f1 = (x - 12) ** 2 + (y - 17) ** 2 + ((z - 10) * 1.4) ** 2
      const f2 = (x - 24) ** 2 + (y - 18) ** 2 + ((z - 14) * 1.4) ** 2
      const v1 = f1 <= 18 ? 0.48 * Math.exp(-f1 / 24) : 0
      const v2 = f2 <= 18 ? 0.48 * Math.exp(-f2 / 24) : 0
      return Math.max(v1, v2)
    },
    { xMin: 6, xMax: 30, yMin: 10, yMax: 25, zMin: 5, zMax: 19 },
    [
      { x: 12, y: 17, z: 10, label: 'foreground' },
      { x: 24, y: 18, z: 14, label: 'foreground' },
      { x: 18, y: 17, z: 12, label: 'background' },
      { x: 8, y: 12, z: 10, label: 'background' },
      { x: 28, y: 23, z: 14, label: 'background' },
    ],
  ),
}
