/**
 * Returns a human-readable count label for a filtered list.
 * When filtered: "X / N comparables"
 * When unfiltered or counts match: "N comparables"
 * When empty: null (caller can hide the label)
 */
export function formatListCount(visible: number, total: number, noun = 'comparable'): string | null {
  if (total === 0) return null
  const plural = total > 1 ? `${noun}s` : noun
  if (visible === total) return `${total} ${plural}`
  return `${visible} / ${total} ${plural}`
}
