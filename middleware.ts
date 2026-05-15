import { NextResponse, type NextRequest } from 'next/server'

// ── AUTH MODE ──────────────────────────────────────────────────────────────────
// Option B (local-only): middleware passthrough — no auth enforced.
// To switch to Option A (Supabase enforced): set LOCAL_ONLY = false and
// configure NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local.
const LOCAL_ONLY = true

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function middleware(_request: NextRequest) {
  if (LOCAL_ONLY) return NextResponse.next()

  // Option A — Supabase auth enforcement (re-enable when LOCAL_ONLY = false)
  // Uncomment and configure when switching to production auth:
  //
  // import { createServerClient } from '@supabase/ssr'
  // const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!
  // const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  // ... (see git history for full implementation)

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
