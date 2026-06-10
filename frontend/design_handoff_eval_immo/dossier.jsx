/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

function DossierPage() {
  const urlId = new URLSearchParams(location.search).get("id") || "2026-0418";
  const d = (window.DOSSIERS.find(x => x.id === urlId)) || window.DOSSIERS[0];
  const ext = window.DOSSIER_DETAILS[d.id] || window.DOSSIER_DETAILS["2026-0418"];

  // Sidebar context
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  const [stage, setStage] = useState(d.stage || 3);

  // Route to the active stage view
  const StageView = (
    stage === 1 ? StageDossier  :
    stage === 2 ? StageMarche   :
    stage === 3 ? StageAnalyse  :
    stage === 4 ? StageSynthese :
                  StageRapport
  );

  return (
    <div className="app" data-screen-label={`02 Dossier ${d.id}`}>
      <Sidebar active="dossiers" counts={counts} pinned={pinnedDossiers} recents={recentDossiers} currentDossier={d}/>

      <div className="main">
        {/* Topbar */}
        <div className="topbar dossier-topbar">
          <div className="pagehead dossier-head">
            <div className="head-left">
              <h1>
                {d.addr}
                <span className="head-id numeric">{d.id}</span>
              </h1>
              <div className="head-meta">
                <span>{d.city}, Montréal</span>
                <span className="dot-sep">·</span>
                <span>{d.type}</span>
                <span className="dot-sep">·</span>
                <span className="numeric">{d.year}</span>
                <span className="dot-sep">·</span>
                <span className="numeric">{formatNum(d.area)} pi²</span>
              </div>
            </div>
            <div className="head-actions">
              <button className="btn ghost"><Icon.Print/> Imprimer</button>
              <button className="btn secondary"><Icon.Share/> Partager</button>
              <button className="btn accent">Reprendre</button>
            </div>
          </div>

          <Stepper current={stage} onJump={setStage} status={d.status}/>
        </div>

        {/* Body */}
        <div className="dossier-body">
          <div className="dossier-main">
            <StageView d={d} ext={ext}/>
          </div>

          {/* Aside — kept consistent across stages */}
          <aside className="dossier-aside">
            <SideCard title="Faits saillants">
              <FactRow k="Type"          v={d.type}/>
              <FactRow k="Année"         v={d.year} numeric/>
              <FactRow k="Superficie"    v={`${formatNum(d.area)} pi²`} numeric/>
              <FactRow k="Lot"           v={`${formatNum(ext.lotArea)} pi²`} numeric/>
              <FactRow k="Étages"        v={ext.stories}/>
              <FactRow k="Chambres"      v={ext.bedrooms}/>
              <FactRow k="Salles de bain" v={ext.bathrooms}/>
              <FactRow k="Stationnement" v={ext.parking}/>
              <FactRow k="Rénovation"    v={ext.yearReno} numeric/>
              <FactRow k="Cadastre"      v={ext.cadastral} numeric/>
              <FactRow k="Rôle municipal" v={formatMoney(ext.municipalRoll)} numeric/>
            </SideCard>

            <SideCard title="Mandat & client">
              <div className="client-block">
                <div className="client-org">{ext.contact.org}</div>
                <div className="client-person">{ext.contact.person}</div>
                <div className="client-role">{ext.contact.role}</div>
                <div className="client-contact">
                  <a>{ext.contact.phone}</a>
                  <span className="dot-sep">·</span>
                  <a>{ext.contact.email}</a>
                </div>
              </div>
              <div className="mandate-tag">
                <span className="dot"/> {d.mandate}
              </div>
            </SideCard>

            <SideCard title="Activité" tight>
              <ul className="activity">
                {ext.activity.map((a, i) => (
                  <li key={i}>
                    <div className="when">{a.when}</div>
                    <div className="what">
                      <span className="who">{a.who}</span> {a.what}
                    </div>
                  </li>
                ))}
              </ul>
            </SideCard>

            <SideCard title={`Documents (${ext.documents.length})`} tight>
              <ul className="docs">
                {ext.documents.map((doc, i) => (
                  <li key={i}>
                    <div className={`doc-icon doc-${doc.type}`}>{doc.type.toUpperCase()}</div>
                    <div className="doc-info">
                      <div className="doc-name">{doc.name}</div>
                      <div className="doc-meta">{doc.size} · {doc.when}</div>
                    </div>
                  </li>
                ))}
              </ul>
              <button className="btn ghost btn-full"><Icon.Plus/> Ajouter un document</button>
            </SideCard>
          </aside>
        </div>

        {/* Agent chat — persistent across stages */}
        <AgentChat stage={stage}/>
      </div>
    </div>
  );
}

/* ============================================================
   Stage stepper (tabs with rounded box on active)
   ============================================================ */
function Stepper({ current, onJump }) {
  const stages = [
    { n: 1, label: "Dossier" },
    { n: 2, label: "Marché"  },
    { n: 3, label: "Analyse" },
    { n: 4, label: "Synthèse" },
    { n: 5, label: "Rapport" }
  ];
  return (
    <div className="stepper">
      {stages.map((s) => {
        const state = s.n < current ? "done" : s.n === current ? "now" : "upcoming";
        return (
          <button key={s.n} className={`step ${state}`} onClick={() => onJump(s.n)}>
            {state === "done"
              ? <Icon.Check/>
              : <span className="num numeric">{String(s.n).padStart(2, "0")}</span>}
            <span className="label">{s.label}</span>
          </button>
        );
      })}
    </div>
  );
}

/* ============================================================
   Side card + Fact row
   ============================================================ */
function SideCard({ title, children, tight }) {
  return (
    <section className={`side-card ${tight ? "tight" : ""}`}>
      <h3>{title}</h3>
      <div className="side-card-body">{children}</div>
    </section>
  );
}

function FactRow({ k, v, numeric }) {
  return (
    <div className="fact-row">
      <div className="k">{k}</div>
      <div className={`v ${numeric ? "numeric" : ""}`}>{v ?? "—"}</div>
    </div>
  );
}

/* ============================================================
   Agent chat — persistent composer at the bottom of the workspace
   ============================================================ */
const STAGE_PROMPTS = {
  1: "Demander à l'agent — vérifier les caractéristiques, suggérer des documents manquants…",
  2: "Demander à l'agent — trouver d'autres comparables, ajuster pour superficie ou état…",
  3: "Demander à l'agent — proposer une pondération, valider les approches…",
  4: "Demander à l'agent — rédiger le narratif, vérifier l'attestation…",
  5: "Demander à l'agent — relire le rapport, suggérer des corrections…"
};

const STAGE_SUGGESTIONS = {
  1: ["Photos manquantes ?", "Vérifier le cadastre", "Importer le rôle"],
  2: ["Élargir le rayon à 1,5 km", "Ajuster pour l'année", "Comparables sur 24 mois"],
  3: ["Pondération recommandée ?", "Comparer aux ventes récentes", "Justifier l'écart coût/marché"],
  4: ["Rédiger un narratif", "Vérifier la fourchette", "Préparer l'attestation"],
  5: ["Aperçu PDF", "Vérifier la mise en page", "Annexes manquantes ?"]
};

function AgentChat({ stage }) {
  const [value, setValue] = useState("");
  const inputRef = useRef(null);

  function pick(s) {
    setValue(s);
    inputRef.current?.focus();
  }

  return (
    <div className="agent-chat-wrap" data-screen-label="Agent Chat">
      <div className="agent-chat">
        <div className="agent-suggestions">
          <span className="agent-sparkle"><Icon.Sparkle/></span>
          {(STAGE_SUGGESTIONS[stage] || []).map((s, i) => (
            <button key={i} className="suggestion" onClick={() => pick(s)}>{s}</button>
          ))}
        </div>
        <form className="agent-input" onSubmit={(e) => { e.preventDefault(); setValue(""); }}>
          <button type="button" className="attach" aria-label="Joindre un fichier" title="Joindre une pièce jointe">
            <Icon.Paperclip/>
          </button>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={STAGE_PROMPTS[stage] || "Demander à l'agent…"}
          />
          <button type="submit" className={`send ${value.trim() ? "ready" : ""}`} aria-label="Envoyer">
            <Icon.Send/>
          </button>
        </form>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<DossierPage/>);
