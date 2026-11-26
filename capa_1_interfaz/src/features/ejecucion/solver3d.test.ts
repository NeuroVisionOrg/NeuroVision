import { describe, expect, it } from 'vitest'

import { SYNTHETIC_DATASETS } from '../../shared/datasets/syntheticVolumes'

import { computeTumorMetrics3D, solveRandomWalker3D } from './solver3d'

describe('solucionador Random Walker 3D', () => {
  it('converge y segmenta vóxeles tumorales con SOR y SSOR', () => {
    const ds = SYNTHETIC_DATASETS.esferico
    const sor = solveRandomWalker3D(ds, ds.defaultRoi, ds.defaultSeeds, 'sor', 1.5, 1e-3, 120)
    const ssor = solveRandomWalker3D(ds, ds.defaultRoi, ds.defaultSeeds, 'ssor', 1.5, 1e-3, 120)

    expect(sor.status).toBe('CONVERGED')
    expect(ssor.status).toBe('CONVERGED')
    expect(ssor.sweeps).toBe(ssor.iterations * 2)

    const metrics = computeTumorMetrics3D(ds, ssor.probabilities)
    expect(metrics.tumorVoxels).toBeGreaterThan(20)
    expect(metrics.volumeCm3).toBeGreaterThan(0)
  })

  it('rechaza omega fuera de (0, 2) en SOR y SSOR', () => {
    const ds = SYNTHETIC_DATASETS.esferico
    expect(() =>
      solveRandomWalker3D(ds, ds.defaultRoi, ds.defaultSeeds, 'sor', 2.0, 1e-3, 50),
    ).toThrow(RangeError)
  })

  it('reporta NUMERICAL_FAILURE si falta una clase de semilla en la ROI', () => {
    const ds = SYNTHETIC_DATASETS.esferico
    const onlyFg = ds.defaultSeeds.filter((s) => s.label === 'foreground')
    const res = solveRandomWalker3D(ds, ds.defaultRoi, onlyFg, 'jacobi', 1.0, 1e-3, 50)
    expect(res.status).toBe('NUMERICAL_FAILURE')
  })
})
