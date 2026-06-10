/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

// Fake "all dossiers" count — only 25 sampled in data, but the firm has 142 archived total
const TOTAL_ARCHIVES = 142;

const MANDATE_OPTIONS = ["Tous", "Hypothécaire", "Pré-vente", "Successoral", "Litige", "Acquisition", "Donation", "Refinancement"];

function ArchivesPage() {
  const all = window.ARCHIVES;
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  const [query, setQuery] = useState("");
  const [year, setYear]   = useState("all");
  const [mandate, setMandate] = useState("Tous");

  const years = useMemo(() => {
    const ys = [...new Set(all.map(a => a.year))].sort((a, b) => b.localeCompare(a));
    return ys;
  }, [all]);

  const filtered = useMemo(() => {
    let arr = all.slice();
    if (year !== "all")     arr = arr.filter(a => a.year === year);
    if (mandate !== "Tous") arr = arr.filter(a => a.mandate === mandate);
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      arr = arr.filter(a =>
        a.addr.toLowerCase().includes(q) ||
        a.city.toLowerCase().includes(q) ||
        a.client.toLowerCase().includes(q) ||
        a.mandate.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q)
      );
    }
    arr.sort((a, b) => b.completedAt.localeCompare(a.completedAt));
    return arr;
  }, [all, query, year, mandate]);

  // Group by year
  const grouped = useMemo(() => {
    const g = {};
    for (const a of filtered) {
      (g[a.year] = g[a.year] || []).push(a);
    }
    return g;
  }, [filtered]);

  // Quick stats
  const totalValue = useMemo(() => filtered.reduce((s, a) => s + (a.value || 0), 0), [filtered]);

  // Counts per year (across full dataset, ignoring other filters)
  const yearCounts = useMemo(() => {
    const c = {};
    for (const a of all) c[a.year] = (c[a.year] || 0) + 1;
    return c;
  }, [all]);

  function clearFilters() { setQuery(""); setYear("all"); setMandate("Tous"); }
  const hasFilter = query || year !== "all" || mandate !== "Tous";

  return (
    <div className="app" data-screen-label="05 Archives">
      <Sidebar active="archives" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">
        <div className="topbar arch-topbar">
          <div className="crumbs">
            <span className="today">
              <span className="numeric">{TOTAL_ARCHIVES}</span> dossiers archivés
            </span>
          </div>

          <div className="pagehead arch-head">
            <div>
              <h1>Archives</h1>
              <div className="subtitle">
                Dossiers terminés, classés par année. Consultez, clonez ou exportez vos évaluations passées.
              </div>
            </div>
            <div style={{display:"flex", gap:10}}>
              <button className="btn secondary"><Icon.Print/> Exporter le registre</button>
            </div>
          </div>
        </div>

        <div className="arch-body">
          {/* Filter row */}
          <div className="arch-toolbar">
            <div className="search">
              <Icon.Glass/>
              <input
                type="text"
                placeholder="Rechercher par adresse, client ou nº de dossier…"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
              {query && <span className="kbd" onClick={() => setQuery("")} style={{cursor:"pointer"}}>esc</span>}
            </div>
            <Dropdown
              label="Mandat"
              value={mandate}
              onChange={setMandate}
              options={MANDATE_OPTIONS}
            />
            {hasFilter && (
              <button className="btn ghost" onClick={clearFilters}>Réinitialiser</button>
            )}
          </div>

          {/* Year pills */}
          <div className="year-strip">
            <button
              className={`year-pill ${year === "all" ? "active" : ""}`}
              onClick={() => setYear("all")}>
              <span className="y-label">Toutes années</span>
              <span className="y-count numeric">{all.length}</span>
            </button>
            {years.map(y => (
              <button
                key={y}
                className={`year-pill ${year === y ? "active" : ""}`}
                onClick={() => setYear(y)}>
                <span className="y-label numeric">{y}</span>
                <span className="y-count numeric">{yearCounts[y]}</span>
              </button>
            ))}
          </div>

          {/* Summary card */}
          {filtered.length > 0 && (
            <div className="arch-summary">
              <div>
                <span className="k">Affichage</span>
                <span className="v numeric">{filtered.length}</span>
                <span className="suffix">sur {all.length}</span>
              </div>
              <div>
                <span className="k">Valeur totale évaluée</span>
                <span className="v numeric">{formatMoney(totalValue)}</span>
              </div>
              <div>
                <span className="k">Plus récent</span>
                <span className="v">{filtered[0].completedLabel}</span>
              </div>
              <div>
                <span className="k">Plus ancien</span>
                <span className="v">{filtered[filtered.length - 1].completedLabel}</span>
              </div>
            </div>
          )}

          {/* Results — grouped by year */}
          {filtered.length === 0 ? (
            <div className="arch-empty">
              <div className="empty-seal">—</div>
              <h3>Aucune archive ne correspond à ces filtres.</h3>
              <button className="btn secondary" onClick={clearFilters}>Réinitialiser les filtres</button>
            </div>
          ) : (
            <div className="arch-groups">
              {Object.entries(grouped)
                .sort(([a], [b]) => b.localeCompare(a))
                .map(([yr, items]) => (
                <section className="arch-group" key={yr}>
                  <div className="ag-head">
                    <div className="ag-year numeric">{yr}</div>
                    <div className="ag-count">
                      <span className="numeric">{items.length}</span> dossier{items.length > 1 ? "s" : ""}
                    </div>
                  </div>
                  <div className="ag-list">
                    {items.map(a => <ArchiveRow key={a.id} a={a}/>)}
                  </div>
                </section>
              ))}
            </div>
          )}

          {/* Showing N of total */}
          {filtered.length > 0 && filtered.length < TOTAL_ARCHIVES && !hasFilter && (
            <div className="arch-more">
              <span>Affichage de <b className="numeric">{filtered.length}</b> sur <b className="numeric">{TOTAL_ARCHIVES}</b> dossiers archivés</span>
              <button className="btn secondary">Charger plus</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ArchiveRow({ a }) {
  return (
    <article className="arch-row" data-screen-label={`Archive ${a.id}`}>
      <div className="ar-date">
        <div className="ar-day numeric">{a.completedAt.slice(8, 10)}</div>
        <div className="ar-month">{a.completedLabel.split(" ")[1]}</div>
      </div>
      <div className="ar-main">
        <div className="ar-addr">{a.addr}</div>
        <div className="ar-meta">
          <span>{a.city}</span>
          <span className="dot-sep">·</span>
          <span>{a.type}</span>
          <span className="dot-sep">·</span>
          <span className="numeric">{a.year}</span>
          <span className="dot-sep">·</span>
          <span className="numeric">{formatNum(a.area)} pi²</span>
        </div>
      </div>
      <div className="ar-mandate">
        <span className={`m-pill mandate-${slug(a.mandate)}`}>{a.mandate}</span>
      </div>
      <div className="ar-client">{a.client}</div>
      <div className="ar-value numeric">{formatMoney(a.value)}</div>
      <div className="ar-id numeric">{a.id}</div>
      <div className="ar-actions">
        <button className="btn ghost btn-sm">Voir</button>
        <button className="btn ghost btn-sm">Cloner</button>
      </div>
    </article>
  );
}

function slug(s) {
  return s.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-");
}

ReactDOM.createRoot(document.getElementById("root")).render(<ArchivesPage/>);
