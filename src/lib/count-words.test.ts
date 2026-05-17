import { describe, it, expect } from 'vitest'
import { countWords } from './count-words'

describe('countWords', () => {
  it('empty string → 0', () => expect(countWords('')).toBe(0))
  it('whitespace only → 0', () => expect(countWords('   \n\t  ')).toBe(0))
  it('single word', () => expect(countWords('bonjour')).toBe(1))
  it('multiple words', () => expect(countWords('Bonjour le monde')).toBe(3))
  it('leading and trailing spaces', () => expect(countWords('  hello world  ')).toBe(2))
  it('newlines as separators', () => expect(countWords('ligne une\nligne deux\nligne trois')).toBe(6))
  it('tabs as separators', () => expect(countWords('a\tb\tc')).toBe(3))
  it('mixed whitespace', () => expect(countWords('un\n deux \t trois')).toBe(3))
})
