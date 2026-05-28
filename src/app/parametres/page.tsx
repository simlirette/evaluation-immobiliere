'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { createClient } from '@/lib/supabase/client'

const SECTIONS = [
  { id: 'profil',       label: 'Profil' },
  { id: 'cabinet',      label: 'Cabinet' },
  { id: 'membres',      label: 'Membres' },
  { id: 'integrations', label: 'Intégrations' },
  { id: 'utilisation',  label: 'Utilisation' },
  { id: 'securite',     label: 'Sécurité' },
  { id: 'preferences',  label: 'Préférences' },
]

function Row({ label, value, action }: { label: string; value?: string; action?: React.ReactNode }) {
  return (
    <div
      className="flex items-center justify-between py-3"
      style={{ borderBottom: '1px solid var(--rule-soft)' }}
    >
      <div>
        <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>{label}</div>
        {value && <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{value}</div>}
      </div>
      {action && <div className="flex-shrink-0 ml-4">{action}</div>}
    </div>
  )
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="relative w-9 h-5 rounded-full transition-colors flex-shrink-0"
      style={{ background: checked ? 'var(--navy)' : 'var(--rule)' }}
    >
      <span
        className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform"
        style={{ transform: checked ? 'translateX(16px)' : 'translateX(0)' }}
      />
    </button>
  )
}

function SectionProfil() {
  return (
    <section className="panel flex flex-col gap-0">
      <div className="panel-head">
        <h2 className="panel-title">Profil</h2>
        <button className="btn ghost btn-sm">Modifier</button>
      </div>
      <Row label="Nom complet" value="Maxime Tremblay, É.A." action={<button className="btn ghost btn-sm">Modifier</button>} />
      <Row label="Adresse e-mail" value="m.tremblay@cabinet-eval.qc.ca" action={<button className="btn ghost btn-sm">Modifier</button>} />
      <Row label="Téléphone" value="+1 (514) 555-0182" action={<button className="btn ghost btn-sm">Modifier</button>} />
      <Row label="Numéro OEAQ" value="OEAQ 4218" action={<button className="btn ghost btn-sm">Modifier</button>} />
      <Row label="Titre professionnel" value="Évaluateur agréé · Résidentiel, Commercial" />
      <div className="mt-4">
        <div className="eyebrow mb-2">Signature électronique</div>
        <div
          className="rounded-[var(--r-md)] px-4 py-3 text-center text-[13px]"
          style={{ background: 'var(--paper-2)', border: '1px dashed var(--rule)', color: 'var(--ink-mute)' }}
        >
          Aucune signature configurée — <button className="underline" style={{ color: 'var(--navy)' }}>Téléverser</button>
        </div>
      </div>
    </section>
  )
}

function SectionCabinet() {
  return (
    <section className="panel flex flex-col gap-0">
      <div className="panel-head">
        <h2 className="panel-title">Cabinet</h2>
        <button className="btn ghost btn-sm">Modifier</button>
      </div>
      <Row label="Raison sociale" value="Cabinet Tremblay & Associés inc." />
      <Row label="NEQ" value="1234567890" />
      <Row label="Adresse" value="1000 rue De La Gauchetière O., bureau 2400, Montréal, QC H3B 4W5" />
      <Row label="Téléphone" value="+1 (514) 555-0100" />
      <Row label="Logo" action={<button className="btn secondary btn-sm">Téléverser</button>} />
      <Row label="Couleur marque" value="#1e3a5f (Marine)" action={<div className="w-6 h-6 rounded-full border border-[var(--rule)]" style={{ background: '#1e3a5f' }} />} />
    </section>
  )
}

function SectionMembres() {
  const membres = [
    { nom: 'Maxime Tremblay, É.A.', courriel: 'm.tremblay@cabinet-eval.qc.ca', role: 'Administrateur', statut: 'Actif' },
    { nom: 'Geneviève Roy, É.A.', courriel: 'g.roy@cabinet-eval.qc.ca', role: 'Évaluateur', statut: 'Actif' },
    { nom: 'Catherine Demers', courriel: 'c.demers@cabinet-eval.qc.ca', role: 'Adjoint(e)', statut: 'Actif' },
  ]
  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">Membres</h2>
        <button className="btn accent btn-sm">+ Inviter</button>
      </div>
      <div
        className="rounded-[var(--r-md)] overflow-hidden"
        style={{ border: '1px solid var(--rule)' }}
      >
        <div
          className="grid px-4 py-2 text-[11px] font-medium uppercase tracking-[.05em]"
          style={{ gridTemplateColumns: '2fr 2fr 120px 80px', color: 'var(--ink-faint)', background: 'var(--paper)' }}
        >
          <span>Nom</span><span>Courriel</span><span>Rôle</span><span>Statut</span>
        </div>
        {membres.map((m, i) => (
          <div
            key={i}
            className="grid px-4 py-3 text-[13px]"
            style={{ gridTemplateColumns: '2fr 2fr 120px 80px', borderTop: '1px solid var(--rule-soft)' }}
          >
            <span style={{ color: 'var(--ink)', fontWeight: 500 }}>{m.nom}</span>
            <span style={{ color: 'var(--ink-mute)' }}>{m.courriel}</span>
            <span style={{ color: 'var(--ink-mute)' }}>{m.role}</span>
            <span
              className="text-[11px] font-medium"
              style={{ color: m.statut === 'Actif' ? 'var(--verdigris)' : 'var(--ink-faint)' }}
            >
              {m.statut}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

function SectionIntegrations() {
  const integrations = [
    { nom: 'OEAQ — Registre', desc: 'Vérification des membres et conformité OEAQ', connecte: true },
    { nom: 'JLR Solutions foncières', desc: 'Données cadastrales et transactions immobilières', connecte: true },
    { nom: 'Centris', desc: 'Comparables résidentiels en temps réel', connecte: false },
    { nom: 'DocuSign', desc: 'Signature électronique des rapports', connecte: false },
    { nom: 'QuickBooks', desc: 'Facturation et suivi des honoraires', connecte: false },
  ]
  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">Intégrations</h2>
      </div>
      <div className="flex flex-col gap-3">
        {integrations.map((integ, i) => (
          <div
            key={i}
            className="flex items-center justify-between p-4 rounded-[var(--r-md)]"
            style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
          >
            <div>
              <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>{integ.nom}</div>
              <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>{integ.desc}</div>
            </div>
            {integ.connecte
              ? <span className="text-[11px] font-medium px-2.5 py-1 rounded-full" style={{ background: 'rgba(46,130,100,.1)', color: 'var(--verdigris)' }}>Connecté</span>
              : <button className="btn secondary btn-sm">Connecter</button>
            }
          </div>
        ))}
      </div>
    </section>
  )
}

function SectionSecurite() {
  return (
    <section className="panel flex flex-col gap-0">
      <div className="panel-head">
        <h2 className="panel-title">Sécurité</h2>
      </div>
      <Row label="Mot de passe" value="Dernière modification il y a 3 mois" action={<button className="btn ghost btn-sm">Modifier</button>} />
      <Row label="Authentification à deux facteurs" value="Non activée" action={<button className="btn secondary btn-sm">Activer</button>} />
      <Row label="Sessions actives" value="1 session — Montréal, QC · Chrome" action={<button className="btn ghost btn-sm">Révoquer</button>} />
      <Row label="Journal d'accès" action={<button className="btn ghost btn-sm">Consulter</button>} />
    </section>
  )
}

function SectionPreferences() {
  const [darkMode, setDarkMode] = useState(false)
  const [notifications, setNotifications] = useState(true)
  const [agentAuto, setAgentAuto] = useState(true)
  const [compactView, setCompactView] = useState(false)

  return (
    <section className="panel flex flex-col gap-0">
      <div className="panel-head">
        <h2 className="panel-title">Préférences</h2>
      </div>
      <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
        <div>
          <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>Mode sombre</div>
          <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>Activer le thème sombre de l'interface</div>
        </div>
        <Toggle checked={darkMode} onChange={v => { setDarkMode(v); document.documentElement.setAttribute('data-theme', v ? 'dark' : 'light') }} />
      </div>
      <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
        <div>
          <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>Notifications par courriel</div>
          <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>Recevoir un résumé quotidien des dossiers actifs</div>
        </div>
        <Toggle checked={notifications} onChange={setNotifications} />
      </div>
      <div className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid var(--rule-soft)' }}>
        <div>
          <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>Enrichissement automatique</div>
          <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>Lancer l'agent d'enrichissement à la création du dossier</div>
        </div>
        <Toggle checked={agentAuto} onChange={setAgentAuto} />
      </div>
      <div className="flex items-center justify-between py-3">
        <div>
          <div className="text-[13px] font-medium" style={{ color: 'var(--ink)' }}>Vue compacte des listes</div>
          <div className="text-[12px] mt-0.5" style={{ color: 'var(--ink-mute)' }}>Réduire la hauteur des rangées dans les tableaux</div>
        </div>
        <Toggle checked={compactView} onChange={setCompactView} />
      </div>
    </section>
  )
}

export default function ParametresPage() {
  const router = useRouter()
  const [activeSection, setActiveSection] = useState('profil')

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'profil': return <SectionProfil />
      case 'cabinet': return <SectionCabinet />
      case 'membres': return <SectionMembres />
      case 'integrations': return <SectionIntegrations />
      case 'securite': return <SectionSecurite />
      case 'preferences': return <SectionPreferences />
      case 'utilisation':
        return (
          <section className="panel">
            <div className="panel-head"><h2 className="panel-title">Utilisation</h2></div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { label: 'Dossiers ouverts', value: '12' },
                { label: 'Rapports signés', value: '284' },
                { label: 'Comparables utilisés', value: '1 842' },
              ].map(s => (
                <div key={s.label} className="panel">
                  <div className="eyebrow mb-1">{s.label}</div>
                  <div className="text-[28px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{s.value}</div>
                </div>
              ))}
            </div>
            <div className="eyebrow mb-3">Facturation</div>
            <div
              className="rounded-[var(--r-md)] p-4"
              style={{ background: 'var(--paper-2)', border: '1px solid var(--rule-soft)' }}
            >
              <div className="text-[13px]" style={{ color: 'var(--ink)' }}>Plan <strong>Professionnel</strong> — 89 $/mois</div>
              <div className="text-[12px] mt-1" style={{ color: 'var(--ink-mute)' }}>Renouvellement le 1er juin 2026 · Visa se terminant par 4242</div>
              <button className="btn ghost btn-sm mt-3">Gérer l'abonnement</button>
            </div>
          </section>
        )
      default: return null
    }
  }

  return (
    <div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
      <Sidebar onSignOut={handleSignOut} />

      <div className="main-content flex overflow-hidden">
        {/* Section nav */}
        <nav
          className="w-[200px] flex-shrink-0 flex flex-col gap-1 pt-8 px-4 border-r overflow-y-auto"
          style={{ borderRightColor: 'var(--rule-soft)' }}
        >
          <div className="eyebrow mb-3">Paramètres</div>
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className="text-left px-3 py-2 text-[13px] rounded-[var(--r-md)] transition-colors"
              style={{
                color: activeSection === s.id ? 'var(--navy)' : 'var(--ink-mute)',
                background: activeSection === s.id ? 'var(--navy-tint)' : 'transparent',
                fontWeight: activeSection === s.id ? 500 : 400,
              }}
            >
              {s.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-10 py-8">
          <div className="max-w-[680px] flex flex-col gap-5">
            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}
