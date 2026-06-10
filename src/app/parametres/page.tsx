'use client'

/* Paramètres — port 1:1 du design handoff (parametres.jsx + parametres-sections.jsx).
   Profil branché sur le profil É.A. réel (nom, n° OEAQ) ; le reste = copie design. */

import { useState, useEffect, Suspense, type ReactNode } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { Icon } from '@/components/shared/Icon'
import { fetchEvaluateurProfile, type EvaluateurProfile } from '@/lib/runtime-api'
import { createClient } from '@/lib/supabase/client'
import './parametres.css'

const SECTIONS = [
  { id: 'profil',       label: 'Profil',       icon: 'user' },
  { id: 'cabinet',      label: 'Cabinet',      icon: 'building' },
  { id: 'membres',      label: 'Membres',      icon: 'users' },
  { id: 'integrations', label: 'Intégrations', icon: 'plug' },
  { id: 'utilisation',  label: 'Utilisation',  icon: 'chart' },
  { id: 'securite',     label: 'Sécurité',     icon: 'lock' },
  { id: 'preferences',  label: 'Préférences',  icon: 'settings' },
] as const

export default function ParametresPage() {
  return (
    <Suspense>
      <ParametresInner/>
    </Suspense>
  )
}

function ParametresInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const initial = searchParams.get('section') || 'profil'
  const [section, setSection] = useState(initial)
  const [profile, setProfile] = useState<EvaluateurProfile | null>(null)

  useEffect(() => {
    fetchEvaluateurProfile().then(setProfile).catch(() => undefined)
  }, [])

  function pickSection(id: string) {
    setSection(id)
    const u = new URL(window.location.href)
    u.searchParams.set('section', id)
    history.replaceState(null, '', u)
  }

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div className="app">
      <Sidebar onSignOut={handleSignOut} />

      <div className="main">
        <div className="topbar param-topbar">
          <div className="pagehead param-head">
            <div>
              <h1>Paramètres</h1>
              <div className="subtitle">
                Personnalisez votre profil, votre cabinet, vos intégrations et la sécurité.
              </div>
            </div>
          </div>
        </div>

        <div className="param-body">
          {/* Sub-nav */}
          <aside className="param-nav">
            {SECTIONS.map(s => (
              <button
                key={s.id}
                className={`pn-item ${section === s.id ? 'active' : ''}`}
                onClick={() => pickSection(s.id)}>
                <SettingsIcon name={s.icon}/>
                <span>{s.label}</span>
              </button>
            ))}
          </aside>

          {/* Section */}
          <section className="param-main">
            {section === 'profil'       && <SectionProfil profile={profile}/>}
            {section === 'cabinet'      && <SectionCabinet/>}
            {section === 'membres'      && <SectionMembres/>}
            {section === 'integrations' && <SectionIntegrations/>}
            {section === 'utilisation'  && <SectionUtilisation/>}
            {section === 'securite'     && <SectionSecurite/>}
            {section === 'preferences'  && <SectionPreferences/>}
          </section>
        </div>
      </div>
    </div>
  )
}

function SettingsIcon({ name }: { name: string }) {
  const common = { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.5, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  switch (name) {
    case 'user':     return <svg {...common}><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></svg>
    case 'building': return <svg {...common}><path d="M5 21V5l8-2v18M5 21h14v-9l-6-2"/><path d="M9 8h1M9 12h1M9 16h1M15 13h1M15 17h1"/></svg>
    case 'users':    return <svg {...common}><circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.4"/><path d="M3 20a6 6 0 0 1 12 0M14 20a4.5 4.5 0 0 1 8 0"/></svg>
    case 'plug':     return <svg {...common}><path d="M9 3v6M15 3v6M7 9h10v3a5 5 0 0 1-5 5v4"/></svg>
    case 'chart':    return <svg {...common}><path d="M4 20V8M10 20V4M16 20v-9M22 20H2"/></svg>
    case 'lock':     return <svg {...common}><rect x="4.5" y="11" width="15" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>
    case 'settings': return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>
    default: return null
  }
}

/* ── Helpers ── */
function PCard({ title, desc, action, children, tight }: {
  title: string; desc?: string; action?: ReactNode; children: ReactNode; tight?: boolean
}) {
  return (
    <section className={`param-card ${tight ? 'tight' : ''}`}>
      <div className="pc-head">
        <div>
          <h3>{title}</h3>
          {desc && <div className="pc-desc">{desc}</div>}
        </div>
        {action}
      </div>
      <div className="pc-body">{children}</div>
    </section>
  )
}

function PRow({ k, v, muted }: { k: string; v: ReactNode; muted?: boolean }) {
  return (
    <div className="pc-row">
      <div className="pc-k">{k}</div>
      <div className={`pc-v ${muted ? 'muted' : ''}`}>{v}</div>
    </div>
  )
}

function PToggle({ on, onChange, label, desc }: {
  on: boolean; onChange: (v: boolean) => void; label: string; desc?: string
}) {
  return (
    <label className="pc-toggle">
      <div className="ptg-text">
        <div className="ptg-label">{label}</div>
        {desc && <div className="ptg-desc">{desc}</div>}
      </div>
      <span className={`switch ${on ? 'on' : ''}`} onClick={() => onChange(!on)}>
        <span className="switch-knob"/>
      </span>
    </label>
  )
}

function initials(name: string): string {
  return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || 'ÉA'
}

/* ── PROFIL ── */
function SectionProfil({ profile }: { profile: EvaluateurProfile | null }) {
  const name = profile?.nom_ea || 'Évaluateur agréé'
  const oeaq = profile?.no_permis_oeaq || '—'
  return (
    <>
      <div className="param-hero">
        <div className="ph-avatar">{initials(name)}</div>
        <div className="ph-info">
          <h2>{name}</h2>
          <div className="ph-meta">
            <span className="ph-pill"><Icon.Seal/> É.A. — OEAQ <span className="numeric">{oeaq}</span></span>
          </div>
        </div>
        <button className="btn secondary">Modifier la photo</button>
      </div>

      <PCard title="Identité" action={<button className="btn ghost">Modifier</button>}>
        <PRow k="Nom complet" v={name}/>
        <PRow k="Titre"   v="Évaluateur agréé"/>
        <PRow k="Langues" v="Français · Anglais"/>
      </PCard>

      <PCard
        title="Adhésion professionnelle"
        desc="Vérifiée auprès du registre de l'OEAQ. Synchronisée chaque mois."
        action={<span className="pc-status ok"><Icon.Check/> En règle</span>}>
        <PRow k="N° de membre OEAQ" v={<span className="numeric">{oeaq}</span>}/>
        <PRow k="Champs de pratique" v="Résidentiel · Multilogements · Commercial léger"/>
      </PCard>

      <PCard
        title="Signature manuscrite"
        desc="Apparaît sur tous les rapports finaux et les certificats d'évaluation."
        action={<button className="btn ghost">Refaire</button>}>
        <div className="signature-preview">
          <svg viewBox="0 0 320 80" preserveAspectRatio="none">
            <path d="M10,55 C30,20 60,75 90,40 S140,15 170,50 S230,75 270,30 C290,10 310,40 315,60"
              stroke="var(--ink)" strokeWidth="1.8" fill="none" strokeLinecap="round"/>
          </svg>
          <div className="sig-meta">
            <div>{name}, É.A.</div>
            <div>OEAQ {oeaq}</div>
          </div>
        </div>
      </PCard>
    </>
  )
}

/* ── CABINET ── */
function SectionCabinet() {
  return (
    <>
      <PCard title="Identification" action={<button className="btn ghost">Modifier</button>}>
        <PRow k="Raison sociale" v="Tremblay Évaluations inc."/>
        <PRow k="NEQ"            v={<span className="numeric">1170 392 488</span>}/>
        <PRow k="N° d'entreprise" v={<span className="numeric">789 234 561 RC0001</span>}/>
        <PRow k="Forme juridique" v="Société par actions"/>
      </PCard>

      <PCard title="Adresse du cabinet" action={<button className="btn ghost">Modifier</button>}>
        <PRow k="Adresse" v="2120, rue Stanley, bureau 800"/>
        <PRow k="Ville"   v="Montréal (Québec) H3A 1R8"/>
        <PRow k="Téléphone" v="514 555-1840"/>
        <PRow k="Courriel"  v="info@tremblay-eval.ca"/>
        <PRow k="Site web"  v="tremblay-eval.ca"/>
      </PCard>

      <PCard
        title="Logo & papier en-tête"
        desc="Le logo apparaît sur la page titre et l'en-tête de chaque rapport."
        action={<button className="btn secondary">Téléverser</button>}>
        <div className="logo-preview">
          <div className="lp-logo">
            <span className="lp-mark">T·É</span>
          </div>
          <div className="lp-info">
            <div className="lp-name">Tremblay Évaluations</div>
            <div className="lp-sub">SVG · 4,2 Ko · téléversé le 8 janv. 2025</div>
          </div>
        </div>
      </PCard>

      <PCard title="Couleurs de marque" desc="Utilisées sur la page titre des rapports.">
        <div className="brand-swatches">
          <div className="swatch">
            <span className="sw-color" style={{ background: '#1c3559' }}/>
            <span className="sw-name">Primaire</span>
            <span className="sw-hex numeric">#1C3559</span>
          </div>
          <div className="swatch">
            <span className="sw-color" style={{ background: '#b88a3e' }}/>
            <span className="sw-name">Accent</span>
            <span className="sw-hex numeric">#B88A3E</span>
          </div>
          <div className="swatch">
            <span className="sw-color" style={{ background: '#1f1e1c' }}/>
            <span className="sw-name">Texte</span>
            <span className="sw-hex numeric">#1F1E1C</span>
          </div>
        </div>
      </PCard>
    </>
  )
}

/* ── MEMBRES ── */
const MEMBERS = [
  { name: 'Maxime Tremblay',    role: 'É.A. — Associé principal',     oeaq: '4218', email: 'maxime@tremblay-eval.ca',  status: 'active' },
  { name: 'Émilie Lapointe',    role: 'É.A. — Associée',              oeaq: '5891', email: 'emilie@tremblay-eval.ca',  status: 'active' },
  { name: 'Jean-François Côté', role: 'É.A. stagiaire',               oeaq: '—',    email: 'jf@tremblay-eval.ca',      status: 'active' },
  { name: 'Sophie Bélanger',    role: 'Adjointe administrative',      oeaq: '—',    email: 'sophie@tremblay-eval.ca',  status: 'active' },
  { name: 'Camille Pelletier',  role: 'Recherchiste — temps partiel', oeaq: '—',    email: 'camille@tremblay-eval.ca', status: 'invited' },
]

function SectionMembres() {
  return (
    <>
      <PCard
        title="Membres du cabinet"
        desc="Gérer les accès, les rôles et les permissions de votre équipe."
        action={<button className="btn accent"><Icon.Plus/> Inviter</button>}>
        <div className="member-table">
          <div className="mt-head">
            <div>Personne</div>
            <div>Rôle</div>
            <div className="num">OEAQ</div>
            <div>Statut</div>
            <div></div>
          </div>
          {MEMBERS.map((m, i) => (
            <div className="mt-row" key={i}>
              <div className="mt-person">
                <div className="mt-avatar">{m.name.split(' ').map(w => w[0]).slice(0, 2).join('')}</div>
                <div>
                  <div className="mt-name">{m.name}</div>
                  <div className="mt-email">{m.email}</div>
                </div>
              </div>
              <div className="mt-role">{m.role}</div>
              <div className="num">{m.oeaq !== '—' ? <span className="numeric">{m.oeaq}</span> : <span className="muted">—</span>}</div>
              <div>
                <span className={`mt-pill ${m.status}`}>
                  {m.status === 'active' ? 'Actif' : 'Invitation envoyée'}
                </span>
              </div>
              <div className="mt-actions">
                <button className="btn ghost btn-sm">Gérer</button>
              </div>
            </div>
          ))}
        </div>
      </PCard>

      <PCard title="Permissions par défaut" desc="Ce qu'un nouveau membre peut faire à son arrivée.">
        <PToggle on={true}  onChange={() => {}} label="Créer des dossiers" desc="Ouvrir de nouveaux dossiers d'évaluation."/>
        <PToggle on={true}  onChange={() => {}} label="Consulter la bibliothèque" desc="Accéder aux ventes, marchés, coûts et taux."/>
        <PToggle on={false} onChange={() => {}} label="Signer des rapports" desc="Réservé aux É.A. en règle uniquement."/>
        <PToggle on={false} onChange={() => {}} label="Modifier les modèles" desc="Peut affecter tous les dossiers en cours."/>
      </PCard>
    </>
  )
}

/* ── INTÉGRATIONS ── */
const INTEGRATIONS = [
  { id: 'oeaq',     name: 'Registre OEAQ',              desc: 'Synchronise vos adhésions, permis et certificats.',           status: 'connected', since: '12 janv. 2024' },
  { id: 'jlr',      name: 'JLR — Ventes immobilières',  desc: 'Importez automatiquement les ventes comparables.',            status: 'connected', since: '22 mars 2024' },
  { id: 'centris',  name: 'Centris',                    desc: 'Données des fiches MLS résidentielles.',                      status: 'connected', since: '22 mars 2024' },
  { id: 'role',     name: "Rôle d'évaluation Montréal", desc: 'Pré-charge les caractéristiques au moment de la création.',   status: 'connected', since: '1 mai 2024' },
  { id: 'docusign', name: 'DocuSign',                   desc: 'Signature électronique des rapports et attestations.',        status: 'available', since: null },
  { id: 'qb',       name: 'QuickBooks',                 desc: 'Facturation des mandats et suivi des honoraires.',            status: 'available', since: null },
  { id: 'outlook',  name: 'Microsoft Outlook',          desc: 'Synchronisation du calendrier et des rendez-vous de visite.', status: 'available', since: null },
]

function SectionIntegrations() {
  return (
    <PCard
      title="Intégrations connectées"
      desc="Les sources qui alimentent vos dossiers."
      tight>
      <div className="int-grid">
        {INTEGRATIONS.map(i => (
          <div className={`int-card ${i.status}`} key={i.id}>
            <div className="int-head">
              <div className="int-logo">{i.name.split(' ')[0].slice(0, 2)}</div>
              <span className={`int-status ${i.status}`}>
                {i.status === 'connected' ? <><span className="d"/> Connecté</> : 'Disponible'}
              </span>
            </div>
            <div className="int-name">{i.name}</div>
            <div className="int-desc">{i.desc}</div>
            <div className="int-foot">
              {i.status === 'connected'
                ? <>
                    <span className="int-meta">Depuis {i.since}</span>
                    <button className="btn ghost btn-sm">Gérer</button>
                  </>
                : <button className="btn secondary btn-sm" style={{ marginLeft: 'auto' }}>Connecter</button>}
            </div>
          </div>
        ))}
      </div>
    </PCard>
  )
}

/* ── UTILISATION ── */
function SectionUtilisation() {
  return (
    <>
      <PCard title="Utilisation — mai 2026" desc="Vos compteurs ce mois-ci.">
        <div className="usage-grid">
          <Usage k="Dossiers ouverts"      v={12} max={25}/>
          <Usage k="Rapports signés"       v={8}  max={null}/>
          <Usage k="Comparables consultés" v={146} max={null}/>
          <Usage k="Stockage"              v="6,4 Go" max="50 Go" kind="storage"/>
        </div>
      </PCard>

      <PCard title="Répartition de vos dossiers" desc="Vos 12 dossiers actifs par type de mandat.">
        <div className="breakdown">
          <BD k="Hypothécaire" v={5} total={12} color="var(--navy)"/>
          <BD k="Pré-vente"    v={3} total={12} color="var(--ochre)"/>
          <BD k="Successoral"  v={2} total={12} color="var(--verdigris)"/>
          <BD k="Litige"       v={1} total={12} color="var(--oxblood)"/>
          <BD k="Acquisition"  v={1} total={12} color="var(--ink-mute)"/>
        </div>
      </PCard>

      <PCard title="Historique mensuel" desc="Dossiers ouverts par mois sur les 6 derniers mois.">
        <div className="history-bars">
          {[
            { m: 'Déc.',  n: 11 },
            { m: 'Janv.', n: 11 },
            { m: 'Févr.', n: 12 },
            { m: 'Mars',  n: 16 },
            { m: 'Avril', n: 18 },
            { m: 'Mai',   n: 14 },
          ].map((x, i) => {
            const pct = (x.n / 20) * 100
            return (
              <div className="hb-col" key={i}>
                <div className="hb-val numeric">{x.n}</div>
                <div className="hb-bar"><span style={{ height: `${pct}%` }}/></div>
                <div className="hb-m">{x.m}</div>
              </div>
            )
          })}
        </div>
      </PCard>

      <div className="billing-note">
        <div className="bn-icon"><Icon.Seal/></div>
        <div className="bn-text">
          <b>La facturation est gérée par votre cabinet.</b>
          <span>
            L&apos;abonnement de <b>Tremblay Évaluations</b> couvre 4 utilisateurs. Pour
            consulter les factures ou modifier le forfait, contactez votre administrateur ou
            {' '}<a href="mailto:facturation@evalimmo.ca">écrivez à facturation@evalimmo.ca</a>.
          </span>
        </div>
      </div>
    </>
  )
}

function BD({ k, v, total, color }: { k: string; v: number; total: number; color: string }) {
  const pct = (v / total) * 100
  return (
    <div className="bd-row">
      <div className="bd-k">{k}</div>
      <div className="bd-bar">
        <span style={{ width: `${pct}%`, background: color }}/>
      </div>
      <div className="bd-v numeric">{v}</div>
    </div>
  )
}

function Usage({ k, v, max, kind = 'count' }: {
  k: string; v: number | string; max: number | string | null; kind?: 'count' | 'storage'
}) {
  let pct = 0
  if (max != null) {
    if (kind === 'storage') pct = 13 // 6,4 / 50
    else if (typeof v === 'number' && typeof max === 'number') pct = Math.min(100, (v / max) * 100)
  }
  return (
    <div className="usage">
      <div className="us-k">{k}</div>
      <div className="us-v numeric">
        {v} {max != null && <span className="us-max">/ {max}</span>}
      </div>
      {max != null && (
        <div className="us-bar">
          <span className="us-fill" style={{ width: `${pct}%` }}/>
        </div>
      )}
    </div>
  )
}

/* ── SÉCURITÉ ── */
function SectionSecurite() {
  const [twofa, setTwofa] = useState(true)
  const [sso, setSso] = useState(true)
  const [autosign, setAutosign] = useState(false)

  return (
    <>
      <PCard title="Mot de passe" action={<button className="btn ghost">Changer</button>}>
        <PRow k="Dernière modification" v="il y a 4 mois"/>
        <PRow k="Robustesse"            v={<span className="strength good">Excellent</span>}/>
      </PCard>

      <PCard title="Authentification" desc="Comment vous accédez à votre cabinet.">
        <PToggle on={twofa} onChange={setTwofa}
          label="Double authentification"
          desc="Code unique envoyé par appli (Authenticator, Microsoft Authy)."/>
        <PToggle on={sso} onChange={setSso}
          label="Connexion via Microsoft 365"
          desc="Activée pour tous les membres du cabinet."/>
        <PToggle on={autosign} onChange={setAutosign}
          label="Signature biométrique sur les rapports"
          desc="Confirmation par Touch ID / Windows Hello à la signature finale."/>
      </PCard>

      <PCard title="Sessions actives" action={<button className="btn ghost">Tout déconnecter</button>}>
        <div className="session">
          <div className="sess-icon">💻</div>
          <div className="sess-main">
            <div className="sess-name">MacBook Pro — Maxime · cette session</div>
            <div className="sess-meta">Safari · Montréal, QC · IP 24.122.•.• · Connecté il y a 4 h</div>
          </div>
          <span className="sess-tag current">Actuel</span>
        </div>
        <div className="session">
          <div className="sess-icon">📱</div>
          <div className="sess-main">
            <div className="sess-name">iPhone — Maxime</div>
            <div className="sess-meta">App iOS · Outremont, QC · Connecté il y a 2 jours</div>
          </div>
          <button className="btn ghost btn-sm">Déconnecter</button>
        </div>
        <div className="session">
          <div className="sess-icon">💻</div>
          <div className="sess-main">
            <div className="sess-name">Windows — Bureau (cabinet)</div>
            <div className="sess-meta">Edge · Montréal, QC · Connecté il y a 1 semaine</div>
          </div>
          <button className="btn ghost btn-sm">Déconnecter</button>
        </div>
      </PCard>

      <PCard
        title="Journal d'audit"
        desc="Conservé 7 ans conformément aux normes de l'OEAQ et à la Loi 25.">
        <ul className="audit">
          <li>
            <div className="au-when">Aujourd&apos;hui · 14:22</div>
            <div className="au-what"><b>Maxime Tremblay</b> a signé le rapport <i>2026-0411</i>.</div>
          </li>
          <li>
            <div className="au-when">Hier · 09:08</div>
            <div className="au-what"><b>Émilie Lapointe</b> a ouvert un dossier <i>2026-0418</i>.</div>
          </li>
          <li>
            <div className="au-when">Il y a 3 jours</div>
            <div className="au-what"><b>Système</b> a synchronisé le registre OEAQ.</div>
          </li>
          <li>
            <div className="au-when">Il y a 5 jours</div>
            <div className="au-what"><b>Maxime Tremblay</b> a invité <i>camille@tremblay-eval.ca</i>.</div>
          </li>
        </ul>
        <button className="btn ghost" style={{ alignSelf: 'flex-start' }}>Voir tout le journal</button>
      </PCard>
    </>
  )
}

/* ── PRÉFÉRENCES ── */
function SectionPreferences() {
  const [agentAuto, setAgentAuto] = useState(true)
  const [emailDigest, setEmailDigest] = useState(true)
  const [deadline, setDeadline] = useState(true)

  return (
    <>
      <PCard title="Affichage" desc="Comment l'application se présente pour vous.">
        <PRow k="Langue de l'interface" v="Français (Canada)"/>
        <PRow k="Format des nombres"    v={<span className="numeric">895 000,00 $</span>}/>
        <PRow k="Unité de superficie"   v="pi² (pieds carrés)"/>
        <PRow k="Fuseau horaire"        v="Amérique / Montréal (UTC −5)"/>
      </PCard>

      <PCard title="Agent IA" desc="L'assistant qui suggère et automatise dans vos dossiers.">
        <PToggle on={agentAuto} onChange={setAgentAuto}
          label="Suggestions automatiques de comparables"
          desc="L'agent vous propose des ventes pertinentes à chaque ouverture de dossier."/>
        <PToggle on={true} onChange={() => {}}
          label="Rédaction assistée des notes"
          desc="L'agent peut générer un brouillon de notes à partir des données du dossier."/>
        <PToggle on={false} onChange={() => {}}
          label="Signature automatique des rapports"
          desc="Désactivé. La signature finale reste manuelle, conformément à l'OEAQ."/>
      </PCard>

      <PCard title="Notifications" desc="Ce qui vous arrive par courriel et dans l'application.">
        <PToggle on={deadline}    onChange={setDeadline}    label="Échéances de mandats à venir"        desc="Rappel 3 jours, 1 jour et le matin même."/>
        <PToggle on={emailDigest} onChange={setEmailDigest} label="Sommaire hebdomadaire par courriel" desc="Tous les lundis matin — dossiers à signer, marchés notables."/>
        <PToggle on={true}        onChange={() => {}}       label="Mises à jour de l'OEAQ"             desc="Avis, normes et changements réglementaires."/>
      </PCard>
    </>
  )
}
