# Archived - Supabase Auth (V2) Implementation Plan

> Archived on 2026-05-08 during the full project audit. This plan was mostly executed, then superseded by the runtime-backed V1 architecture where `middleware.ts` is intentionally disabled and business data is read from the Python runtime API. Keep it as historical context only; do not use it as the active implementation plan.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add invite-only email+password auth — login page, middleware route protection, sign-out wired in sidebar.

**Architecture:** Supabase SSR (`@supabase/ssr`) with cookie-based sessions. Browser + server clients already exist at `src/lib/supabase/`. Middleware reads the session cookie on every request; unauthenticated requests to protected routes redirect to `/login`. Login uses a Server Action to call `supabase.auth.signInWithPassword`. No public signup — admin creates users via Supabase dashboard.

**Tech Stack:** Next.js 16 App Router, TypeScript, Tailwind v4, `@supabase/ssr` (already installed), Server Actions.

**Assumptions:**
- `.env.local` exists with placeholder values — user must fill `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` before running.
- "Disable sign ups" is toggled in Supabase dashboard — this plan does NOT enforce that; it's a dashboard setting.
- No email confirmation flow needed at launch — admin creates users directly, no confirm-email step.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `src/app/auth/callback/route.ts` | Create | Exchanges Supabase code for session (required for magic-link / email-confirm flows even if not used now) |
| `src/app/login/page.tsx` | Create | Login form — email + password, liquid glass style, Server Action sign-in |
| `src/app/login/actions.ts` | Create | Server Action: `signIn(formData)` — calls supabase.auth.signInWithPassword, redirects |
| `middleware.ts` | Create | Protects `/dossier/*` and `/dossiers` — redirect to `/login` if no session |
| `src/hooks/useUser.ts` | Create | Client hook — returns current user from Supabase session |
| `src/app/dossier/[id]/page.tsx` | Modify | Replace stub `onSignOut` with real Supabase `signOut()` + redirect |

---

### Task 1: Auth callback route

**Files:**
- Create: `src/app/auth/callback/route.ts`

**Does NOT cover:** Magic link flows, OAuth. This route is a required Supabase SSR scaffolding step even for password-only auth.

- [ ] **Step 1: Create the route handler**

```typescript
// src/app/auth/callback/route.ts
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dossiers'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`)
}
```

- [ ] **Step 2: Verify file created**

Run: `ls src/app/auth/callback/route.ts`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add src/app/auth/callback/route.ts
git commit -m "feat(auth): add Supabase auth callback route handler"
```

---

### Task 2: Login page + Server Action

**Files:**
- Create: `src/app/login/actions.ts`
- Create: `src/app/login/page.tsx`

**Does NOT cover:** Sign-up, password reset, magic link. Validation is minimal (form field required — no zod).

- [ ] **Step 1: Create Server Action**

```typescript
// src/app/login/actions.ts
'use server'

import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export async function signIn(formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string

  const supabase = await createClient()
  const { error } = await supabase.auth.signInWithPassword({ email, password })

  if (error) {
    redirect(`/login?error=${encodeURIComponent(error.message)}`)
  }

  redirect('/dossiers')
}
```

- [ ] **Step 2: Create login page**

```tsx
// src/app/login/page.tsx
import { signIn } from './actions'
import { APP_WORDMARK } from '@/constants/app'

interface Props {
  searchParams: Promise<{ error?: string }>
}

export default async function LoginPage({ searchParams }: Props) {
  const { error } = await searchParams

  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'var(--color-bg)' }}
    >
      <div
        className="w-full max-w-[360px] rounded-[18px] px-8 py-10 flex flex-col gap-7"
        style={{
          background: 'linear-gradient(165deg, rgba(238,232,222,.80) 0%, rgba(228,222,212,.70) 100%)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          border: '1px solid var(--glass-border)',
          boxShadow: 'var(--shadow-glass)',
        }}
      >
        {/* Wordmark */}
        <div className="text-center">
          <span
            className="font-serif text-[28px] font-medium tracking-[-0.02em] text-[#1a1916]"
          >
            {APP_WORDMARK}
          </span>
          <p className="mt-1 text-[13px] text-[#8a8780]">Connexion à votre espace</p>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-[10px] px-4 py-3 text-[13px] text-red-700 bg-red-50/80 border border-red-200/60">
            {decodeURIComponent(error)}
          </div>
        )}

        {/* Form */}
        <form action={signIn} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-[12px] text-[#8a8780] font-medium">
              Adresse e-mail
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              placeholder="vous@exemple.com"
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow placeholder:text-[#b5b2ac]"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
              }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-[12px] text-[#8a8780] font-medium">
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              className="w-full rounded-[10px] px-4 py-2.5 text-[14px] text-[#1a1916] outline-none transition-shadow placeholder:text-[#b5b2ac]"
              style={{
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
              }}
            />
          </div>

          <button
            type="submit"
            className="mt-1 w-full rounded-[10px] py-2.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 active:opacity-80"
            style={{ background: '#334155' }}
          >
            Se connecter
          </button>
        </form>
      </div>
    </main>
  )
}
```

- [ ] **Step 3: Verify build**

Run: `cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20`
Expected: no TypeScript errors mentioning login or actions

- [ ] **Step 4: Commit**

```bash
git add src/app/login/actions.ts src/app/login/page.tsx
git commit -m "feat(auth): add login page with email+password Server Action"
```

---

### Task 3: Middleware — route protection

**Files:**
- Create: `middleware.ts` (project root, next to `package.json`)

**Does NOT cover:** Role-based access control, per-user data isolation. Middleware only checks "is there a session?" — not which user.

- [ ] **Step 1: Create middleware**

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session — required to keep cookie alive
  const { data: { user } } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl
  const isProtected = pathname.startsWith('/dossier') || pathname.startsWith('/dossiers')

  if (isProtected && !user) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Redirect logged-in user away from login page
  if (pathname === '/login' && user) {
    const url = request.nextUrl.clone()
    url.pathname = '/dossiers'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

- [ ] **Step 2: Verify middleware file is at project root**

Run: `ls middleware.ts`
Expected: file exists (not inside src/)

- [ ] **Step 3: Commit**

```bash
git add middleware.ts
git commit -m "feat(auth): add middleware protecting /dossiers and /dossier/* routes"
```

---

### Task 4: useUser hook + real sign-out wiring

**Files:**
- Create: `src/hooks/useUser.ts`
- Modify: `src/app/dossier/[id]/page.tsx`

**Does NOT cover:** Session refresh, user profile data beyond email. `useUser` returns the Supabase `User` object or `null`.

- [ ] **Step 1: Create useUser hook**

```typescript
// src/hooks/useUser.ts
'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

export function useUser() {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const supabase = createClient()

    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  return user
}
```

- [ ] **Step 2: Wire real sign-out in DossierShellInner**

In `src/app/dossier/[id]/page.tsx`, replace the stub `onSignOut` with a real sign-out function. Add this import at the top:

```typescript
import { createClient } from '@/lib/supabase/client'
```

Replace the `onSignOut` prop passed to `<Sidebar>`:

Old:
```tsx
onSignOut={() => router.push('/login')}
```

New:
```tsx
onSignOut={async () => {
  const supabase = createClient()
  await supabase.auth.signOut()
  router.push('/login')
}}
```

- [ ] **Step 3: Verify build**

Run: `cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20`
Expected: `✓ Compiled successfully` — no errors

- [ ] **Step 4: Commit**

```bash
git add src/hooks/useUser.ts src/app/dossier/[id]/page.tsx
git commit -m "feat(auth): add useUser hook and wire real Supabase sign-out in sidebar"
```

---

## Post-execution checklist

Before testing end-to-end, user must:

1. Fill `.env.local` with real Supabase credentials:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
   ```

2. In Supabase dashboard → Authentication → Settings → **Disable sign ups** (invite-only).

3. Create a test user: Supabase dashboard → Authentication → Users → **Invite user**.

4. Start dev server: `npm run dev`, navigate to `http://localhost:3000` → should redirect to `/login`.

5. Log in with test credentials → should land on `/dossiers`.

6. Click Déconnexion → should return to `/login`.
