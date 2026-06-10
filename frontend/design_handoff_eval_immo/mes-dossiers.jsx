/* eslint-disable */
const { useState, useMemo, useEffect } = React;

const STATE_OPTIONS = [
  { id: "success", label: "Normal" },
  { id: "loading", label: "Chargement" },
  { id: "empty",   label: "Vide" },
  { id: "error",   label: "Erreur" },
  { id: "partial", label: "Partiel" }
];

function App() {
  const [query, setQuery]       = useState("");
  const [statusFilter, setStatusFilter] = useState("all"); // all | brouillon | encours | complet
  const [sort, setSort]         = useState("modified");    // modified | alpha | created | value | type | year | area | client
  const [sortDir, setSortDir]   = useState("desc");        // asc | desc
  const [view, setView]         = useState("grid");        // grid | rows
  const [viewState, setViewState] = useState("success");
  const [dossiers, setDossiers] = useState(window.DOSSIERS);

  const counts = useMemo(() => {
    const all = dossiers.length;
    const c = { dossiers: all, all, brouillon: 0, encours: 0, complet: 0 };
    for (const d of dossiers) c[d.status]++;
    return c;
  }, [dossiers]);

  const pinnedDossiers = useMemo(
    () => dossiers.filter(d => d.pinned),
    [dossiers]
  );
  const recentDossiers = useMemo(
    () => dossiers.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    [dossiers]
  );

  const filtered = useMemo(() => {
    let arr = dossiers.slice();
    if (statusFilter !== "all") arr = arr.filter(d => d.status === statusFilter);
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      arr = arr.filter(d =>
        d.addr.toLowerCase().includes(q) ||
        d.city.toLowerCase().includes(q) ||
        d.type.toLowerCase().includes(q) ||
        d.client.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q)
      );
    }
    arr.sort((a, b) => {
      // pinned first regardless of sort
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      const dir = sortDir === "asc" ? 1 : -1;
      const cmpStr = (x, y) => (x || "").localeCompare(y || "", "fr-CA");
      const cmpNum = (x, y) => (x ?? -Infinity) - (y ?? -Infinity);
      switch (sort) {
        case "alpha":    return cmpStr(a.addr, b.addr) * (sortDir === "asc" ? 1 : -1);
        case "type":     return cmpStr(a.type, b.type) * (sortDir === "asc" ? 1 : -1);
        case "client":   return cmpStr(a.client, b.client) * (sortDir === "asc" ? 1 : -1);
        case "year":     return cmpNum(a.year, b.year) * dir;
        case "area":     return cmpNum(a.area, b.area) * dir;
        case "stage":    return (cmpNum(a.stage, b.stage) || cmpNum(a.value, b.value)) * dir;
        case "created":  return cmpStr(a.createdAt, b.createdAt) * dir;
        case "value":    return cmpNum(a.value, b.value) * dir;
        case "modified":
        default:         return cmpStr(a.modifiedAt, b.modifiedAt) * dir;
      }
    });
    return arr;
  }, [dossiers, query, statusFilter, sort, sortDir]);

  function onSort(key) {
    if (sort === key) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSort(key);
      // text fields default ascending, numeric/date default descending
      setSortDir(["alpha", "type", "client"].includes(key) ? "asc" : "desc");
    }
  }

  function onPin(id) {
    setDossiers(ds => ds.map(d => d.id === id ? { ...d, pinned: !d.pinned } : d));
  }

  function clearFilters() {
    setQuery("");
    setStatusFilter("all");
  }

  // Today, Quebec formatted
  const today = new Date(2026, 4, 27); // 27 mai 2026
  const todayStr = today.toLocaleDateString("fr-CA", {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  });

  return (
    <div className="app" data-screen-label="01 Dossiers">
      <Sidebar active="dossiers" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">

        {/* Page head */}
        <div className="topbar">
          <div className="crumbs">
            <span className="today">{todayStr}</span>
          </div>
          <div className="pagehead">
            <div>
              <h1>Dossiers</h1>
            </div>
            <div style={{display:"flex", gap:10}}>
              <button className="btn secondary">Importer un dossier</button>
              <a href="nouveau-dossier.html" className="btn accent" style={{textDecoration:"none"}}>
                <Icon.Plus/> Nouveau dossier
              </a>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="toolbar">
          <div className="search">
            <Icon.Glass/>
            <input
              type="text"
              placeholder="Rechercher par adresse, quartier, client ou nº de dossier…"
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
            {query && <span className="kbd" onClick={() => setQuery("")} style={{cursor:"pointer"}}>esc</span>}
          </div>

          <div className="filter-pills">
            <button className={`pill ${statusFilter === "all" ? "active" : ""}`} onClick={() => setStatusFilter("all")}>
              <span>Tous</span><span className="count">{counts.all}</span>
            </button>
            <button className={`pill ${statusFilter === "encours" ? "active" : ""}`} onClick={() => setStatusFilter("encours")}>
              <span>En cours</span><span className="count">{counts.encours}</span>
            </button>
            <button className={`pill ${statusFilter === "complet" ? "active" : ""}`} onClick={() => setStatusFilter("complet")}>
              <span>Complets</span><span className="count">{counts.complet}</span>
            </button>
            <button className={`pill ${statusFilter === "brouillon" ? "active" : ""}`} onClick={() => setStatusFilter("brouillon")}>
              <span>Brouillons</span><span className="count">{counts.brouillon}</span>
            </button>
          </div>

          <div className="sort-select">
            <span className="label">Trier par</span>
            <select value={sort} onChange={e => setSort(e.target.value)}>
              <option value="modified">Modifié récemment</option>
              <option value="created">Créé récemment</option>
              <option value="alpha">Adresse (A–Z)</option>
              <option value="value">Valeur (décroissant)</option>
            </select>
          </div>

          <div className="view-toggle">
            <button className={view === "grid" ? "active" : ""} title="Vue en grille" onClick={() => setView("grid")}>
              <Icon.Grid/>
            </button>
            <button className={view === "rows" ? "active" : ""} title="Vue en liste" onClick={() => setView("rows")}>
              <Icon.Rows/>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="grid-wrap">
          {viewState === "loading" && <LoadingState/>}
          {viewState === "error"   && <ErrorState/>}
          {viewState === "empty"   && <EmptyState/>}
          {(viewState === "success" || viewState === "partial") && (
            <>
              {filtered.length === 0 ? (
                <NoResultsState query={query} onClear={clearFilters}/>
              ) : (
                <div className={view === "grid" ? "card-grid" : "card-list"}>
                  {viewState === "partial" && (
                    <div className="partial-banner">
                      <span className="pulse"/>
                      <div>
                        <b>Mise à jour partielle.</b>{" "}
                        <span style={{fontStyle:"italic", color:"var(--ink-mute)"}}>
                          3 dossiers sur 12 ont été synchronisés avec le registre OEAQ.
                          L'enrichissement automatique se poursuit en arrière-plan.
                        </span>
                      </div>
                      <span className="numeric eyebrow" style={{marginLeft:"auto"}}>3 / 12</span>
                    </div>
                  )}
                  {view === "rows" && (
                    <div className="list-head">
                      <SortHead k="alpha"    sort={sort} dir={sortDir} onSort={onSort}>Adresse</SortHead>
                      <SortHead k="type"     sort={sort} dir={sortDir} onSort={onSort}>Type</SortHead>
                      <SortHead k="year"     sort={sort} dir={sortDir} onSort={onSort}>Année</SortHead>
                      <SortHead k="area"     sort={sort} dir={sortDir} onSort={onSort}>Superficie</SortHead>
                      <SortHead k="stage"    sort={sort} dir={sortDir} onSort={onSort}>Stade / Valeur</SortHead>
                      <SortHead k="client"   sort={sort} dir={sortDir} onSort={onSort}>Client</SortHead>
                      <SortHead k="modified" sort={sort} dir={sortDir} onSort={onSort}>Modifié</SortHead>
                      <div></div>
                    </div>
                  )}
                  {filtered.map(d => view === "grid"
                    ? <DossierCard key={d.id} d={d} onPin={onPin}/>
                    : <DossierRow  key={d.id} d={d} onPin={onPin}/>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Dev affordance — switch between UI states */}
      <div className="state-switcher">
        <span className="label">État</span>
        {STATE_OPTIONS.map(s => (
          <button
            key={s.id}
            className={viewState === s.id ? "active" : ""}
            onClick={() => setViewState(s.id)}>
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   Sortable list-head cell
   ============================================================ */
function SortHead({ k, sort, dir, onSort, children }) {
  const active = sort === k;
  return (
    <button
      type="button"
      className={`sort-head ${active ? "active" : ""}`}
      onClick={() => onSort(k)}>
      <span>{children}</span>
      <span className={`caret ${active ? (dir === "asc" ? "asc" : "desc") : ""}`}>
        <svg viewBox="0 0 10 6" width="9" height="6" aria-hidden="true">
          <path d="M0 1l5 4 5-4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </span>
    </button>
  );
}

/* ============================================================
   State views
   ============================================================ */
function LoadingState() {
  return (
    <div className="skeleton-grid">
      {Array.from({length: 6}).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="body">
            <div className="line w2"/>
            <div className="line w1"/>
            <div className="line w3"/>
            <div style={{height: 8}}/>
            <div className="line w2"/>
          </div>
        </div>
      ))}
    </div>
  );
}

function ErrorState() {
  return (
    <div className="state">
      <div className="seal" style={{borderColor: "var(--oxblood)", color: "var(--oxblood)"}}>!</div>
      <h2>Connexion <em style={{color:"var(--oxblood)"}}>interrompue</em></h2>
      <p>
        Le registre des évaluations de l'OEAQ n'a pas répondu. Vos dossiers locaux sont
        intacts ; seule la synchronisation est en pause.
      </p>
      <div className="actions">
        <button className="btn">Réessayer la connexion</button>
        <button className="btn secondary">Travailler hors ligne</button>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="state">
      <div className="seal">É.A.</div>
      <h2>Aucun dossier <em>ouvert</em>.</h2>
      <p>
        Commencez votre premier dossier d'évaluation. Vous pourrez importer les
        données du rôle d'évaluation ou saisir manuellement les caractéristiques de la propriété.
      </p>
      <div className="actions">
        <button className="btn accent"><Icon.Plus/> Nouveau dossier</button>
        <button className="btn secondary">Importer depuis le rôle</button>
      </div>
    </div>
  );
}

function NoResultsState({ query, onClear }) {
  return (
    <div className="state" style={{padding:"60px 40px"}}>
      <div className="seal" style={{width:72, height:72, fontSize:14}}>—</div>
      <h2>Aucun résultat</h2>
      <p>
        Aucun dossier ne correspond à
        {query ? <> «&nbsp;<i style={{color:"var(--ink)"}}>{query}</i>&nbsp;»</> : " ces filtres"}.
        Essayez d'élargir votre recherche ou de retirer un filtre.
      </p>
      <div className="actions">
        <button className="btn secondary" onClick={onClear}>Réinitialiser les filtres</button>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
