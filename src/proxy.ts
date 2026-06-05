import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? ''
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''

// Auth active uniquement quand les vraies credentials Supabase sont configurées.
// Placeholders → passthrough (dev local sans Supabase).
const AUTH_ENABLED =
  Boolean(SUPABASE_URL) &&
  !SUPABASE_URL.includes('<project-ref>') &&
  Boolean(SUPABASE_ANON_KEY) &&
  !SUPABASE_ANON_KEY.includes('<anon-key>')

const PUBLIC_PATHS = ['/login', '/auth/']
const ADMIN_PATHS = ['/admin']

export async function proxy(request: NextRequest) {
  if (!AUTH_ENABLED) return NextResponse.next()

  const { pathname } = request.nextUrl
  const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p))

  let response = NextResponse.next({ request })

  const supabase = createServerClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
        response = NextResponse.next({ request })
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options)
        )
      },
    },
  })

  // getUser() valide la session côté serveur (pas seulement le cookie)
  const { data: { user } } = await supabase.auth.getUser()

  if (!user && !isPublic) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('next', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (user && pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/dossiers', request.url))
  }

  // Routes /admin/* — réservées aux bureau_admin
  if (user && ADMIN_PATHS.some(p => pathname.startsWith(p))) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('role')
      .eq('id', user.id)
      .single()

    if (!profile || profile.role !== 'bureau_admin') {
      return NextResponse.redirect(new URL('/dossiers', request.url))
    }
  }

  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
