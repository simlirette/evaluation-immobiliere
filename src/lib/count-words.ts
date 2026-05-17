/**
 * Counts words in a plain-text string.
 * Splits on whitespace (spaces, tabs, newlines); ignores empty tokens.
 */
export function countWords(text: string): number {
  return text.split(/\s+/).filter(s => s.length > 0).length
}
