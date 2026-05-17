import type { EnrichmentMarche } from '@/types'

export interface SalesPressureIndex {
  /** Composite index 0–100: 0 = full buyers' market, 100 = full sellers' market */
  index: number
  /** 'vendeur' index ≥ 60, 'équilibré' 40–59, 'acheteur' < 40 */
  regime: 'vendeur' | 'équilibré' | 'acheteur'
  /** Human-readable label describing market pressure */
  label: string
  /** Number of signals used in computation (1–3) */
  signalCount: number
}

/**
 * Computes a composite sales pressure index from available market signals.
 *
 * Uses up to 3 signals (each normalized to 0–100, higher = more seller pressure):
 * 1. Absorption rate (taux_absorption_pct): 100% → 100 points
 * 2. Vacancy rate (taux_inoccupation_pct): 0% → 100 points, 8%+ → 0 points
 * 3. Market score (score_marche): 10 → 100 points, 0 → 0 points
 *
 * Returns null when no signals are available.
 */
export function computeSalesPressureIndex(marche: EnrichmentMarche): SalesPressureIndex | null {
  const signals: number[] = []

  if (marche.taux_absorption_pct != null) {
    signals.push(Math.min(100, Math.max(0, marche.taux_absorption_pct)))
  }
  if (marche.taux_inoccupation_pct != null) {
    // Invert: low vacancy = seller pressure. Clamp at 8% (beyond = full buyers' market)
    signals.push(Math.min(100, Math.max(0, (1 - marche.taux_inoccupation_pct / 8) * 100)))
  }
  if (marche.score_marche != null) {
    signals.push(Math.min(100, Math.max(0, (marche.score_marche / 10) * 100)))
  }

  if (signals.length === 0) return null

  const index = Math.round(signals.reduce((s, v) => s + v, 0) / signals.length)
  const regime: SalesPressureIndex['regime'] =
    index >= 60 ? 'vendeur' : index >= 40 ? 'équilibré' : 'acheteur'
  const label =
    regime === 'vendeur' ? 'Marché de vendeurs — pression haussière sur les prix'
    : regime === 'acheteur' ? 'Marché d\'acheteurs — pression baissière sur les prix'
    : 'Marché équilibré — offre et demande en équilibre relatif'

  return { index, regime, label, signalCount: signals.length }
}
