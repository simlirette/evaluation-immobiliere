// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { deleteRuntimeDossier, toggleRuntimePin, uploadRuntimeDocument } from '@/lib/runtime-api'

// ── localStorage helpers ─────────────────────────────────────────────────────

describe('deleteRuntimeDossier', () => {
  beforeEach(() => localStorage.clear())

  it('adds id to archived set', async () => {
    await deleteRuntimeDossier('abc')
    const stored = JSON.parse(localStorage.getItem('eval_immo_archived') ?? '[]') as string[]
    expect(stored).toContain('abc')
  })

  it('accumulates multiple archived ids', async () => {
    await deleteRuntimeDossier('id1')
    await deleteRuntimeDossier('id2')
    const stored = JSON.parse(localStorage.getItem('eval_immo_archived') ?? '[]') as string[]
    expect(stored).toContain('id1')
    expect(stored).toContain('id2')
  })

  it('is idempotent', async () => {
    await deleteRuntimeDossier('dup')
    await deleteRuntimeDossier('dup')
    const stored = JSON.parse(localStorage.getItem('eval_immo_archived') ?? '[]') as string[]
    expect(stored.filter(x => x === 'dup').length).toBe(1)
  })
})

describe('toggleRuntimePin', () => {
  beforeEach(() => localStorage.clear())

  it('pins an unpinned dossier', async () => {
    await toggleRuntimePin('xyz', false)
    const stored = JSON.parse(localStorage.getItem('eval_immo_pinned') ?? '[]') as string[]
    expect(stored).toContain('xyz')
  })

  it('unpins a pinned dossier', async () => {
    await toggleRuntimePin('xyz', false)
    await toggleRuntimePin('xyz', true)
    const stored = JSON.parse(localStorage.getItem('eval_immo_pinned') ?? '[]') as string[]
    expect(stored).not.toContain('xyz')
  })

  it('pinned and archived sets are independent', async () => {
    await toggleRuntimePin('p1', false)
    await deleteRuntimeDossier('a1')
    const pinned = JSON.parse(localStorage.getItem('eval_immo_pinned') ?? '[]') as string[]
    const archived = JSON.parse(localStorage.getItem('eval_immo_archived') ?? '[]') as string[]
    expect(pinned).toContain('p1')
    expect(archived).toContain('a1')
    expect(pinned).not.toContain('a1')
    expect(archived).not.toContain('p1')
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
