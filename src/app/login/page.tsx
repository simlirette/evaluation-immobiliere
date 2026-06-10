'use client'

/* Login — port 1:1 du design handoff (login.jsx + login.css).
   Connexion courriel/mot de passe branchée sur le server action Supabase ;
   SSO Microsoft et inscription OEAQ = visuels (backend à venir). */

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Icon } from '@/components/shared/Icon'
import { signIn } from './actions'
import './login.css'

const QUOTES = [
  { line: "Le rapport, la signature, la défense — tout ce qui suit la valeur. Éval Immo s'occupe d'arriver à la valeur.", author: 'Catherine Demers, É.A.', firm: 'Cabinet Demers & associés' },
  { line: 'Le rôle, les comparables, la pondération, le narratif — réunis dans un seul espace de travail. Ce que je faisais en six logiciels.', author: 'Maxime Tremblay, É.A.', firm: 'Tremblay Évaluations' },
  { line: 'Les évaluateurs agréés ne devraient pas perdre leur temps avec la mise en page. Éval Immo l\'a compris.', author: 'Geneviève Roy, É.A.', firm: 'OEAQ — membre depuis 1998' },
]

type Mode = 'signin' | 'signup' | 'sent'

export default function LoginPage() {
  return (
    <Suspense>
      <LoginInner/>
    </Suspense>
  )
}

function LoginInner() {
  const [mode, setMode] = useState<Mode>('signin')
  const [quoteIdx, setQuoteIdx] = useState(0)
  const [sentEmail, setSentEmail] = useState('')

  useEffect(() => {
    const t = setInterval(() => setQuoteIdx(i => (i + 1) % QUOTES.length), 8000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="login">
      {/* Brand panel */}
      <aside className="login-brand">
        <div className="lb-top">
          <div className="lb-mark">
            Éval&nbsp;<em>Immo</em>
          </div>
          <div className="lb-tag">Évaluateurs agréés — Québec</div>
        </div>

        <div className="lb-mid">
          <div className="lb-quote">
            <div className="lb-marks">“</div>
            <p className="lb-line">{QUOTES[quoteIdx].line}</p>
            <div className="lb-attribution">
              <div className="lb-author">{QUOTES[quoteIdx].author}</div>
              <div className="lb-firm">{QUOTES[quoteIdx].firm}</div>
            </div>
          </div>
          <div className="lb-quote-dots">
            {QUOTES.map((_, i) => (
              <button
                key={i}
                className={`lbd-dot ${i === quoteIdx ? 'active' : ''}`}
                onClick={() => setQuoteIdx(i)}
                aria-label={`Citation ${i + 1}`}
              />
            ))}
          </div>
        </div>

        <div className="lb-foot">
          <div className="lb-seal">
            <div className="lbs-ring">É.A.</div>
            <div className="lbs-text">
              <div>Conforme aux normes de l&apos;</div>
              <div className="lbs-strong">Ordre des évaluateurs agréés du Québec</div>
              <div className="lbs-rule"/>
              <div>Hébergement conforme à la</div>
              <div className="lbs-strong">Loi 25 — protection des renseignements personnels</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Form panel */}
      <main className="login-main">
        <div className="lm-corner">
          <a href="/dossiers" className="corner-link">
            Aperçu de l&apos;application <ChevronR/>
          </a>
        </div>

        <div className="lm-content">
          {mode === 'signin' && <SignIn onSwitch={() => setMode('signup')}/>}
          {mode === 'signup' && (
            <SignUp
              onSwitch={() => setMode('signin')}
              onSent={email => { setSentEmail(email); setMode('sent') }}
            />
          )}
          {mode === 'sent' && <Sent email={sentEmail} onBack={() => setMode('signin')}/>}

          <div className="lm-foot">
            <span>© 2026 Éval Immo inc.</span>
            <span className="dot-sep">·</span>
            <a>Confidentialité</a>
            <span className="dot-sep">·</span>
            <a>Conditions</a>
            <span className="dot-sep">·</span>
            <span>Montréal · Québec</span>
          </div>
        </div>
      </main>
    </div>
  )
}

function ChevronR() {
  return (
    <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 4l4 4-4 4"/>
    </svg>
  )
}

/* ── SIGN IN — branché sur le server action Supabase ── */
function SignIn({ onSwitch }: { onSwitch: () => void }) {
  const searchParams = useSearchParams()
  const error = searchParams.get('error')
  const [remember, setRemember] = useState(true)
  const [showPw, setShowPw] = useState(false)

  return (
    <form className="auth-form" action={signIn}>
      <div className="af-eyebrow">Bon retour</div>
      <h1 className="af-title">Se connecter</h1>
      <p className="af-sub">Reprenez vos dossiers là où vous les avez laissés.</p>

      {error && (
        <div
          style={{
            color: 'var(--oxblood)',
            background: 'rgba(138,48,48,.08)',
            border: '1px solid rgba(138,48,48,.15)',
            borderRadius: 'var(--r-md)',
            padding: '10px 14px',
            fontSize: 13,
            marginBottom: 4,
          }}
        >
          {decodeURIComponent(error)}
        </div>
      )}

      <div className="af-sso">
        <button type="button" className="sso-btn" title="Bientôt disponible">
          <SsoMicrosoft/>
          <span>Continuer avec Microsoft</span>
        </button>
      </div>

      <div className="af-divider"><span>ou</span></div>

      <div className="af-fields">
        <label className="af-field">
          <span className="af-k">Courriel professionnel</span>
          <input
            type="email"
            name="email"
            placeholder="vous@cabinet.ca"
            autoComplete="email"
            required
          />
        </label>
        <label className="af-field">
          <span className="af-k">
            Mot de passe
            <a className="af-forgot">Mot de passe oublié ?</a>
          </span>
          <div className="af-input-wrap">
            <input
              type={showPw ? 'text' : 'password'}
              name="password"
              placeholder="••••••••••"
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              className="af-toggle"
              onClick={() => setShowPw(s => !s)}
              aria-label={showPw ? 'Masquer' : 'Afficher'}>
              {showPw ? 'Masquer' : 'Afficher'}
            </button>
          </div>
        </label>
      </div>

      <label className="af-check">
        <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)}/>
        <span>Garder ma session active 14 jours</span>
      </label>

      <button type="submit" className="btn accent af-submit">Se connecter</button>

      <div className="af-switch">
        Pas encore de compte ?
        <a onClick={onSwitch}>S&apos;inscrire via votre firme</a>
      </div>
    </form>
  )
}

/* ── SIGN UP ── */
function SignUp({ onSwitch, onSent }: { onSwitch: () => void; onSent: (email: string) => void }) {
  const [data, setData] = useState({
    nom: '', prenom: '', email: '', oeaq: '', firm: '', accept: false,
  })

  function up<K extends keyof typeof data>(field: K, v: typeof data[K]) {
    setData(d => ({ ...d, [field]: v }))
  }
  const canSubmit = data.nom && data.prenom && data.email && data.oeaq && data.firm && data.accept

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    onSent(data.email)
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="af-eyebrow">Bienvenue</div>
      <h1 className="af-title">Créer votre cabinet</h1>
      <p className="af-sub">Quelques instants pour vérifier votre adhésion à l&apos;OEAQ.</p>

      <div className="af-fields">
        <div className="af-row-2">
          <label className="af-field">
            <span className="af-k">Prénom</span>
            <input type="text" value={data.prenom} onChange={e => up('prenom', e.target.value)}/>
          </label>
          <label className="af-field">
            <span className="af-k">Nom</span>
            <input type="text" value={data.nom} onChange={e => up('nom', e.target.value)}/>
          </label>
        </div>

        <label className="af-field">
          <span className="af-k">Courriel professionnel</span>
          <input type="email" value={data.email} onChange={e => up('email', e.target.value)} placeholder="vous@cabinet.ca"/>
        </label>

        <div className="af-row-2">
          <label className="af-field">
            <span className="af-k">N° de membre OEAQ</span>
            <input type="text" value={data.oeaq} onChange={e => up('oeaq', e.target.value)} placeholder="ex. 4218" inputMode="numeric"/>
          </label>
          <label className="af-field">
            <span className="af-k">Cabinet</span>
            <input type="text" value={data.firm} onChange={e => up('firm', e.target.value)} placeholder="ex. Tremblay Évaluations"/>
          </label>
        </div>
      </div>

      <label className="af-check">
        <input type="checkbox" checked={data.accept} onChange={e => up('accept', e.target.checked)}/>
        <span>
          J&apos;accepte les <a>conditions d&apos;utilisation</a> et la <a>politique de confidentialité</a>,
          et je confirme que mon adhésion à l&apos;OEAQ est en règle.
        </span>
      </label>

      <button type="submit" className="btn accent af-submit" disabled={!canSubmit}>
        Vérifier auprès de l&apos;OEAQ
      </button>

      <div className="af-switch">
        Déjà un compte ?
        <a onClick={onSwitch}>Se connecter</a>
      </div>
    </form>
  )
}

/* ── SENT (post-inscription) ── */
function Sent({ email, onBack }: { email: string; onBack: () => void }) {
  return (
    <div className="auth-form auth-sent">
      <div className="sent-seal">
        <Icon.Check/>
      </div>
      <h1 className="af-title">Vérification en cours</h1>
      <p className="af-sub">
        Nous avons envoyé un courriel de confirmation et nous vérifions votre numéro OEAQ
        auprès du registre. Cela prend habituellement <b>quelques minutes</b>.
      </p>

      <div className="sent-steps">
        <div className="ss-row done">
          <div className="ss-dot"><Icon.Check/></div>
          <div className="ss-text">Courriel envoyé à <b>{email || 'votre adresse'}</b></div>
        </div>
        <div className="ss-row active">
          <div className="ss-dot ss-pulse"/>
          <div className="ss-text">Vérification de l&apos;adhésion OEAQ <span className="ss-meta">— en cours</span></div>
        </div>
        <div className="ss-row">
          <div className="ss-dot"/>
          <div className="ss-text">Activation de votre cabinet</div>
        </div>
      </div>

      <button className="btn secondary af-submit" onClick={onBack}>
        Retour à la connexion
      </button>
    </div>
  )
}

/* ── SSO Microsoft ── */
function SsoMicrosoft() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <rect x="2"    y="2"    width="9.5" height="9.5" fill="#F35325"/>
      <rect x="12.5" y="2"    width="9.5" height="9.5" fill="#81BC06"/>
      <rect x="2"    y="12.5" width="9.5" height="9.5" fill="#05A6F0"/>
      <rect x="12.5" y="12.5" width="9.5" height="9.5" fill="#FFBA08"/>
    </svg>
  )
}
