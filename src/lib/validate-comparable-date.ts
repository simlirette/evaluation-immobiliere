const STALE_MONTHS = 36

export interface ComparableDateValidation {
  ageMonths: number
  stale: boolean   // true if sale_date > 36 months before today
  warning: string | null
}

/**
 * Validates that a comparable's sale date meets OEAQ recency requirements.
 * Comparables older than 36 months are considered stale.
 *
 * @param saleDate - ISO date string (e.g. "2022-03-15")
 * @param today    - reference date; defaults to current date
 */
export function validateComparableDate(
  saleDate: string,
  today: Date = new Date()
): ComparableDateValidation {
  const sale = new Date(saleDate)
  const ageMonths = (today.getFullYear() - sale.getFullYear()) * 12
    + (today.getMonth() - sale.getMonth())
  const stale = ageMonths > STALE_MONTHS
  return {
    ageMonths,
    stale,
    warning: stale
      ? `Vente datant de ${ageMonths} mois — peut dépasser le seuil OEAQ (${STALE_MONTHS} mois).`
      : null,
  }
}
