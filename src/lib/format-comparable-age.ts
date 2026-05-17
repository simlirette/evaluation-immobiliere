/**
 * Formats a comparable age in months as a human-readable French string.
 * Used to give evaluators quick reference without mental arithmetic from sale dates.
 */
export function formatComparableAge(ageMonths: number): string {
  if (ageMonths <= 0) return 'ce mois-ci'
  if (ageMonths < 12) return `${ageMonths} mois`
  const years = Math.floor(ageMonths / 12)
  const months = ageMonths % 12
  const yStr = `${years} an${years > 1 ? 's' : ''}`
  return months === 0 ? yStr : `${yStr} ${months} mois`
}
