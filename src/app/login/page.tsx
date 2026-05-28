'use client'

import { useState, useEffect } from 'react'
import { signIn } from './actions'

// signIn is a server action — we pass it directly to form action

const QUOTES = [
  {
    line: 'Le rapport, la signature, la défense — tout ce qui suit la valeur. Éval Immo s\'occupe d\'arriver à la valeur.',
    author: 'Catherine Demers, É.A.',
    firm: 'Cabinet Demers & associés',
  },
  {
    line: 'Le rôle, les comparables, la pondération, le narratif — réunis dans un seul espace de travail. Ce que je faisais en six logiciels.',
    author: 'Maxime Tremblay, É.A.',
    firm: 'Tremblay Évaluations',
  },
  {
    line: 'Les évaluateurs agréés ne devraient pas perdre leur temps avec la mise en page. Éval Immo l\'a compris.',
    author: 'Geneviève Roy, É.A.',
    firm: 'OEAQ — membre depuis 1998',
  },
]

export default function LoginPage() {
  const [quoteIdx, setQuoteIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const e = params.get('error')
    if (e) setError(decodeURIComponent(e))
  }, [])

  useEffect(() => {
    const t = setInterval(() => setQuoteIdx(i => (i + 1) % QUOTES.length), 8000)
    return () => clearInterval(t)
  }, [])

  const q = QUOTES[quoteIdx]

  return (
    <div
      className="min-h-screen flex"
      style={{ background: 'var(--paper)', fontFamily: 'var(--font-sans)' }}
    >
      {/* Left — brand panel */}
      <aside
        className="hidden md:flex flex-col justify-between w-1/2 p-12"
        style={{ background: 'var(--ink)', color: 'var(--paper-hi)' }}
      >
        {/* Top: wordmark */}
        <div>
          <div
            className="text-[38px] font-medium leading-[1.1]"
            style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.015em' }}
          >
            Éval <em style={{ color: 'rgba(125,164,214,1)' }}>Immo</em>
          </div>
          <div className="text-[13px] mt-1" style={{ color: 'rgba(243,237,220,.55)' }}>
            Évaluateurs agréés — Québec
          </div>
        </div>

        {/* Mid: rotating quote */}
        <div>
          <div
            className="text-[120px] leading-none mb-2 select-none"
            style={{ color: 'rgba(125,164,214,.12)', fontFamily: 'var(--font-serif)', lineHeight: 1 }}
            aria-hidden="true"
          >
            "
          </div>
          <p
            className="text-[22px] font-medium leading-[1.4] mb-6"
            style={{ fontFamily: 'var(--font-serif)', fontStyle: 'italic', color: 'var(--paper-hi)' }}
          >
            {q.line}
          </p>
          <div>
            <div className="text-[13.5px] font-medium" style={{ color: 'var(--paper-hi)' }}>{q.author}</div>
            <div className="text-[12.5px]" style={{ color: 'rgba(243,237,220,.55)' }}>{q.firm}</div>
          </div>
          {/* Dot nav */}
          <div className="flex gap-2 mt-5">
            {QUOTES.map((_, i) => (
              <button
                key={i}
                onClick={() => setQuoteIdx(i)}
                aria-label={`Citation ${i + 1}`}
                className="border-none cursor-pointer transition-all"
                style={{
                  width: i === quoteIdx ? '20px' : '6px',
                  height: '6px',
                  borderRadius: '999px',
                  background: i === quoteIdx ? 'var(--paper-hi)' : 'rgba(243,237,220,.3)',
                  padding: 0,
                }}
              />
            ))}
          </div>
        </div>

        {/* Bottom: compliance seal */}
        <div
          className="rounded-[var(--r-lg)] p-4 flex items-start gap-4"
          style={{ background: 'rgba(255,255,255,.10)', border: '1px solid rgba(255,255,255,.15)' }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-[11px] font-bold border-2 border-[rgba(255,255,255,.4)]"
            style={{ color: 'var(--paper-hi)' }}
          >
            É.A.
          </div>
          <div className="text-[12px]" style={{ color: 'rgba(243,237,220,.70)', lineHeight: 1.6 }}>
            Conforme aux normes de l'<strong style={{ color: 'var(--paper-hi)' }}>Ordre des évaluateurs agréés du Québec</strong>
            <br />
            Hébergement conforme à la <strong style={{ color: 'var(--paper-hi)' }}>Loi 25 — protection des renseignements personnels</strong>
          </div>
        </div>
      </aside>

      {/* Right — form panel */}
      <main
        className="flex flex-col w-full md:w-1/2 min-h-screen"
        style={{ background: 'var(--paper-hi)' }}
      >
        <div className="flex justify-end p-6">
          <a
            href="/dossiers"
            className="text-[13px] px-3 py-1.5 rounded-[var(--r-pill)] border border-[var(--rule)] no-underline transition-colors"
            style={{ color: 'var(--navy)', fontFamily: 'var(--font-sans)' }}
          >
            Aperçu de l'application →
          </a>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center px-8">
          <div className="w-full max-w-[400px]">
            <div className="eyebrow mb-3">Bon retour</div>
            <h1
              className="text-[36px] font-medium mb-6"
              style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.015em', color: 'var(--ink)' }}
            >
              Se connecter
            </h1>

            {error && (
              <div
                className="rounded-[var(--r-md)] px-4 py-3 text-[13px] mb-4"
                style={{ color: 'var(--oxblood)', background: 'rgba(138,48,48,.08)', border: '1px solid rgba(138,48,48,.15)' }}
              >
                {error}
              </div>
            )}

            <form action={signIn} className="flex flex-col gap-4">
              <div>
                <label
                  htmlFor="email"
                  className="block text-[12px] font-medium mb-1.5"
                  style={{ color: 'var(--ink-mute)' }}
                >
                  Adresse e-mail
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="vous@exemple.com"
                  className="field"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-[12px] font-medium mb-1.5"
                  style={{ color: 'var(--ink-mute)' }}
                >
                  Mot de passe
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  className="field"
                />
              </div>

              <button
                type="submit"
                className="btn accent btn-full mt-1"
              >
                Se connecter
              </button>
            </form>
          </div>
        </div>

        <div
          className="text-center p-6 text-[11px]"
          style={{ color: 'var(--ink-faint)' }}
        >
          © 2026 Éval Immo inc. · Confidentialité · Conditions · Montréal · Québec
        </div>
      </main>
    </div>
  )
}
