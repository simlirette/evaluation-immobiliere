/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

const STEPS = [
  { n: 1, label: "Point de départ" },
  { n: 2, label: "Propriété" },
  { n: 3, label: "Mandat" },
  { n: 4, label: "Confirmation" }
];

const PATHS = [
  {
    id: "search",
    title: "Rechercher une propriété",
    desc: "Trouvez l'immeuble dans le registre municipal et importez automatiquement les caractéristiques du rôle d'évaluation.",
    badge: "Recommandé",
    icon: "search"
  },
  {
    id: "manual",
    title: "Saisir manuellement",
    desc: "Entrez l'adresse et les caractéristiques de la propriété à la main. Utile lorsque le rôle n'est pas à jour.",
    icon: "edit"
  },
  {
    id: "import",
    title: "Importer un document",
    desc: "Importez un mandat, un rôle municipal ou une fiche Centris en PDF. Les champs seront extraits automatiquement.",
    badge: "Bêta",
    icon: "import"
  },
  {
    id: "template",
    title: "Démarrer d'un modèle",
    desc: "Reprenez la structure d'un mandat précédent — utile pour les évaluations en série ou les nouveaux contrats récurrents.",
    icon: "template"
  }
];

const MANDATE_TYPES = [
  "Hypothécaire",
  "Pré-vente",
  "Successoral",
  "Donation",
  "Litige",
  "Acquisition",
  "Refinancement",
  "Expropriation"
];

const MODELES = [
  "Hypothécaire — Résidentiel",
  "Pré-vente — Résidentiel",
  "Successoral & donation",
  "Litige & expropriation",
  "Acquisition — Immeuble à revenus",
  "Avis de valeur restreint"
];

const CLIENTS = [
  "Banque Nationale du Canada",
  "Caisse Desjardins — Outremont",
  "RBC — Refinancement",
  "Étude Goldberg, avocats",
  "Me Anne Beauchamp, notaire",
  "Cabinet Lévesque & Tremblay"
];

// Mock address search index
const ADDRESS_INDEX = [
  { addr: "245, av. Wiseman",        city: "Outremont",          cadastre: "1 870 421", year: 1948, area: 1842, lot: 4820, type: "Maison unifamiliale", roll: 1185000 },
  { addr: "312, av. Bloomfield",     city: "Outremont",          cadastre: "1 870 412", year: 1936, area: 1920, lot: 4200, type: "Maison unifamiliale", roll: 1240000 },
  { addr: "198, av. Outremont",      city: "Outremont",          cadastre: "1 870 388", year: 1936, area: 1720, lot: 3650, type: "Maison unifamiliale", roll: 1095000 },
  { addr: "4218, rue Cartier",       city: "Plateau-Mont-Royal", cadastre: "1 872 104", year: 1923, area: 2410, lot: 2100, type: "Duplex",              roll: 685000 },
  { addr: "67, av. Wood",            city: "Westmount",          cadastre: "1 869 022", year: 1912, area: 3240, lot: 6200, type: "Maison unifamiliale", roll: 2105000 },
  { addr: "5412, av. de l'Esplanade",city: "Mile End",           cadastre: "1 873 542", year: 1918, area: 2580, lot: 2400, type: "Duplex",              roll: 805000 },
  { addr: "8124, rue de Lanaudière", city: "Villeray",           cadastre: "1 875 219", year: 1958, area: 2640, lot: 2900, type: "Triplex",             roll: 615000 }
];

function NouveauDossierPage() {
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  const [step, setStep] = useState(1);
  const [path, setPath] = useState(null);
  const [property, setProperty] = useState(null);
  const [mandate, setMandate] = useState({
    type: "Hypothécaire",
    client: "",
    contact: "",
    phone: "",
    email: "",
    dateValeur: "2026-05-28",
    dateEcheance: "",
    modele: "Hypothécaire — Résidentiel",
    notes: ""
  });
  const [created, setCreated] = useState(false);

  const canAdvance = (
    step === 1 ? !!path :
    step === 2 ? !!property :
    step === 3 ? !!mandate.type && !!mandate.client && !!mandate.dateValeur :
    true
  );

  function next() { if (canAdvance && step < 4) setStep(s => s + 1); }
  function prev() { if (step > 1) setStep(s => s - 1); }

  function create() {
    setCreated(true);
    // In a real app, we'd navigate to the new dossier.
    setTimeout(() => {
      window.location.href = "dossier.html?id=2026-0418";
    }, 1200);
  }

  return (
    <div className="app" data-screen-label="06 Nouveau dossier">
      <Sidebar active="nouveau" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

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
            {STEPS.map((s) => {
              const state = s.n < step ? "done" : s.n === step ? "now" : "upcoming";
              return (
                <button
                  key={s.n}
                  className={`step ${state}`}
                  onClick={() => { if (s.n < step) setStep(s.n); }}>
                  {state === "done"
                    ? <Icon.Check/>
                    : <span className="num numeric">{String(s.n).padStart(2, "0")}</span>}
                  <span className="label">{s.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="nd-body">
          {step === 1 && <StepPath path={path} setPath={setPath} onAdvance={next}/>}
          {step === 2 && <StepProperty property={property} setProperty={setProperty} path={path}/>}
          {step === 3 && <StepMandate mandate={mandate} setMandate={setMandate}/>}
          {step === 4 && <StepConfirm path={path} property={property} mandate={mandate} created={created}/>}
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
                  {created ? "Création…" : "Créer le dossier"}
                </button>}
          </div>
        </div>
      </div>
    </div>
  );
}

function stepSubtitle(step) {
  switch (step) {
    case 1: return "Comment souhaitez-vous démarrer ce dossier ?";
    case 2: return "Identifier la propriété à évaluer.";
    case 3: return "Préciser le mandat et le client.";
    case 4: return "Vérifiez les informations avant de créer le dossier.";
    default: return "";
  }
}

function ChevronRight() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 4l4 4-4 4"/>
    </svg>
  );
}

/* ============================================================
   STEP 1 — Pick a starting path
   ============================================================ */
function StepPath({ path, setPath, onAdvance }) {
  return (
    <div className="nd-step nd-step-path">
      <div className="nd-paths">
        {PATHS.map(p => (
          <button
            key={p.id}
            className={`path-card ${path === p.id ? "selected" : ""}`}
            onClick={() => setPath(p.id)}>
            <div className="path-icon">
              {p.icon === "search"   && <Icon.Glass/>}
              {p.icon === "edit"     && <Icon.Edit/>}
              {p.icon === "import"   && <Icon.Plus/>}
              {p.icon === "template" && <Icon.Template/>}
            </div>
            <div className="path-body">
              <div className="path-title">
                {p.title}
                {p.badge && <span className={`path-badge badge-${p.badge.toLowerCase()}`}>{p.badge}</span>}
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
  );
}

/* ============================================================
   STEP 2 — Property identification
   ============================================================ */
function StepProperty({ property, setProperty, path }) {
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    if (!query.trim()) return ADDRESS_INDEX.slice(0, 5);
    const q = query.trim().toLowerCase();
    return ADDRESS_INDEX.filter(x =>
      x.addr.toLowerCase().includes(q) ||
      x.city.toLowerCase().includes(q) ||
      x.cadastre.includes(q.replace(/\s/g, ""))
    );
  }, [query]);

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
              onChange={e => { setQuery(e.target.value); setProperty(null); }}
            />
          </div>
          <span className="nd-help">
            Recherche dans le registre municipal de Montréal. Les caractéristiques seront
            préchargées du rôle d'évaluation.
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
              <button className="btn ghost" onClick={() => { setProperty(null); setQuery(""); }}>
                Changer
              </button>
            </div>
            <div className="prev-grid">
              <KVP k="Cadastre"      v={property.cadastre}/>
              <KVP k="Type"          v={property.type}/>
              <KVP k="Année"         v={property.year}/>
              <KVP k="Superficie"    v={`${formatNum(property.area)} pi²`}/>
              <KVP k="Lot"           v={`${formatNum(property.lot)} pi²`}/>
              <KVP k="Rôle municipal" v={formatMoney(property.roll)}/>
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
  );
}

function KVP({ k, v }) {
  return (
    <div className="kvp">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  );
}

/* ============================================================
   STEP 3 — Mandate details
   ============================================================ */
function StepMandate({ mandate, setMandate }) {
  function up(field, v) { setMandate(m => ({ ...m, [field]: v })); }
  return (
    <div className="nd-step nd-step-mandate">
      <div className="nd-form nd-form-2col">
        <Section title="Mandat">
          <Field label="Type de mandat" required>
            <Dropdown
              value={mandate.type}
              onChange={v => up("type", v)}
              options={MANDATE_TYPES}
            />
          </Field>
          <Field label="Modèle de rapport">
            <Dropdown
              value={mandate.modele}
              onChange={v => up("modele", v)}
              options={MODELES}
            />
          </Field>
          <div className="nd-row-2">
            <Field label="Date de valeur" required>
              <input type="date"
                value={mandate.dateValeur}
                onChange={e => up("dateValeur", e.target.value)}
                onClick={e => e.currentTarget.showPicker?.()}/>
            </Field>
            <Field label="Échéance">
              <input type="date"
                value={mandate.dateEcheance}
                onChange={e => up("dateEcheance", e.target.value)}
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
              onChange={e => up("client", e.target.value)}
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
              onChange={e => up("contact", e.target.value)}
            />
          </Field>
          <div className="nd-row-2">
            <Field label="Téléphone">
              <input
                type="tel"
                placeholder="514 …"
                value={mandate.phone}
                onChange={e => up("phone", e.target.value)}
              />
            </Field>
            <Field label="Courriel">
              <input
                type="email"
                placeholder="prenom@org.ca"
                value={mandate.email}
                onChange={e => up("email", e.target.value)}
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
              onChange={e => up("notes", e.target.value)}
            />
          </Field>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children, full }) {
  return (
    <section className={`nd-section ${full ? "full" : ""}`}>
      <h3>{title}</h3>
      <div className="nd-section-body">{children}</div>
    </section>
  );
}

function Field({ label, required, children }) {
  return (
    <label className="nd-field">
      <span className="nd-k">{label}{required && <span className="req"> *</span>}</span>
      {children}
    </label>
  );
}

/* ============================================================
   STEP 4 — Confirmation
   ============================================================ */
function StepConfirm({ path, property, mandate, created }) {
  const pathLabel = PATHS.find(p => p.id === path)?.title || "—";
  return (
    <div className="nd-step nd-step-confirm">
      <div className="nd-form">
        <div className="confirm-card">
          <div className="cc-head">
            <div className="eyebrow">Nouveau dossier</div>
            <h2>{property?.addr || "—"}</h2>
            <div className="cc-sub">{property?.city}, Montréal — {property?.type}</div>
          </div>

          <div className="cc-section">
            <h4>Propriété</h4>
            <div className="cc-grid">
              <KVP k="Adresse"        v={property?.addr}/>
              <KVP k="Cadastre"       v={property?.cadastre}/>
              <KVP k="Type"           v={property?.type}/>
              <KVP k="Année"          v={property?.year}/>
              <KVP k="Superficie"     v={`${formatNum(property?.area)} pi²`}/>
              <KVP k="Rôle municipal" v={formatMoney(property?.roll)}/>
            </div>
          </div>

          <div className="cc-section">
            <h4>Mandat</h4>
            <div className="cc-grid">
              <KVP k="Type"           v={mandate.type}/>
              <KVP k="Modèle"         v={mandate.modele}/>
              <KVP k="Client"         v={mandate.client || "—"}/>
              <KVP k="Représentant"   v={mandate.contact || "—"}/>
              <KVP k="Date de valeur" v={mandate.dateValeur}/>
              <KVP k="Échéance"       v={mandate.dateEcheance || "—"}/>
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
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<NouveauDossierPage/>);
