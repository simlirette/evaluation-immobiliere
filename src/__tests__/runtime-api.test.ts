// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from 'vitest'
import { deleteRuntimeDossier, fetchRuntimeEnrichment, toggleRuntimePin, uploadRuntimeDocument } from '@/lib/runtime-api'

// ── Backend-persisted archive / pin ──────────────────────────────────────────

function mockFetch(ok: boolean, json: object) {
  return vi.fn().mockResolvedValue({ ok, status: ok ? 200 : 500, json: async () => json })
}

afterEach(() => vi.unstubAllGlobals())

describe('deleteRuntimeDossier', () => {
  it('calls POST /app/archive with session_id', async () => {
    const fetch = mockFetch(true, { ok: true })
    vi.stubGlobal('fetch', fetch)
    await deleteRuntimeDossier('abc')
    expect(fetch).toHaveBeenCalledOnce()
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/app/archive')
    expect(JSON.parse(init.body as string)).toMatchObject({ session_id: 'abc' })
  })

  it('calls POST /app/archive for each id independently', async () => {
    const fetch = mockFetch(true, { ok: true })
    vi.stubGlobal('fetch', fetch)
    await deleteRuntimeDossier('id1')
    await deleteRuntimeDossier('id2')
    expect(fetch).toHaveBeenCalledTimes(2)
    const bodies = fetch.mock.calls.map((c: unknown[]) => JSON.parse((c[1] as RequestInit).body as string))
    expect(bodies[0]).toMatchObject({ session_id: 'id1' })
    expect(bodies[1]).toMatchObject({ session_id: 'id2' })
  })
})

describe('toggleRuntimePin', () => {
  it('calls POST /app/pin with pinned:true when unpinned', async () => {
    const fetch = mockFetch(true, { ok: true })
    vi.stubGlobal('fetch', fetch)
    await toggleRuntimePin('xyz', false)
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/app/pin')
    expect(JSON.parse(init.body as string)).toMatchObject({ session_id: 'xyz', pinned: true })
  })

  it('calls POST /app/pin with pinned:false when currently pinned', async () => {
    const fetch = mockFetch(true, { ok: true })
    vi.stubGlobal('fetch', fetch)
    await toggleRuntimePin('xyz', true)
    const [, init] = fetch.mock.calls[0] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toMatchObject({ session_id: 'xyz', pinned: false })
  })

  it('archive and pin hit different endpoints', async () => {
    const fetch = mockFetch(true, { ok: true })
    vi.stubGlobal('fetch', fetch)
    await toggleRuntimePin('p1', false)
    await deleteRuntimeDossier('a1')
    const urls = fetch.mock.calls.map((c: unknown[]) => c[0] as string)
    expect(urls[0]).toContain('/app/pin')
    expect(urls[1]).toContain('/app/archive')
  })
})

// ── uploadRuntimeDocument validation ────────────────────────────────────────

describe('uploadRuntimeDocument — client-side validation', () => {
  it('rejects disallowed mime type', async () => {
    const file = new File(['data'], 'test.txt', { type: 'text/plain' })
    await expect(uploadRuntimeDocument('session-1', file)).rejects.toThrow('Type non autorisé')
  })

  it('accepts pdf mime type (proceeds past type check)', async () => {
    // Should not throw a type error — will fail later on fetch (no server in unit test)
    const file = new File(['%PDF-1'], 'doc.pdf', { type: 'application/pdf' })
    // Mock fetch to avoid network call
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      json: async () => ({ error: 'no server' }),
    }))
    await expect(uploadRuntimeDocument('session-1', file)).rejects.toThrow('Runtime API 502')
    vi.unstubAllGlobals()
  })

  it('rejects files over 10 MB', async () => {
    const bigData = new Uint8Array(11 * 1024 * 1024)
    const file = new File([bigData], 'huge.pdf', { type: 'application/pdf' })
    await expect(uploadRuntimeDocument('session-1', file)).rejects.toThrow('trop volumineux')
  })

  it('rejects extension mismatch before calling the BFF', async () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const file = new File(['%PDF-1'], 'doc.txt', { type: 'application/pdf' })
    await expect(uploadRuntimeDocument('session-1', file)).rejects.toThrow('Extension')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('rejects fake pdf bytes before calling the BFF', async () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const file = new File(['not a pdf'], 'doc.pdf', { type: 'application/pdf' })
    await expect(uploadRuntimeDocument('session-1', file)).rejects.toThrow('PDF invalide')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('accepts jpeg mime type (proceeds past type check)', async () => {
    const file = new File([new Uint8Array([0xff, 0xd8])], 'photo.jpg', { type: 'image/jpeg' })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'doc-1', name: 'photo.jpg' }),
    }))
    const doc = await uploadRuntimeDocument('session-1', file)
    expect(doc).toHaveProperty('id', 'doc-1')
    vi.unstubAllGlobals()
  })
})

// ── fetchRuntimeEnrichment ────────────────────────────────────────────────────

describe('fetchRuntimeEnrichment', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('returns enrichment from active session state', async () => {
    const enrichment = {
      score_global: { score: 7.5, grade: 'B', recommandation: 'Bon investissement' },
      alertes: { liste: [], nb_critiques: 0, nb_attention: 0, nb_info: 0 },
      score_investissement: null,
      indice_qualite_vie: null,
      score_risque: null,
      projection_valeur: null,
      rendement_locatif: null,
      valeur_indicative: null,
      taxes_municipales: null,
      ratio_prix_loyer: null,
      vetuste_batiment: null,
      source_coverage: {
        status: 'degraded',
        expected_sources: ['geocoding', 'infolot', 'mamh', 'sirf'],
        source_statuses: { geocoding: 'ok', infolot: 'failed', mamh: 'missing', sirf: 'missing' },
        available_count: 1,
        ok_count: 1,
        partial_count: 0,
        empty_count: 0,
        skipped_count: 0,
        failed_count: 1,
        missing_count: 2,
        last_updated_utc: '2026-05-21T00:00:00Z',
        diagnostics: [],
      },
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ active: { enrichment } }),
    }))
    const result = await fetchRuntimeEnrichment('session-abc')
    expect(result).not.toBeNull()
    expect(result?.score_global?.grade).toBe('B')
    expect(result?.score_global?.score).toBe(7.5)
    expect(result?.source_coverage?.status).toBe('degraded')
  })

  it('returns null when active is null', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ active: null }),
    }))
    const result = await fetchRuntimeEnrichment('session-new')
    expect(result).toBeNull()
  })

  it('calls /app/state with session_id query param', async () => {
    const fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ active: null }),
    })
    vi.stubGlobal('fetch', fetch)
    await fetchRuntimeEnrichment('my-session')
    const [url] = fetch.mock.calls[0] as [string]
    expect(url).toContain('/app/state')
    expect(url).toContain('my-session')
  })
})
