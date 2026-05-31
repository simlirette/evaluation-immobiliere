import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

// Allow up to 120s — pipeline runs include LLM steps + optional Vision ingestion
export const maxDuration = 120

const RUNTIME_URL = (process.env.RUNTIME_API_URL || 'http://127.0.0.1:8796').replace(/\/$/, '')
const RUNTIME_TOKEN = process.env.RUNTIME_API_TOKEN || ''
// Default timeout: 30s for reads, 120s for pipeline runs (ingestion + 7 LLM steps)
const TIMEOUT_MS = 30_000
const TIMEOUT_PIPELINE_MS = 120_000
const PIPELINE_PATHS = new Set(['/app/demo', '/app/create', '/app/state', '/app/package', '/app/review/validate'])
const IS_PROD = process.env.NODE_ENV === 'production'
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? ''
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
const AUTH_ENABLED =
  Boolean(SUPABASE_URL) &&
  !SUPABASE_URL.includes('<project-ref>') &&
  Boolean(SUPABASE_ANON_KEY) &&
  !SUPABASE_ANON_KEY.includes('<anon-key>')

function isLocalRuntimeUrl(url: URL): boolean {
  const host = url.hostname.replace(/^\[|\]$/g, '').toLowerCase()
  return ['localhost', '127.0.0.1', '0.0.0.0', '::1'].includes(host)
}

function runtimeConfigError(): string | null {
  if (!IS_PROD) return null

  let parsedRuntimeUrl: URL
  try {
    parsedRuntimeUrl = new URL(RUNTIME_URL)
  } catch {
    return '[BFF] RUNTIME_API_URL invalide en production - configurer URL Railway absolue.'
  }

  if (parsedRuntimeUrl.protocol !== 'https:') {
    return '[BFF] RUNTIME_API_URL doit etre HTTPS en production - configurer URL Railway publique.'
  }
  if (isLocalRuntimeUrl(parsedRuntimeUrl)) {
    return '[BFF] RUNTIME_API_URL pointe vers localhost en production - configurer la variable Railway.'
  }
  if (!RUNTIME_TOKEN) {
    return '[BFF] RUNTIME_API_TOKEN absent en production - requetes runtime refusees.'
  }
  if (!AUTH_ENABLED) {
    return '[BFF] Supabase auth absent en production - configurer NEXT_PUBLIC_SUPABASE_URL et NEXT_PUBLIC_SUPABASE_ANON_KEY.'
  }

  return null
}

type Ctx = { params: Promise<{ path: string[] }> }

async function authenticatedUserId(): Promise<string | null> {
  if (!AUTH_ENABLED) return null
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  return user?.id ?? null
}

async function proxy(req: NextRequest, ctx: Ctx, method: 'GET' | 'POST'): Promise<Response> {
  const configError = runtimeConfigError()
  if (configError) {
    return NextResponse.json({ error: configError }, { status: 500 })
  }

  const { path } = await ctx.params
  const forwardPath = '/' + path.join('/')
  const search = req.nextUrl.search

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (RUNTIME_TOKEN) headers['Authorization'] = `Bearer ${RUNTIME_TOKEN}`

  // Forward authenticated user identity to runtime for audit and ownership checks.
  try {
    const userId = await authenticatedUserId()
    if (AUTH_ENABLED && !userId) {
      return NextResponse.json({ error: 'authentification requise' }, { status: 401 })
    }
    if (userId) headers['X-Evaluator-Id'] = userId
  } catch {
    if (AUTH_ENABLED) {
      return NextResponse.json({ error: 'authentification requise' }, { status: 401 })
    }
  }

  const timeout = PIPELINE_PATHS.has(forwardPath) ? TIMEOUT_PIPELINE_MS : TIMEOUT_MS
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  try {
    const body = method === 'POST' ? await req.text() : undefined
    const res = await fetch(`${RUNTIME_URL}${forwardPath}${search}`, {
      method,
      headers,
      body,
      signal: controller.signal,
    })
    clearTimeout(timer)

    // SSE — pipe body directly, do not buffer
    const contentType = res.headers.get('Content-Type') ?? ''
    if (contentType.includes('text/event-stream')) {
      return new Response(res.body, {
        status: res.status,
        headers: {
          'Content-Type': 'text/event-stream; charset=utf-8',
          'Cache-Control': 'no-cache',
          'X-Accel-Buffering': 'no',
        },
      })
    }

    // Binary responses (ZIP downloads) — pipe body directly
    const ct = res.headers.get('Content-Type') ?? ''
    if (ct.includes('application/zip') || ct.includes('application/octet-stream')) {
      const disposition = res.headers.get('Content-Disposition') ?? ''
      return new Response(res.body, {
        status: res.status,
        headers: {
          'Content-Type': ct,
          ...(disposition ? { 'Content-Disposition': disposition } : {}),
        },
      })
    }

    const text = await res.text()
    return new NextResponse(text, {
      status: res.status,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    })
  } catch (err) {
    clearTimeout(timer)
    if ((err as Error).name === 'AbortError') {
      return NextResponse.json({ error: 'Runtime API timeout' }, { status: 504 })
    }
    return NextResponse.json({ error: 'Runtime API inaccessible' }, { status: 502 })
  }
}

export async function GET(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx, 'GET')
}

export async function POST(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx, 'POST')
}
