import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const RUNTIME_URL = (process.env.RUNTIME_API_URL || 'http://127.0.0.1:8796').replace(/\/$/, '')
const RUNTIME_TOKEN = process.env.RUNTIME_API_TOKEN || ''
const TIMEOUT_MS = 30_000
const IS_PROD = process.env.NODE_ENV === 'production'

// Catch misconfigured deployments before they silently fail
if (IS_PROD && RUNTIME_URL.includes('127.0.0.1')) {
  console.error('[BFF] RUNTIME_API_URL pointe vers localhost en production — configurer la variable Railway.')
}
if (IS_PROD && !RUNTIME_TOKEN) {
  console.warn('[BFF] RUNTIME_API_TOKEN absent en production — les requêtes runtime ne seront pas authentifiées.')
}

type Ctx = { params: Promise<{ path: string[] }> }

async function proxy(req: NextRequest, ctx: Ctx, method: 'GET' | 'POST'): Promise<NextResponse> {
  const { path } = await ctx.params
  const forwardPath = '/' + path.join('/')
  const search = req.nextUrl.search

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (RUNTIME_TOKEN) headers['Authorization'] = `Bearer ${RUNTIME_TOKEN}`

  // Forward authenticated user identity to runtime for audit logging
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (user) headers['X-Evaluator-Id'] = user.id
  } catch {
    // Supabase not configured — local dev, skip
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const body = method === 'POST' ? await req.text() : undefined
    const res = await fetch(`${RUNTIME_URL}${forwardPath}${search}`, {
      method,
      headers,
      body,
      signal: controller.signal,
    })
    clearTimeout(timer)

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
