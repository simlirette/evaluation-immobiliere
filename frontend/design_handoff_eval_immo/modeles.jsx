/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

const MODELES = [
  {
    id: "hypo-res",
    title: "Hypothécaire — Résidentiel",
    cat: "résidentiel",
    desc: "Rapport narratif complet conforme aux exigences des prêteurs hypothécaires. Approches comparative et coût, attestation OEAQ.",
    sections: 8, pages: 32, docs: 6,
    used: 28, last: "12 mai 2026",
    norm: "OEAQ — Rapport narratif"
  },
  {
    id: "pre-vente",
    title: "Pré-vente — Résidentiel",
    cat: "résidentiel",
    desc: "Évaluation orientée vendeur. Étude de marché élargie, fourchette de prix de mise en vente, recommandations stratégiques.",
    sections: 6, pages: 22, docs: 4,
    used: 14, last: "28 avril 2026",
    norm: "OEAQ — Rapport narratif"
  },
  {
    id: "successoral",
    title: "Successoral & donation",
    cat: "résidentiel",
    desc: "Valeur marchande à une date passée précise. Justification de la date de valeur, comparables historiques, attestation notariale.",
    sections: 7, pages: 26, docs: 5,
    used: 9, last: "3 mars 2026",
    norm: "OEAQ — Rapport narratif"
  },
  {
    id: "litige",
    title: "Litige & expropriation",
    cat: "spécialisé",
    desc: "Rapport d'expertise judiciaire. Analyse détaillée des trois approches, démonstration méthodologique, annexes substantielles.",
    sections: 11, pages: 64, docs: 12,
    used: 5, last: "18 février 2026",
    norm: "OEAQ — Rapport d'expert"
  },
  {
    id: "revenus",
    title: "Acquisition — Immeuble à revenus",
    cat: "commercial",
    desc: "Approche par les revenus en méthode dominante. État des revenus et dépenses normalisé, taux de capitalisation justifié.",
    sections: 9, pages: 42, docs: 8,
    used: 7, last: "22 avril 2026",
    norm: "OEAQ — Rapport narratif"
  },
  {
    id: "avis",
    title: "Avis de valeur restreint",
    cat: "restreint",
    desc: "Rapport court à portée limitée. Une seule approche, hypothèses explicites. Pour usage interne ou validation rapide.",
    sections: 4, pages: 8, docs: 2,
    used: 18, last: "26 mai 2026",
    norm: "OEAQ — Avis de valeur"
  }
];

function ModelesPage() {
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  // Sort by usage
  const [sort, setSort] = useState("used");
  const sorted = useMemo(() => {
    const arr = MODELES.slice();
    if (sort === "used")  arr.sort((a, b) => b.used - a.used);
    if (sort === "alpha") arr.sort((a, b) => a.title.localeCompare(b.title, "fr-CA"));
    if (sort === "last")  arr.sort((a, b) => b.last.localeCompare(a.last));
    return arr;
  }, [sort]);

  return (
    <div className="app" data-screen-label="04 Modèles">
      <Sidebar active="modeles" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">
        <div className="topbar modeles-topbar">
          <div className="crumbs">
            <span className="today">{MODELES.length} modèles disponibles</span>
          </div>

          <div className="pagehead modeles-head">
            <div>
              <h1>Modèles</h1>
              <div className="subtitle">
                Un point de départ pour chaque type de mandat — conformes aux exigences de l'OEAQ.
              </div>
            </div>
            <div style={{display:"flex", gap:10, alignItems:"center"}}>
              <div className="sort-select" style={{padding: 0}}>
                <span className="label">Trier par</span>
                <select value={sort} onChange={e => setSort(e.target.value)}>
                  <option value="used">Plus utilisés</option>
                  <option value="alpha">Nom (A–Z)</option>
                  <option value="last">Modifié récemment</option>
                </select>
              </div>
              <button className="btn accent"><Icon.Plus/> Nouveau modèle</button>
            </div>
          </div>
        </div>

        <div className="modeles-body">
          <div className="modeles-grid">
            {sorted.map(m => <ModelCard key={m.id} m={m}/>)}
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelCard({ m }) {
  return (
    <article className="model-card" data-screen-label={`Modèle ${m.id}`}>
      <div className="mc-head">
        <span className={`mc-cat cat-${m.cat}`}>{m.cat}</span>
        <button className="mc-action" title="Options" onClick={(e) => e.stopPropagation()}>
          <Icon.More/>
        </button>
      </div>

      <h2 className="mc-title">{m.title}</h2>
      <p className="mc-desc">{m.desc}</p>

      <div className="mc-stats">
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.sections}</div>
          <div className="mc-stat-k">sections</div>
        </div>
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.pages}</div>
          <div className="mc-stat-k">pages env.</div>
        </div>
        <div className="mc-stat">
          <div className="mc-stat-v numeric">{m.docs}</div>
          <div className="mc-stat-k">documents</div>
        </div>
      </div>

      <div className="mc-foot">
        <div className="mc-norm">
          <Icon.Seal/>
          <span>{m.norm}</span>
        </div>
        <div className="mc-meta">
          <span className="mc-meta-l">Utilisé dans <b className="numeric">{m.used}</b> dossier{m.used > 1 ? "s" : ""}</span>
          <span className="mc-meta-d">Mod. {m.last}</span>
        </div>
      </div>

      <div className="mc-actions">
        <button className="btn ghost">Aperçu</button>
        <button className="btn secondary">Démarrer un dossier</button>
      </div>
    </article>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<ModelesPage/>);
