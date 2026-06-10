/* eslint-disable */
/* ============================================================
   Éval Immo — Dossier stage views
   1. Dossier  — intake / property data
   2. Marché   — comparable analysis
   3. Analyse  — three approaches reconciliation
   4. Synthèse — final value & sign-off
   5. Rapport  — report preview & export
   ============================================================ */

/* ----------- Helpers (shared with dossier.jsx) ----------- */
function SectionRow({ children }) {
  return <div className="section-row">{children}</div>;
}

function KV({ k, v, muted }) {
  return (
    <div className="kv">
      <div className="k">{k}</div>
      <div className={`v ${muted ? "muted" : ""}`}>{v ?? "—"}</div>
    </div>
  );
}

/* ============================================================
   STAGE 1 — Dossier (intake)
   ============================================================ */
function StageDossier({ d, ext }) {
  return (
    <>
      <section className="panel">
        <div className="panel-head">
          <div>
            <div className="eyebrow">Étape 1 — Dossier</div>
            <h2>Identification de la propriété</h2>
          </div>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <div className="kv-grid kv-grid-2">
          <KV k="Numéro de dossier" v={d.id}/>
          <KV k="Date de création" v="12 mai 2026"/>
          <KV k="Adresse" v={`${d.addr}, ${d.city}`}/>
          <KV k="Arrondissement" v={d.city}/>
          <KV k="Cadastre du Québec" v={ext.cadastral}/>
          <KV k="Rôle d'évaluation" v={formatMoney(ext.municipalRoll)}/>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Caractéristiques</h2>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <div className="kv-grid kv-grid-3">
          <KV k="Type" v={d.type}/>
          <KV k="Année de construction" v={d.year}/>
          <KV k="Rénovation majeure" v={ext.yearReno}/>
          <KV k="Superficie habitable" v={`${formatNum(d.area)} pi²`}/>
          <KV k="Superficie du lot" v={`${formatNum(ext.lotArea)} pi²`}/>
          <KV k="Étages" v={ext.stories}/>
          <KV k="Chambres" v={ext.bedrooms}/>
          <KV k="Salles de bain" v={ext.bathrooms}/>
          <KV k="Stationnement" v={ext.parking}/>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Mandat</h2>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <div className="kv-grid kv-grid-2">
          <KV k="Type de mandat" v={d.mandate}/>
          <KV k="Date de mandat" v="12 mai 2026"/>
          <KV k="Date de valeur" v="15 mai 2026"/>
          <KV k="Échéance" v="2 juin 2026"/>
          <KV k="Client" v={ext.contact.org}/>
          <KV k="Représentant" v={`${ext.contact.person} — ${ext.contact.role}`}/>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Visite</h2>
          <button className="btn secondary"><Icon.Plus/> Planifier une visite</button>
        </div>
        <div className="visit-row">
          <div className="visit-status visit-done">
            <Icon.Check/>
            <div>
              <div className="visit-title">Visite intérieure & extérieure</div>
              <div className="visit-meta">17 mai 2026 · 10h00 · Maxime Tremblay</div>
            </div>
          </div>
          <div className="visit-stats">
            <div><b>42</b> photos</div>
            <div><b>14</b> pièces relevées</div>
            <div><b>3</b> mesures du lot</div>
          </div>
        </div>
      </section>
    </>
  );
}

/* ============================================================
   STAGE 2 — Marché (already exists, kept here for routing)
   We re-export by rendering the existing market view from dossier.jsx.
   ============================================================ */
function StageMarche({ d, ext }) {
  const comps = ext.comps || [];
  const pricesPerSqft = comps.map(c => c.price / c.area);
  const median = pricesPerSqft.length
    ? pricesPerSqft.slice().sort((a, b) => a - b)[Math.floor(pricesPerSqft.length / 2)]
    : 0;
  const min = Math.min(...pricesPerSqft);
  const max = Math.max(...pricesPerSqft);
  const indicatedLow  = Math.round((median * d.area * 0.985) / 1000) * 1000;
  const indicatedHigh = Math.round((median * d.area * 1.012) / 1000) * 1000;

  return (
    <>
      <section className="panel">
        <div className="panel-head">
          <div>
            <div className="eyebrow">Étape 2 — Marché</div>
            <h2>Analyse comparative</h2>
          </div>
          <div className="panel-actions">
            <button className="btn secondary"><Icon.Plus/> Ajouter un comparable</button>
          </div>
        </div>

        <div className="comp-table">
          <div className="comp-head">
            <div>Comparable</div>
            <div>Vendu</div>
            <div className="num">Superficie</div>
            <div className="num">Prix</div>
            <div className="num">$/pi²</div>
            <div className="num">Ajust.</div>
            <div className="num">Distance</div>
          </div>
          {comps.map((c, i) => {
            const ppsf = c.price / c.area;
            return (
              <div className="comp-row" key={i}>
                <div className="c-addr">
                  <div className="line1">{c.addr}</div>
                  <div className="line2">{c.note}</div>
                </div>
                <div className="c-when">{c.soldLabel}</div>
                <div className="num">{formatNum(c.area)} pi²</div>
                <div className="num strong">{formatMoney(c.price)}</div>
                <div className="num">{Math.round(ppsf)} $</div>
                <div className={`num adj ${c.adj > 0 ? "pos" : c.adj < 0 ? "neg" : ""}`}>
                  {c.adj > 0 ? "+" : ""}{c.adj.toFixed(1)}%
                </div>
                <div className="num muted">{c.distance.toFixed(1)} km</div>
              </div>
            );
          })}
        </div>

        <div className="recon">
          <div className="recon-row">
            <div className="recon-k">Médiane $/pi²</div>
            <div className="recon-v numeric">{Math.round(median)} $</div>
          </div>
          <div className="recon-row">
            <div className="recon-k">Étendue</div>
            <div className="recon-v numeric">{Math.round(min)}–{Math.round(max)} $</div>
          </div>
          <div className="recon-row recon-final">
            <div className="recon-k">Valeur indiquée</div>
            <div className="recon-v numeric strong">
              {formatMoney(indicatedLow)} <span className="dash">–</span> {formatMoney(indicatedHigh)}
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Notes</h2>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <p className="notes-body">{ext.notes}</p>
      </section>
    </>
  );
}

/* ============================================================
   STAGE 3 — Analyse (three approaches)
   ============================================================ */
function StageAnalyse({ d, ext }) {
  const comps = ext.comps || [];
  const ppsf = comps.map(c => c.price / c.area);
  const median = ppsf.slice().sort((a, b) => a - b)[Math.floor(ppsf.length / 2)] || 0;
  const compsValue = Math.round((median * d.area) / 1000) * 1000;

  // Synthetic cost approach
  const replacement = 285 * d.area;
  const depreciation = Math.round(replacement * 0.18);
  const landValue = 720000;
  const costValue = Math.round((replacement - depreciation + landValue) / 1000) * 1000;

  const approaches = [
    {
      key: "comp",
      title: "Comparaison",
      sub: "Ventes récentes ajustées",
      value: compsValue,
      weight: 70,
      notes: `${comps.length} ventes retenues — Outremont · 0,4–1,1 km`,
      applies: true
    },
    {
      key: "cost",
      title: "Coût",
      sub: "Reconstitution − dépréciation + terrain",
      value: costValue,
      weight: 30,
      notes: "Coût neuf 285 $/pi² · dépréciation effective 18 %",
      applies: true
    },
    {
      key: "income",
      title: "Revenus",
      sub: "Capitalisation des revenus nets",
      value: null,
      weight: 0,
      notes: "Non applicable — propriété occupée par le propriétaire",
      applies: false
    }
  ];

  // Weighted final
  const weightedSum = approaches
    .filter(a => a.applies)
    .reduce((s, a) => s + a.value * a.weight / 100, 0);
  const finalValue = Math.round(weightedSum / 1000) * 1000;

  return (
    <>
      <section className="panel">
        <div className="panel-head">
          <div>
            <div className="eyebrow">Étape 3 — Analyse</div>
            <h2>Réconciliation des approches</h2>
          </div>
        </div>

        <div className="approach-grid">
          {approaches.map(a => (
            <div key={a.key} className={`approach ${a.applies ? "" : "na"}`}>
              <div className="approach-head">
                <div>
                  <div className="approach-title">{a.title}</div>
                  <div className="approach-sub">{a.sub}</div>
                </div>
                {a.applies && (
                  <div className="approach-weight">
                    <span className="numeric">{a.weight}</span>%
                  </div>
                )}
              </div>
              <div className="approach-value numeric">
                {a.applies ? formatMoney(a.value) : "—"}
              </div>
              <div className="approach-notes">{a.notes}</div>
            </div>
          ))}
        </div>

        <div className="recon recon-weighted">
          <div className="recon-row recon-final">
            <div className="recon-k">
              Valeur réconciliée
              <span className="recon-sub">moyenne pondérée des approches retenues</span>
            </div>
            <div className="recon-v numeric strong huge">{formatMoney(finalValue)}</div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Justification</h2>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <p className="notes-body">
          La pondération favorise l'approche comparative (70 %) compte tenu de
          l'abondance de ventes récentes de propriétés similaires dans Outremont.
          L'approche coût (30 %) sert de validation et confirme l'ordre de
          grandeur. L'approche revenus n'est pas applicable à une résidence
          principale occupée par son propriétaire.
        </p>
      </section>
    </>
  );
}

/* ============================================================
   STAGE 4 — Synthèse (final value & sign-off)
   ============================================================ */
function StageSynthese({ d, ext }) {
  const finalValue = 1380000;
  const low = 1360000;
  const high = 1395000;

  return (
    <>
      <section className="panel synthese-hero">
        <div className="eyebrow">Étape 4 — Synthèse</div>
        <div className="syn-label">Valeur marchande estimée</div>
        <div className="syn-value numeric">{formatMoney(finalValue)}</div>
        <div className="syn-range numeric">
          fourchette {formatMoney(low)} <span className="dash">—</span> {formatMoney(high)}
        </div>
        <div className="syn-meta">
          <div><span className="k">Date de valeur</span><span className="v">15 mai 2026</span></div>
          <div><span className="k">Méthode dominante</span><span className="v">Comparaison directe</span></div>
          <div><span className="k">Niveau de confiance</span><span className="v conf">Élevé</span></div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Narratif de synthèse</h2>
          <button className="btn ghost"><Icon.Edit/> Modifier</button>
        </div>
        <p className="notes-body">
          La propriété située au {d.addr}, dans l'arrondissement d'Outremont,
          est une maison unifamiliale de prestige de {d.year} sur un lot d'angle
          de {formatNum(ext.lotArea)} pi². Les caractéristiques architecturales
          d'origine ont été préservées, et plusieurs composantes (toiture, fenestration)
          ont été modernisées en 2019. Le marché d'Outremont demeure soutenu, avec une
          médiane de {Math.round(comps_median(ext))} $/pi² pour les ventes des douze
          derniers mois. La valeur réconciliée reflète une pondération favorisant
          l'approche comparative, validée par l'approche coût.
        </p>
      </section>

      <section className="panel signoff">
        <div className="panel-head">
          <h2>Attestation</h2>
          <div className="status-pill">
            <Icon.Clock/> En attente de signature
          </div>
        </div>
        <div className="signoff-body">
          <div className="signoff-text">
            Je certifie que la présente évaluation a été préparée conformément aux
            normes de l'Ordre des évaluateurs agréés du Québec (OEAQ) et qu'elle
            reflète mon opinion professionnelle indépendante de la valeur marchande
            de l'immeuble à la date de valeur indiquée.
          </div>
          <div className="signoff-sig">
            <div className="sig-line"/>
            <div className="sig-name">Maxime Tremblay, É.A.</div>
            <div className="sig-cred">OEAQ 4218 · Évaluateur agréé</div>
          </div>
        </div>
        <div className="signoff-actions">
          <button className="btn secondary">Demander une révision interne</button>
          <button className="btn accent"><Icon.Check/> Signer & finaliser</button>
        </div>
      </section>
    </>
  );
}

function comps_median(ext) {
  const ps = (ext.comps || []).map(c => c.price / c.area);
  return ps.slice().sort((a,b) => a-b)[Math.floor(ps.length/2)] || 0;
}

/* ============================================================
   STAGE 5 — Rapport (preview & export)
   ============================================================ */
function StageRapport({ d, ext }) {
  const sections = [
    { name: "Page titre & identification", done: true, pages: 1 },
    { name: "Sommaire exécutif",            done: true, pages: 2 },
    { name: "Description de la propriété",  done: true, pages: 4 },
    { name: "Contexte de marché",           done: true, pages: 3 },
    { name: "Analyse des approches",        done: true, pages: 6 },
    { name: "Réconciliation & synthèse",    done: true, pages: 2 },
    { name: "Attestation & certificat",     done: false, pages: 1 },
    { name: "Annexes (photos, plans, comparables)", done: true, pages: 14 }
  ];
  const totalPages = sections.reduce((s, x) => s + x.pages, 0);
  const completed = sections.filter(x => x.done).length;

  return (
    <>
      <section className="panel rapport-hero">
        <div className="rapport-cover">
          <div className="cover-eyebrow">Rapport d'évaluation</div>
          <div className="cover-addr">{d.addr}</div>
          <div className="cover-city">{d.city}, Montréal</div>
          <div className="cover-bottom">
            <div>
              <div className="cover-meta-k">Préparé pour</div>
              <div className="cover-meta-v">{ext.contact.org}</div>
            </div>
            <div>
              <div className="cover-meta-k">Date de valeur</div>
              <div className="cover-meta-v numeric">15 mai 2026</div>
            </div>
            <div>
              <div className="cover-meta-k">Dossier</div>
              <div className="cover-meta-v numeric">{d.id}</div>
            </div>
          </div>
          <div className="cover-seal">É.A.</div>
        </div>
        <div className="rapport-side">
          <div className="rs-stat">
            <div className="rs-num numeric">{totalPages}</div>
            <div className="rs-lbl">pages</div>
          </div>
          <div className="rs-stat">
            <div className="rs-num numeric">{completed}/{sections.length}</div>
            <div className="rs-lbl">sections complètes</div>
          </div>
          <div className="rs-actions">
            <button className="btn accent btn-full">Télécharger PDF complet</button>
            <button className="btn secondary btn-full">Aperçu</button>
            <button className="btn ghost btn-full">PDF signé électroniquement</button>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Sections du rapport</h2>
          <button className="btn ghost">Réorganiser</button>
        </div>
        <ul className="rapport-sections">
          {sections.map((s, i) => (
            <li key={i} className={s.done ? "done" : "pending"}>
              <span className="sec-icon">
                {s.done ? <Icon.Check/> : <Icon.Clock/>}
              </span>
              <span className="sec-num numeric">{String(i+1).padStart(2,"0")}</span>
              <span className="sec-name">{s.name}</span>
              <span className="sec-pages numeric">{s.pages} p.</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

Object.assign(window, {
  StageDossier, StageMarche, StageAnalyse, StageSynthese, StageRapport, KV
});
