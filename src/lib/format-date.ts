/**
 * Format a YYYY-MM-DD date string as a French relative label.
 * "Aujourd'hui", "Hier", "il y a N jours", "il y a N semaines", then absolute.
 */
export function formatRelativeDate(dateStr: string, now: Date = new Date()): string {
  // Parse as local date (YYYY-MM-DD)
  const [y, m, d] = dateStr.split('-').map(Number)
  const date = new Date(y, m - 1, d)

  const todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const diffMs = todayMidnight.getTime() - date.getTime()
  const diffDays = Math.round(diffMs / 86400000)

  if (diffDays <= 0) return "Aujourd'hui"
  if (diffDays === 1) return 'Hier'
  if (diffDays < 7) return `il y a ${diffDays} jours`
  if (diffDays < 14) return 'il y a 1 semaine'
  if (diffDays < 30) return `il y a ${Math.floor(diffDays / 7)} semaines`

  const MONTHS_FR = ['jan', 'fév', 'mar', 'avr', 'mai', 'juin', 'juil', 'août', 'sep', 'oct', 'nov', 'déc']
  const label = `${d} ${MONTHS_FR[m - 1]}`
  return date.getFullYear() !== now.getFullYear() ? `${label} ${y}` : label
}
