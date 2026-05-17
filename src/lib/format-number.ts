const CAD_FMT = new Intl.NumberFormat('fr-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 0,
})

/**
 * Formats a number as Canadian dollars in fr-CA locale (e.g. "400 000 $").
 * Defensively strips any "CA" prefix that some environments add before "D$".
 */
export function formatCAD(n: number): string {
  return CAD_FMT.format(n).replace('CA', '').trim()
}

/**
 * Formats a number in fr-CA locale with optional decimal precision.
 * Returns "—" for null or undefined inputs.
 */
export function fmtNum(n: number | null | undefined, digits = 0): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-CA', { maximumFractionDigits: digits }).format(n)
}

/**
 * Formats a percentage value with a " %" suffix.
 * Returns "—" for null or undefined inputs.
 * Defaults to 1 decimal digit (e.g. "3,5 %").
 */
export function formatPct(n: number | null | undefined, digits = 1): string {
  if (n == null) return '—'
  return `${fmtNum(n, digits)} %`
}

/**
 * Formats a large CAD amount in compact notation: 475 000 → "475 k$", 1 200 000 → "1,2 M$".
 * Uses 1 decimal for M when relevant, rounds to nearest k otherwise.
 * Values below 1000 are formatted as full dollars.
 */
export function formatCADCompact(n: number): string {
  if (Math.abs(n) >= 1_000_000) {
    const m = n / 1_000_000
    const decimals = Math.abs(m % 1) >= 0.05 ? 1 : 0
    return `${new Intl.NumberFormat('fr-CA', { maximumFractionDigits: decimals }).format(m)} M$`
  }
  if (Math.abs(n) >= 1_000) {
    const k = Math.round(n / 1_000)
    return `${new Intl.NumberFormat('fr-CA', { maximumFractionDigits: 0 }).format(k)} k$`
  }
  return formatCAD(n)
}
