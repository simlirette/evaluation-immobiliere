import { describe, it, expect } from 'vitest'
import { formatAgentError } from './agent-error'

describe('formatAgentError', () => {
  it('network error → réseau message', () => {
    expect(formatAgentError(new Error('Failed to fetch'))).toContain('réseau')
  })

  it('NetworkError → réseau message', () => {
    expect(formatAgentError(new Error('NetworkError occurred'))).toContain('réseau')
  })

  it('timeout → délai message', () => {
    expect(formatAgentError(new Error('Request timeout'))).toContain('délai')
  })

  it('401 → accès refusé', () => {
    expect(formatAgentError(new Error('401 Unauthorized'))).toContain('refusé')
  })

  it('403 → accès refusé', () => {
    expect(formatAgentError(new Error('403 Forbidden'))).toContain('refusé')
  })

  it('500 → serveur erreur', () => {
    expect(formatAgentError(new Error('500 Internal Server Error'))).toContain('serveur')
  })

  it('502 → serveur erreur', () => {
    expect(formatAgentError(new Error('502 Bad Gateway'))).toContain('serveur')
  })

  it('generic Error with message → includes message', () => {
    expect(formatAgentError(new Error('something went wrong'))).toContain('something went wrong')
  })

  it('non-Error string thrown → fallback message', () => {
    expect(formatAgentError('oops')).toContain('inattendue')
  })

  it('null thrown → fallback message', () => {
    expect(formatAgentError(null)).toContain('inattendue')
  })

  it('undefined thrown → fallback message', () => {
    expect(formatAgentError(undefined)).toContain('inattendue')
  })
})
