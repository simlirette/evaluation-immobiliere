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
