'use client'

/* Nouveau dossier — wizard 4 étapes, port 1:1 du design handoff
   (nouveau-dossier.jsx + nouveau-dossier.css).
   - Création câblée sur createRuntimeDossier (runtime backend).
   - Recherche : index municipal mock du design (le registre réel viendra
     d'un endpoint backend).
   - Chemin « Saisir manuellement » rendu fonctionnel (le prototype ne
     l'implémentait pas) avec les mêmes champs nd-field. */

import { useState, useMemo, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Dropdown from '@/components/shared/Dropdown'
import { Icon } from '@/components/shared/Icon'
import { formatCAD, fmtNum } from '@/lib/format-number'
import { createRuntimeDossier } from '@/lib/runtime-api'
import { createClient } from '@/lib/supabase/client'
import './nouveau-dossier.css'

const STEPS = [
  { n: 1, label: 'Point de départ' },
  { n: 2, label: 'Propriété' },
  { n: 3, label: 'Mandat' },
  { n: 4, label: 'Confirmation' },
]

const PATHS = [
  {
    id: 'search',
    title: 'Rechercher une propriété',
    desc: "Trouvez l'immeuble dans le registre municipal et importez automatiquement les caractéristiques du rôle d'évaluation.",
    badge: 'Recommandé',
    icon: 'search',
  },
  {
    id: 'manual',
    title: 'Saisir manuellement',
    desc: "Entrez l'adresse et les caractéristiques de la propriété à la main. Utile lorsque le rôle n'est pas à jour.",
    icon: 'edit',
  },
  {
    id: 'import',
    title: 'Importer un document',
    desc: 'Importez un mandat, un rôle municipal ou une fiche Centris en PDF. Les champs seront extraits automatiquement.',
    badge: 'Bêta',
    icon: 'import',
  },
  {
    id: 'template',
    title: "Démarrer d'un modèle",
    desc: "Reprenez la structure d'un mandat précédent — utile pour les évaluations en série ou les nouveaux contrats récurrents.",
    icon: 'template',
  },
] as const

type PathId = typeof PATHS[number]['id']

const MANDATE_TYPES = [
  'Hypothécaire', 'Pré-vente', 'Successoral', 'Donation',
  'Litige', 'Acquisition', 'Refinancement', 'Expropriation',
]

const MODELES = [
  'Hypothécaire — Résidentiel',
  'Pré-vente — Résidentiel',
  'Successoral & donation',
  'Litige & expropriation',
  'Acquisition — Immeuble à revenus',
  'Avis de valeur restreint',
]

const CLIENTS = [
  'Banque Nationale du Canada',
  'Caisse Desjardins — Outremont',
  'RBC — Refinancement',
  'Étude Goldberg, avocats',
  'Me Anne Beauchamp, notaire',
  'Cabinet Lévesque & Tremblay',
]

interface Property {
  addr: string
  city: string
  cadastre: string
  year: number | null
  area: number | null
  lot: number | null
  type: string
  roll: number | null
}

/* Index municipal mock du design — remplacé par un endpoint registre réel plus tard. */
const ADDRESS_INDEX: Property[] = [
  { addr: '245, av. Wiseman',         city: 'Outremont',          cadastre: '1 870 421', year: 1948, area: 1842, lot: 4820, type: 'Maison unifamiliale', roll: 1185000 },
  { addr: '312, av. Bloomfield',      city: 'Outremont',          cadastre: '1 870 412', year: 1936, area: 1920, lot: 4200, type: 'Maison unifamiliale', roll: 1240000 },
  { addr: '198, av. Outremont',       city: 'Outremont',          cadastre: '1 870 388', year: 1936, area: 1720, lot: 3650, type: 'Maison unifamiliale', roll: 1095000 },
  { addr: '4218, rue Cartier',        city: 'Plateau-Mont-Royal', cadastre: '1 872 104', year: 1923, area: 2410, lot: 2100, type: 'Duplex',              roll: 685000 },
  { addr: '67, av. Wood',             city: 'Westmount',          cadastre: '1 869 022', year: 1912, area: 3240, lot: 6200, type: 'Maison unifamiliale', roll: 2105000 },
  { addr: "5412, av. de l'Esplanade", city: 'Mile End',           cadastre: '1 873 542', year: 1918, area: 2580, lot: 2400, type: 'Duplex',              roll: 805000 },
  { addr: '8124, rue de Lanaudière',  city: 'Villeray',           cadastre: '1 875 219', year: 1958, area: 2640, lot: 2900, type: 'Triplex',             roll: 615000 },
]

const PROPERTY_TYPES = ['Maison unifamiliale', 'Condo', 'Duplex', 'Triplex', 'Quadruplex', 'Immeuble à revenus', 'Commercial', 'Terrain']

function backendPropertyType(t: string): string {
  const map: Record<string, string> = {
    'Maison unifamiliale': 'residentiel_unifamilial',
    'Condo': 'condo',
    'Duplex': 'duplex',
    'Triplex': 'triplex',
    'Quadruplex': 'quadruplex',
    'Immeuble à revenus': 'autre',
    'Commercial': 'commercial',
    'Terrain': 'terrain',
  }
  return map[t] ?? 'autre'
}

function backendFinEvaluation(m: string): string {
  const map: Record<string, string> = {
    'Hypothécaire': 'hypothecaire',
    'Pré-vente': 'autre',
    'Successoral': 'succession',
    'Donation': 'succession',
    'Litige': 'litige',
    'Acquisition': 'commercial',
    'Refinancement': 'hypothecaire',
    'Expropriation': 'expropriation',
  }
  return map[m] ?? 'autre'
}

interface Mandate {
  type: string
  client: string
  contact: string
  phone: string
  email: string
  dateValeur: string
  dateEcheance: string
  modele: string
  notes: string
}

export default function NouveauDossierPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [path, setPath] = useState<PathId | null>(null)
  const [property, setProperty] = useState<Property | null>(null)
  const [mandate, setMandate] = useState<Mandate>({
    type: 'Hypothécaire',
    client: '',
    contact: '',
    phone: '',
    email: '',
    dateValeur: new Date().toISOString().slice(0, 10),
    dateEcheance: '',
    modele: 'Hypothécaire — Résidentiel',
    notes: '',
  })
  const [created, setCreated] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const canAdvance = (
    step === 1 ? !!path :
    step === 2 ? !!property && !!property.addr && !!property.city :
    step === 3 ? !!mandate.type && !!mandate.client && !!mandate.dateValeur :
    true
  )

  function next() { if (canAdvance && step < 4) setStep(s => s + 1) }
  function prev() { if (step > 1) setStep(s => s - 1) }

  async function create() {
    if (!property || created) return
    setCreated(true)
    setCreateError(null)
    try {
      const d = await createRuntimeDossier({
        address: property.addr,
        property_type: backendPropertyType(property.type),
        neighborhood: property.city,
        mandat_type: undefined, // routage classify_dossier côté backend
        date_reference: mandate.dateValeur,
        superficie_habitable: property.area,
        superficie_terrain: property.lot,
        annee_construction: property.year,
        commanditaire: {
          nom: mandate.contact || mandate.client,
          organisation: mandate.client,
          fin_evaluation: backendFinEvaluation(mandate.type),
        },
        date_livraison: mandate.dateEcheance || undefined,
      })
      router.push(`/dossier/${d.slug}?tab=dossier`)
    } catch (e) {
      setCreated(false)
      setCreateError(e instanceof Error ? e.message : 'Erreur lors de la création du dossier')
    }
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
        <div className="topbar nd-topbar">
          <div className="pagehead nd-head">
            <div>
              <h1>Nouveau dossier</h1>
              <div className="subtitle">{stepSubtitle(step)}</div>
            </div>
          </div>

          {/* Stepper */}
          <div className="stepper nd-stepper">
            {STEPS.map(s => {
              const state = s.n < step ? 'done' : s.n === step ? 'now' : 'upcoming'
              return (
                <button
                  key={s.n}
                  className={`step ${state}`}
                  onClick={() => { if (s.n < step) setStep(s.n) }}>
                  {state === 'done'
                    ? <Icon.Check/>
                    : <span className="num numeric">{String(s.n).padStart(2, '0')}</span>}
                  <span className="label">{s.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="nd-body">
          {step === 1 && <StepPath path={path} setPath={setPath}/>}
          {step === 2 && <StepProperty property={property} setProperty={setProperty} path={path}/>}
          {step === 3 && <StepMandate mandate={mandate} setMandate={setMandate}/>}
          {step === 4 && <StepConfirm path={path} property={property} mandate={mandate} created={created} error={createError}/>}
        </div>

        {/* Footer */}
        <div className="nd-footer">
          <div className="nd-footer-inner">
            <button className="btn ghost" onClick={prev} disabled={step === 1}>
              <Icon.ChevronLeft/> Précédent
            </button>
            <div className="nd-footer-status">
              Étape <b className="numeric">{step}</b> sur <b className="numeric">{STEPS.length}</b>
            </div>
            {step < 4
              ? <button className="btn accent" onClick={next} disabled={!canAdvance}>
                  Continuer <ChevronRight/>
                </button>
              : <button className="btn accent" onClick={create} disabled={created}>
                  {created ? 'Création…' : 'Créer le dossier'}
                </button>}
          </div>
        </div>
      </div>
    </div>
  )
}

function stepSubtitle(step: number): string {
  switch (step) {
    case 1: return 'Comment souhaitez-vous démarrer ce dossier ?'
    case 2: return 'Identifier la propriété à évaluer.'
    case 3: return 'Préciser le mandat et le client.'
    case 4: return 'Vérifiez les informations avant de créer le dossier.'
    default: return ''
  }
}

function ChevronRight() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 4l4 4-4 4"/>
    </svg>
  )
}

/* ── STEP 1 — Point de départ ── */
function StepPath({ path, setPath }: { path: PathId | null; setPath: (p: PathId) => void }) {
  return (
    <div className="nd-step nd-step-path">
      <div className="nd-paths">
        {PATHS.map(p => (
          <button
            key={p.id}
            className={`path-card ${path === p.id ? 'selected' : ''}`}
            onClick={() => setPath(p.id)}>
            <div className="path-icon">
              {p.icon === 'search'   && <Icon.Glass/>}
              {p.icon === 'edit'     && <Icon.Edit/>}
              {p.icon === 'import'   && <Icon.Plus/>}
              {p.icon === 'template' && <Icon.Template/>}
            </div>
            <div className="path-body">
              <div className="path-title">
                {p.title}
                {'badge' in p && p.badge && <span className={`path-badge badge-${p.badge.toLowerCase()}`}>{p.badge}</span>}
              </div>
              <div className="path-desc">{p.desc}</div>
            </div>
            <div className="path-mark">
              {path === p.id ? <Icon.Check/> : null}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

/* ── STEP 2 — Propriété ── */
function StepProperty({ property, setProperty, path }: {
  property: Property | null
  setProperty: (p: Property | null) => void
  path: PathId | null
}) {
  const [query, setQuery] = useState('')
  const results = useMemo(() => {
    if (!query.trim()) return ADDRESS_INDEX.slice(0, 5)
    const q = query.trim().toLowerCase()
    return ADDRESS_INDEX.filter(x =>
      x.addr.toLowerCase().includes(q) ||
      x.city.toLowerCase().includes(q) ||
      x.cadastre.replace(/\s/g, '').includes(q.replace(/\s/g, ''))
    )
  }, [query])

  if (path === 'manual') {
    return <StepPropertyManual property={property} setProperty={setProperty}/>
  }

  return (
    <div className="nd-step nd-step-prop">
      <div className="nd-form">
        <label className="nd-field">
          <span className="nd-k">Adresse ou cadastre</span>
          <div className="nd-search">
            <Icon.Glass/>
            <input
              type="text"
              autoFocus
              placeholder="ex. 245 Wiseman, ou 1 870 421"
              value={query}
              onChange={e => { setQuery(e.target.value); setProperty(null) }}
            />
          </div>
          <span className="nd-help">
            Recherche dans le registre municipal de Montréal. Les caractéristiques seront
            préchargées du rôle d&apos;évaluation.
          </span>
        </label>

        {!property && (
          <div className="nd-results">
            {results.length === 0 && (
              <div className="nd-empty">Aucune adresse ne correspond à « {query} »</div>
            )}
            {results.map((r, i) => (
              <button key={i} className="nd-result" onClick={() => setProperty(r)}>
                <div className="r-left">
                  <div className="r-addr">{r.addr}</div>
                  <div className="r-meta">
                    <span>{r.city}</span>
                    <span className="dot-sep">·</span>
                    <span>{r.type}</span>
                    <span className="dot-sep">·</span>
                    <span className="numeric">{r.year}</span>
                  </div>
                </div>
                <div className="r-right numeric">{r.cadastre}</div>
              </button>
            ))}
          </div>
        )}

        {property && (
          <div className="nd-preview">
            <div className="prev-head">
              <div>
                <div className="eyebrow">Aperçu du rôle municipal</div>
                <h3>{property.addr}</h3>
                <div className="prev-sub">{property.city}, Montréal</div>
              </div>
              <button className="btn ghost" onClick={() => { setProperty(null); setQuery('') }}>
                Changer
              </button>
            </div>
            <div className="prev-grid">
              <KVP k="Cadastre"       v={property.cadastre}/>
              <KVP k="Type"           v={property.type}/>
              <KVP k="Année"          v={property.year ?? '—'}/>
              <KVP k="Superficie"     v={property.area ? `${fmtNum(property.area)} pi²` : '—'}/>
              <KVP k="Lot"            v={property.lot ? `${fmtNum(property.lot)} pi²` : '—'}/>
              <KVP k="Rôle municipal" v={property.roll ? formatCAD(property.roll) : '—'}/>
            </div>
            <div className="prev-note">
              <Icon.Sparkle/>
              <span>
                Les caractéristiques détaillées (chambres, salles de bain, stationnement)
                seront enrichies automatiquement après la création du dossier.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* Chemin « Saisir manuellement » — mêmes champs nd-field (intent du design,
   non implémenté dans le prototype). */
function StepPropertyManual({ property, setProperty }: {
  property: Property | null
  setProperty: (p: Property | null) => void
}) {
  const p = property ?? { addr: '', city: '', cadastre: '', year: null, area: null, lot: null, type: 'Maison unifamiliale', roll: null }

  function up<K extends keyof Property>(field: K, v: Property[K]) {
    setProperty({ ...p, [field]: v })
  }

  return (
    <div className="nd-step nd-step-prop">
      <div className="nd-form">
        <Section title="Propriété">
          <Field label="Adresse" required>
            <input type="text" placeholder="ex. 245, av. Wiseman" value={p.addr}
              onChange={e => up('addr', e.target.value)}/>
          </Field>
          <div className="nd-row-2">
            <Field label="Quartier / ville" required>
              <input type="text" placeholder="ex. Outremont" value={p.city}
                onChange={e => up('city', e.target.value)}/>
            </Field>
            <Field label="Cadastre">
              <input type="text" placeholder="ex. 1 870 421" value={p.cadastre}
                onChange={e => up('cadastre', e.target.value)}/>
            </Field>
          </div>
          <Field label="Type de propriété">
            <Dropdown value={p.type} onChange={v => up('type', v)} options={PROPERTY_TYPES}/>
          </Field>
          <div className="nd-row-2">
            <Field label="Année de construction">
              <input type="number" placeholder="ex. 1948" value={p.year ?? ''}
                onChange={e => up('year', e.target.value ? Number(e.target.value) : null)}/>
            </Field>
            <Field label="Superficie habitable (pi²)">
              <input type="number" placeholder="ex. 1842" value={p.area ?? ''}
                onChange={e => up('area', e.target.value ? Number(e.target.value) : null)}/>
            </Field>
          </div>
          <Field label="Superficie du terrain (pi²)">
            <input type="number" placeholder="ex. 4820" value={p.lot ?? ''}
              onChange={e => up('lot', e.target.value ? Number(e.target.value) : null)}/>
          </Field>
        </Section>
      </div>
    </div>
  )
}

function KVP({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="kvp">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  )
}

/* ── STEP 3 — Mandat ── */
function StepMandate({ mandate, setMandate }: {
  mandate: Mandate
  setMandate: React.Dispatch<React.SetStateAction<Mandate>>
}) {
  function up<K extends keyof Mandate>(field: K, v: Mandate[K]) {
    setMandate(m => ({ ...m, [field]: v }))
  }
  return (
    <div className="nd-step nd-step-mandate">
      <div className="nd-form nd-form-2col">
        <Section title="Mandat">
          <Field label="Type de mandat" required>
            <Dropdown
              value={mandate.type}
              onChange={v => up('type', v)}
              options={MANDATE_TYPES}
            />
          </Field>
          <Field label="Modèle de rapport">
            <Dropdown
              value={mandate.modele}
              onChange={v => up('modele', v)}
              options={MODELES}
            />
          </Field>
          <div className="nd-row-2">
            <Field label="Date de valeur" required>
              <input type="date"
                value={mandate.dateValeur}
                onChange={e => up('dateValeur', e.target.value)}
                onClick={e => e.currentTarget.showPicker?.()}/>
            </Field>
            <Field label="Échéance">
              <input type="date"
                value={mandate.dateEcheance}
                onChange={e => up('dateEcheance', e.target.value)}
                onClick={e => e.currentTarget.showPicker?.()}/>
            </Field>
          </div>
        </Section>

        <Section title="Client">
          <Field label="Organisation" required>
            <input
              type="text"
              placeholder="ex. Banque Nationale du Canada"
              list="clients-list"
              value={mandate.client}
              onChange={e => up('client', e.target.value)}
            />
            <datalist id="clients-list">
              {CLIENTS.map(c => <option key={c} value={c}/>)}
            </datalist>
          </Field>
          <Field label="Représentant">
            <input
              type="text"
              placeholder="ex. Mtre. Sylvie Gagné"
              value={mandate.contact}
              onChange={e => up('contact', e.target.value)}
            />
          </Field>
          <div className="nd-row-2">
            <Field label="Téléphone">
              <input
                type="tel"
                placeholder="514 …"
                value={mandate.phone}
                onChange={e => up('phone', e.target.value)}
              />
            </Field>
            <Field label="Courriel">
              <input
                type="email"
                placeholder="prenom@org.ca"
                value={mandate.email}
                onChange={e => up('email', e.target.value)}
              />
            </Field>
          </div>
        </Section>

        <Section title="Notes" full>
          <Field label="Contexte du mandat">
            <textarea
              rows={3}
              placeholder="Détails additionnels qui orienteront l'évaluation…"
              value={mandate.notes}
              onChange={e => up('notes', e.target.value)}
            />
          </Field>
        </Section>
      </div>
    </div>
  )
}

function Section({ title, children, full }: { title: string; children: ReactNode; full?: boolean }) {
  return (
    <section className={`nd-section ${full ? 'full' : ''}`}>
      <h3>{title}</h3>
      <div className="nd-section-body">{children}</div>
    </section>
  )
}

function Field({ label, required, children }: { label: string; required?: boolean; children: ReactNode }) {
  return (
    <label className="nd-field">
      <span className="nd-k">{label}{required && <span className="req"> *</span>}</span>
      {children}
    </label>
  )
}

/* ── STEP 4 — Confirmation ── */
function StepConfirm({ path, property, mandate, created, error }: {
  path: PathId | null
  property: Property | null
  mandate: Mandate
  created: boolean
  error: string | null
}) {
  const pathLabel = PATHS.find(p => p.id === path)?.title || '—'
  return (
    <div className="nd-step nd-step-confirm">
      <div className="nd-form">
        <div className="confirm-card">
          <div className="cc-head">
            <div className="eyebrow">Nouveau dossier</div>
            <h2>{property?.addr || '—'}</h2>
            <div className="cc-sub">{property?.city}{property?.city ? ', Montréal' : ''} — {property?.type}</div>
          </div>

          <div className="cc-section">
            <h4>Propriété</h4>
            <div className="cc-grid">
              <KVP k="Adresse"        v={property?.addr || '—'}/>
              <KVP k="Cadastre"       v={property?.cadastre || '—'}/>
              <KVP k="Type"           v={property?.type || '—'}/>
              <KVP k="Année"          v={property?.year ?? '—'}/>
              <KVP k="Superficie"     v={property?.area ? `${fmtNum(property.area)} pi²` : '—'}/>
              <KVP k="Rôle municipal" v={property?.roll ? formatCAD(property.roll) : '—'}/>
            </div>
          </div>

          <div className="cc-section">
            <h4>Mandat</h4>
            <div className="cc-grid">
              <KVP k="Type"           v={mandate.type}/>
              <KVP k="Modèle"         v={mandate.modele}/>
              <KVP k="Client"         v={mandate.client || '—'}/>
              <KVP k="Représentant"   v={mandate.contact || '—'}/>
              <KVP k="Date de valeur" v={mandate.dateValeur}/>
              <KVP k="Échéance"       v={mandate.dateEcheance || '—'}/>
            </div>
          </div>

          {mandate.notes && (
            <div className="cc-section">
              <h4>Notes</h4>
              <p className="cc-notes">{mandate.notes}</p>
            </div>
          )}

          <div className="cc-foot">
            <div className="cc-foot-k">Méthode de démarrage</div>
            <div className="cc-foot-v">{pathLabel}</div>
          </div>
        </div>

        {created && (
          <div className="created-banner">
            <Icon.Check/>
            <div>
              <b>Dossier créé.</b> Redirection vers la fiche…
            </div>
          </div>
        )}
        {error && (
          <div
            style={{
              marginTop: 14,
              padding: '12px 16px',
              borderRadius: 'var(--r-md)',
              color: 'var(--oxblood)',
              background: 'rgba(138,48,48,.08)',
              border: '1px solid rgba(138,48,48,.15)',
              fontSize: 13.5,
            }}
          >
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
