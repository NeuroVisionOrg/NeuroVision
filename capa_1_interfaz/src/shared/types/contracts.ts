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
