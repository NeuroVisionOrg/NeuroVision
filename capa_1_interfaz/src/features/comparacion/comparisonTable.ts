import type { SolverMethod, SolverRunResult } from '../../shared/types/contracts'

export function renderComparisonRows(
  results: readonly SolverRunResult[],
  activeMethod: SolverMethod,
): string {
  return results
    .map((row) => {
      const isSelected = row.method === activeMethod
      const statusClass = row.status === 'CONVERGED' ? 'nv-pill-ok' : 'nv-pill-warn'
      const statusLabel =
        row.status === 'CONVERGED' ? 'OK' : row.status === 'MAX_ITERATIONS' ? 'Tope' : 'Sin sem.'
      return `
        <tr class="${isSelected ? 'selected-row' : ''}">
          <td><strong>${row.label}</strong></td>
          <td>${row.iterations} (${row.sweeps})</td>
          <td>${row.elapsedMs.toFixed(1)} ms</td>
          <td>${row.finalResidual.toExponential(1)}</td>
          <td class="${statusClass}">${statusLabel}</td>
        </tr>
      `
    })
    .join('')
}
