/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

const TABS = [
  { id: "ventes",  label: "Ventes",  countKey: "VENTES"  },
  { id: "marches", label: "Marchés", countKey: "MARCHES" },
  { id: "couts",   label: "Coûts",   countKey: "COUTS"   },
  { id: "taux",    label: "Taux",    countKey: "TAUX"    }
];

function BibliothequePage() {
  const [tab, setTab] = useState("ventes");

  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  return (
    <div className="app" data-screen-label="03 Bibliothèque">
      <Sidebar active="bibliotheque" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">
        <div className="topbar biblio-topbar">
          <div className="crumbs">
            <span className="today">Mise à jour : 28 mai 2026</span>
          </div>

          <div className="pagehead biblio-head">
            <div>
              <h1>Bibliothèque</h1>
              <div className="subtitle">
                Données de référence — ventes, marchés, coûts et taux pour appuyer chaque évaluation.
              </div>
            </div>
            <div style={{display:"flex", gap:10}}>
              <button className="btn secondary">Exporter</button>
              <button className="btn accent"><Icon.Plus/> Importer</button>
            </div>
          </div>

          {/* Top tabs */}
          <div className="biblio-tabs">
            {TABS.map(t => {
              const count = (window[t.countKey] || []).length;
              return (
                <button
                  key={t.id}
                  className={`biblio-tab ${tab === t.id ? "active" : ""}`}
                  onClick={() => setTab(t.id)}>
                  <span className="label">{t.label}</span>
                  <span className="count numeric">{count}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="biblio-body">
          {tab === "ventes"  && <VentesTab/>}
          {tab === "marches" && <MarchesTab/>}
          {tab === "couts"   && <CoutsTab/>}
          {tab === "taux"    && <TauxTab/>}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   VENTES — filterable, sortable table of comparable sales
   ============================================================ */
function VentesTab() {
  const all = window.VENTES;
  const districts = window.DISTRICTS;
  const types = window.VENTE_TYPES;

  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("all");
  const [type, setType] = useState("all");
  const [sort, setSort] = useState("soldAt");
  const [sortDir, setSortDir] = useState("desc");

  const rows = useMemo(() => {
    let arr = all.slice();
    if (district !== "all") arr = arr.filter(v => v.district === district);
    if (type !== "all")     arr = arr.filter(v => v.type === type);
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      arr = arr.filter(v =>
        v.addr.toLowerCase().includes(q) ||
        v.district.toLowerCase().includes(q) ||
        v.type.toLowerCase().includes(q) ||
        v.id.toLowerCase().includes(q)
      );
    }
    const dir = sortDir === "asc" ? 1 : -1;
    arr.sort((a, b) => {
      switch (sort) {
        case "addr":     return a.addr.localeCompare(b.addr, "fr-CA") * (sortDir === "asc" ? 1 : -1);
        case "district": return a.district.localeCompare(b.district, "fr-CA") * (sortDir === "asc" ? 1 : -1);
        case "type":     return a.type.localeCompare(b.type, "fr-CA") * (sortDir === "asc" ? 1 : -1);
        case "year":     return (a.year - b.year) * dir;
        case "area":     return (a.area - b.area) * dir;
        case "price":    return (a.price - b.price) * dir;
        case "ppsf":     return ((a.ppsf || 0) - (b.ppsf || 0)) * dir;
        case "soldAt":
        default:         return a.soldAt.localeCompare(b.soldAt) * dir;
      }
    });
    return arr;
  }, [all, query, district, type, sort, sortDir]);

  function onSort(k) {
    if (sort === k) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSort(k); setSortDir(["addr","district","type"].includes(k) ? "asc" : "desc"); }
  }

  // Aggregate stats for the filtered set
  const stats = useMemo(() => {
    if (rows.length === 0) return null;
    const prices = rows.map(r => r.price);
    const ppsfs = rows.filter(r => r.ppsf).map(r => r.ppsf);
    const medianOf = arr => arr.slice().sort((a,b)=>a-b)[Math.floor(arr.length/2)];
    return {
      n: rows.length,
      medPrice: medianOf(prices),
      medPpsf: ppsfs.length ? medianOf(ppsfs) : null,
      minP: Math.min(...prices),
      maxP: Math.max(...prices)
    };
  }, [rows]);

  return (
    <>
      {/* Filter bar */}
      <div className="biblio-toolbar">
        <div className="search">
          <Icon.Glass/>
          <input
            type="text"
            placeholder="Rechercher une adresse, un quartier, un type…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          {query && <span className="kbd" onClick={() => setQuery("")} style={{cursor:"pointer"}}>esc</span>}
        </div>
        <Dropdown
          label="Quartier"
          value={district}
          onChange={setDistrict}
          options={[{ value: "all", label: "Tous" }, ...districts.map(d => ({ value: d, label: d }))]}
        />
        <Dropdown
          label="Type"
          value={type}
          onChange={setType}
          options={[{ value: "all", label: "Tous" }, ...types.map(t => ({ value: t, label: t }))]}
        />
        {(district !== "all" || type !== "all" || query) && (
          <button className="btn ghost" onClick={() => { setQuery(""); setDistrict("all"); setType("all"); }}>
            Réinitialiser
          </button>
        )}
      </div>

      {/* Stats */}
      {stats && (
        <div className="biblio-stats">
          <div className="stat">
            <div className="stat-k">Ventes filtrées</div>
            <div className="stat-v numeric">{stats.n}</div>
          </div>
          <div className="stat">
            <div className="stat-k">Médiane prix</div>
            <div className="stat-v numeric">{formatMoney(stats.medPrice)}</div>
          </div>
          <div className="stat">
            <div className="stat-k">Médiane $/pi²</div>
            <div className="stat-v numeric">{stats.medPpsf ? `${Math.round(stats.medPpsf)} $` : "—"}</div>
          </div>
          <div className="stat">
            <div className="stat-k">Étendue prix</div>
            <div className="stat-v numeric small">
              {formatMoney(stats.minP)} <span className="dash">–</span> {formatMoney(stats.maxP)}
            </div>
          </div>
        </div>
      )}

      {/* Results table */}
      <div className="biblio-table-wrap">
        <div className="biblio-table">
          <div className="bt-head">
            <SortHead k="addr"     sort={sort} dir={sortDir} onSort={onSort}>Adresse</SortHead>
            <SortHead k="district" sort={sort} dir={sortDir} onSort={onSort}>Quartier</SortHead>
            <SortHead k="type"     sort={sort} dir={sortDir} onSort={onSort}>Type</SortHead>
            <SortHead k="year"     sort={sort} dir={sortDir} onSort={onSort} align="right">Année</SortHead>
            <SortHead k="area"     sort={sort} dir={sortDir} onSort={onSort} align="right">Superficie</SortHead>
            <SortHead k="soldAt"   sort={sort} dir={sortDir} onSort={onSort}>Vendu</SortHead>
            <SortHead k="price"    sort={sort} dir={sortDir} onSort={onSort} align="right">Prix</SortHead>
            <SortHead k="ppsf"     sort={sort} dir={sortDir} onSort={onSort} align="right">$/pi²</SortHead>
            <div className="num-h">Utilisé</div>
          </div>
          {rows.map(v => (
            <div className="bt-row" key={v.id}>
              <div className="cell c-addr">
                <div className="addr">{v.addr}</div>
                <div className="meta numeric">{v.id} · {v.source}</div>
              </div>
              <div className="cell">{v.district}</div>
              <div className="cell muted">{v.type}</div>
              <div className="cell num">{v.year}</div>
              <div className="cell num">{formatNum(v.area)} pi²</div>
              <div className="cell">{v.soldLabel}</div>
              <div className="cell num strong">{formatMoney(v.price)}</div>
              <div className="cell num">{v.ppsf ? `${Math.round(v.ppsf)} $` : "—"}</div>
              <div className="cell num used">
                {v.used > 0
                  ? <span className="used-badge">{v.used}×</span>
                  : <span className="used-zero">—</span>}
              </div>
            </div>
          ))}
          {rows.length === 0 && (
            <div className="bt-empty">Aucune vente ne correspond à ces filtres.</div>
          )}
        </div>
      </div>
    </>
  );
}

function SortHead({ k, sort, dir, onSort, children, align = "left" }) {
  const active = sort === k;
  return (
    <button
      type="button"
      className={`sort-head ${active ? "active" : ""}`}
      onClick={() => onSort(k)}
      style={{justifyContent: align === "right" ? "flex-end" : "flex-start"}}>
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
   MARCHÉS — neighbourhood market indicators with sparklines
   ============================================================ */
function MarchesTab() {
  const data = window.MARCHES;
  return (
    <div className="marche-grid">
      {data.map(m => (
        <article className="marche-card" key={m.district}>
          <div className="mc-head">
            <h3>{m.district}</h3>
            <span className={`mc-ytd ${m.ytd >= 0 ? "pos" : "neg"}`}>
              {m.ytd > 0 ? "+" : ""}{m.ytd.toFixed(1)} %
            </span>
          </div>
          <div className="mc-median">
            <span className="mc-median-v numeric">{m.median}</span>
            <span className="mc-median-u">$ / pi²</span>
          </div>
          <Sparkline series={m.trend}/>
          <div className="mc-stats">
            <div>
              <div className="mc-k">Étendue</div>
              <div className="mc-v numeric">{m.ppsfLow}–{m.ppsfHigh} $</div>
            </div>
            <div>
              <div className="mc-k">DOM médian</div>
              <div className="mc-v numeric">{m.dom} j</div>
            </div>
            <div>
              <div className="mc-k">Ventes (12m)</div>
              <div className="mc-v numeric">{m.n}</div>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function Sparkline({ series }) {
  const w = 240, h = 44, pad = 4;
  const min = Math.min(...series), max = Math.max(...series);
  const range = max - min || 1;
  const pts = series.map((v, i) => {
    const x = pad + (i / (series.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return [x, y];
  });
  const d = pts.map((p, i) => (i === 0 ? "M" : "L") + p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
  const area = d + ` L${pts[pts.length-1][0].toFixed(1)},${h - pad} L${pts[0][0].toFixed(1)},${h - pad} Z`;
  const last = pts[pts.length - 1];
  return (
    <svg className="sparkline" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      <path d={area} fill="rgba(28,53,89,.08)"/>
      <path d={d} fill="none" stroke="var(--navy)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx={last[0]} cy={last[1]} r="2.4" fill="var(--navy)"/>
    </svg>
  );
}

/* ============================================================
   COÛTS — construction cost reference table
   ============================================================ */
function CoutsTab() {
  const data = window.COUTS;
  // Group by category
  const groups = data.reduce((acc, c) => {
    (acc[c.category] = acc[c.category] || []).push(c);
    return acc;
  }, {});

  return (
    <div className="couts-wrap">
      <div className="couts-intro">
        Coûts de remplacement neuf — utilisés pour l'approche par le coût.
        Toutes les valeurs sont en dollars canadiens.
      </div>
      {Object.entries(groups).map(([cat, rows]) => (
        <section className="couts-group" key={cat}>
          <h3>{cat}</h3>
          <div className="couts-table">
            <div className="ct-head">
              <div>Qualité</div>
              <div className="num">Taux</div>
              <div>Unité</div>
              <div>Source</div>
              <div>Mis à jour</div>
            </div>
            {rows.map((r, i) => (
              <div className="ct-row" key={i}>
                <div className="ct-quality">{r.quality}</div>
                <div className="num strong">{r.rate} $</div>
                <div className="muted">{r.unit}</div>
                <div className="muted">{r.source}</div>
                <div className="muted numeric">{r.updated}</div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

/* ============================================================
   TAUX — capitalization rates
   ============================================================ */
function TauxTab() {
  const data = window.TAUX;
  return (
    <>
      <div className="couts-intro">
        Taux de capitalisation observés — utilisés pour l'approche par les revenus.
        Plage typique par segment et secteur.
      </div>
      <div className="taux-grid">
        {data.map((t, i) => (
          <article className="taux-card" key={i}>
            <div className="tc-segment">{t.segment}</div>
            <div className="tc-zone">{t.zone}</div>
            <div className="tc-cap">
              <span className="tc-cap-v numeric">
                {t.capLow.toFixed(1)} <span className="dash">–</span> {t.capHigh.toFixed(1)}
              </span>
              <span className="tc-cap-u">% taux global</span>
            </div>
            <div className="tc-foot">
              <span className="tc-k">Vacance type</span>
              <span className="tc-v numeric">{t.vacancy.toFixed(1)} %</span>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<BibliothequePage/>);
