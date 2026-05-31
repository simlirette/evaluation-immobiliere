import { afterEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const ORIGINAL_ENV = { ...process.env }

function resetEnv() {
  process.env = { ...ORIGINAL_ENV }
  delete process.env.RUNTIME_API_URL
  delete process.env.RUNTIME_API_TOKEN
  delete process.env.NEXT_PUBLIC_SUPABASE_URL
  delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
}

async function loadRoute(user: { id: string } | null) {
  vi.resetModules()
  vi.doMock('@/lib/supabase/server', () => ({
    createClient: vi.fn(async () => ({
      auth: {
        getUser: vi.fn(async () => ({ data: { user } })),
      },
    })),
  }))
  return import('@/app/api/runtime/[...path]/route')
}

function ctx(path: string[]) {
  return { params: Promise.resolve({ path }) }
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
  vi.doUnmock('@/lib/supabase/server')
  vi.resetModules()
  resetEnv()
})

describe('runtime BFF route auth', () => {
  it('rejects unauthenticated callers when Supabase auth is configured', async () => {
    process.env.RUNTIME_API_URL = 'https://runtime.example.test'
    process.env.RUNTIME_API_TOKEN = 'runtime-secret'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://project.supabase.co'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'anon-key'
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadRoute(null)
    const response = await route.GET(
      new NextRequest('http://app.test/api/runtime/app/state'),
      ctx(['app', 'state']),
    )

    expect(response.status).toBe(401)
    expect(await response.json()).toMatchObject({ error: 'authentification requise' })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('forwards runtime token and evaluator id for authenticated callers', async () => {
    process.env.RUNTIME_API_URL = 'https://runtime.example.test'
    process.env.RUNTIME_API_TOKEN = 'runtime-secret'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://project.supabase.co'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'anon-key'
    const fetchMock = vi.fn(async () => new Response('{"ok":true}', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadRoute({ id: 'user-123' })
    const response = await route.POST(
      new NextRequest('http://app.test/api/runtime/app/create', {
        method: 'POST',
        body: JSON.stringify({ address: '123 rue Test' }),
      }),
      ctx(['app', 'create']),
    )

    expect(response.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledOnce()
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer runtime-secret')
    expect((init.headers as Record<string, string>)['X-Evaluator-Id']).toBe('user-123')
  })

  it('keeps local placeholder Supabase config as dev passthrough', async () => {
    process.env.RUNTIME_API_URL = 'http://127.0.0.1:8796'
    process.env.NEXT_PUBLIC_SUPABASE_URL = '<project-ref>'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = '<anon-key>'
    const fetchMock = vi.fn(async () => new Response('{"ok":true}', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadRoute(null)
    const response = await route.GET(
      new NextRequest('http://app.test/api/runtime/app/state'),
      ctx(['app', 'state']),
    )

    expect(response.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledOnce()
  })

  it('rejects localhost runtime URLs in production', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    process.env.RUNTIME_API_URL = 'https://localhost:8796'
    process.env.RUNTIME_API_TOKEN = 'runtime-secret'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://project.supabase.co'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'anon-key'
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadRoute({ id: 'user-123' })
    const response = await route.GET(
      new NextRequest('http://app.test/api/runtime/app/state'),
      ctx(['app', 'state']),
    )

    expect(response.status).toBe(500)
    expect(await response.json()).toMatchObject({ error: expect.stringMatching(/localhost/) })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('rejects non-HTTPS runtime URLs in production', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    process.env.RUNTIME_API_URL = 'http://runtime.example.test'
    process.env.RUNTIME_API_TOKEN = 'runtime-secret'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://project.supabase.co'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'anon-key'
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    const route = await loadRoute({ id: 'user-123' })
    const response = await route.GET(
      new NextRequest('http://app.test/api/runtime/app/state'),
      ctx(['app', 'state']),
    )

    expect(response.status).toBe(500)
    expect(await response.json()).toMatchObject({ error: expect.stringMatching(/HTTPS/) })
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
