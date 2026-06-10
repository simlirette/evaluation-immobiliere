/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

const SECTIONS = [
  { id: "survol",       label: "Survol" },
  { id: "creer",        label: "Créer un dossier" },
  { id: "etapes",       label: "Les 5 étapes" },
  { id: "agent",        label: "L'agent IA" },
  { id: "bibliotheque", label: "Bibliothèque & Modèles" },
  { id: "oeaq",         label: "Conformité OEAQ" },
  { id: "raccourcis",   label: "Raccourcis clavier" },
  { id: "faq",          label: "Questions fréquentes" },
  { id: "contact",      label: "Nous joindre" }
];

function AidePage() {
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  const [query, setQuery] = useState("");

  // Scroll to section on click; track which is in view to highlight nav.
  const [active, setActive] = useState("survol");
  const containerRef = useRef(null);

  useEffect(() => {
    const els = SECTIONS.map(s => document.getElementById(s.id)).filter(Boolean);
    function onScroll() {
      const y = window.scrollY + 160;
      let cur = SECTIONS[0].id;
      for (const el of els) {
        if (el.offsetTop <= y) cur = el.id;
      }
      setActive(cur);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function jump(id) {
    const el = document.getElementById(id);
    if (el) window.scrollTo({ top: el.offsetTop - 32, behavior: "smooth" });
  }

  // Filter sections when searching
  const filteredSections = useMemo(() => {
    if (!query.trim()) return SECTIONS;
    const q = query.trim().toLowerCase();
    return SECTIONS.filter(s => s.label.toLowerCase().includes(q));
  }, [query]);

  return (
    <div className="app" data-screen-label="08 Aide">
      <Sidebar active="" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">
        <div className="topbar aide-topbar">
          <div className="pagehead aide-head">
            <div>
              <h1>Comment Éval Immo fonctionne</h1>
              <div className="subtitle">
                Du premier mandat à la signature finale — un guide rapide du flux de travail,
                des outils et de l'agent qui vous accompagne.
              </div>
            </div>
            <div className="aide-search">
              <Icon.Glass/>
              <input
                type="text"
                placeholder="Rechercher dans l'aide…"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="aide-body" ref={containerRef}>
          <aside className="aide-nav">
            <div className="an-label">Sommaire</div>
            {filteredSections.map(s => (
              <button
                key={s.id}
                className={`an-item ${active === s.id ? "active" : ""}`}
                onClick={() => jump(s.id)}>
                {s.label}
              </button>
            ))}
            <div className="an-divider"/>
            <a className="an-item an-link" href="parametres.html">Paramètres du compte →</a>
            <a className="an-item an-link" href="mailto:support@evalimmo.ca">Écrire au soutien →</a>
          </aside>

          <main className="aide-main">
            <Survol/>
            <Creer/>
            <Etapes/>
            <Agent/>
            <Bibli/>
            <OEAQ/>
            <Raccourcis/>
            <FAQ/>
            <Contact/>
          </main>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   SURVOL — workflow at a glance
   ============================================================ */
function Survol() {
  const flow = [
    { n: 1, label: "Dossier",   desc: "Identification de la propriété, mandat, client." },
    { n: 2, label: "Marché",    desc: "Comparables sélectionnés et ajustés." },
    { n: 3, label: "Analyse",   desc: "Réconciliation des trois approches." },
    { n: 4, label: "Synthèse",  desc: "Valeur marchande et attestation." },
    { n: 5, label: "Rapport",   desc: "Rapport final, signature, livraison." }
  ];
  return (
    <section id="survol" className="ah-section">
      <div className="ah-eyebrow">Survol</div>
      <h2 className="ah-title">Un mandat, cinq étapes, un rapport.</h2>
      <p className="ah-lead">
        Éval Immo accompagne chaque évaluation depuis l'ouverture du dossier jusqu'à
        la livraison du rapport signé. Chaque étape est sauvegardée, partagée avec
        votre équipe et conservée selon les normes de l'OEAQ et la Loi 25.
      </p>

      <div className="flow">
        {flow.map((s, i) => (
          <React.Fragment key={s.n}>
            <div className="flow-step">
              <div className="fs-n numeric">{String(s.n).padStart(2,"0")}</div>
              <div className="fs-label">{s.label}</div>
              <div className="fs-desc">{s.desc}</div>
            </div>
            {i < flow.length - 1 && <div className="flow-arrow">›</div>}
          </React.Fragment>
        ))}
      </div>

      <div className="ah-pillars">
        <Pillar title="Une seule source de vérité"
                desc="Le rôle municipal, les comparables, les comptes-rendus de visite et le rapport vivent dans le même dossier."/>
        <Pillar title="L'agent comme copilote"
                desc="Suggestions de comparables, rédaction assistée, vérifications de cohérence — toujours en retrait, jamais signataire."/>
        <Pillar title="Conforme par défaut"
                desc="Normes OEAQ, attestation type, archivage 7 ans, journal d'audit. Activés dès le premier dossier."/>
      </div>
    </section>
  );
}

function Pillar({ title, desc }) {
  return (
    <div className="pillar">
      <h4>{title}</h4>
      <p>{desc}</p>
    </div>
  );
}

/* ============================================================
   CRÉER UN DOSSIER
   ============================================================ */
function Creer() {
  return (
    <section id="creer" className="ah-section">
      <div className="ah-eyebrow">Créer un dossier</div>
      <h2 className="ah-title">Quatre étapes, deux minutes.</h2>
      <ol className="ah-steps">
        <li>
          <b>Point de départ.</b> Choisissez la méthode :
          recherche du registre municipal, saisie manuelle, importation d'un PDF
          (mandat, rôle, fiche MLS), ou démarrage à partir d'un modèle.
        </li>
        <li>
          <b>Propriété.</b> Identifiez l'immeuble par son adresse ou son cadastre.
          Les caractéristiques du rôle se préchargent automatiquement —
          superficie, année, lot, rôle municipal.
        </li>
        <li>
          <b>Mandat.</b> Type de mandat, client, représentant, date de valeur,
          échéance. Le modèle de rapport est suggéré selon le mandat.
        </li>
        <li>
          <b>Confirmation.</b> Vérifiez les données et créez le dossier.
          Il ouvre directement à l'étape <i>Marché</i> avec les premières
          suggestions de comparables.
        </li>
      </ol>
      <a className="ah-cta" href="nouveau-dossier.html">Démarrer un dossier →</a>
    </section>
  );
}

/* ============================================================
   LES 5 ÉTAPES
   ============================================================ */
function Etapes() {
  const stages = [
    { n: 1, name: "Dossier",   what: "Identifier la propriété et le mandat.",
      details: "Adresse, cadastre, caractéristiques tirées du rôle, mandat, client, représentant, visite. C'est la base de tout ce qui suit." },
    { n: 2, name: "Marché",    what: "Sélectionner et ajuster les comparables.",
      details: "L'agent suggère des ventes pertinentes. Vous validez, ajoutez, retirez. Les ajustements (superficie, état, distance) sont visibles en permanence." },
    { n: 3, name: "Analyse",   what: "Pondérer les trois approches.",
      details: "Coût, comparaison et revenus, chacune avec une valeur indiquée et une pondération justifiée. Un texte de justification accompagne le choix." },
    { n: 4, name: "Synthèse",  what: "Arrêter la valeur et préparer l'attestation.",
      details: "Valeur marchande, fourchette, niveau de confiance, narratif final. L'attestation OEAQ est prête à être signée." },
    { n: 5, name: "Rapport",   what: "Générer, signer, livrer.",
      details: "Le rapport est assemblé à partir du modèle et des données du dossier. Signature électronique, export PDF, journal d'envoi." }
  ];
  return (
    <section id="etapes" className="ah-section">
      <div className="ah-eyebrow">Les 5 étapes</div>
      <h2 className="ah-title">Un même rythme pour chaque dossier.</h2>
      <p className="ah-lead">
        Chaque étape produit des artefacts qui alimentent la suivante — vous ne
        ressaisissez jamais une donnée déjà connue. Vous pouvez revenir en arrière
        à tout moment ; l'historique conserve les versions.
      </p>
      <div className="stage-cards">
        {stages.map(s => (
          <article className="stage-card" key={s.n}>
            <div className="sc-head">
              <span className="sc-n numeric">{String(s.n).padStart(2,"0")}</span>
              <h3>{s.name}</h3>
            </div>
            <div className="sc-what">{s.what}</div>
            <p className="sc-details">{s.details}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

/* ============================================================
   AGENT
   ============================================================ */
function Agent() {
  return (
    <section id="agent" className="ah-section">
      <div className="ah-eyebrow">L'agent IA</div>
      <h2 className="ah-title">Un copilote, pas un signataire.</h2>
      <p className="ah-lead">
        L'agent travaille à vos côtés à chaque étape. Il vous propose, vous résume,
        vous interroge — il ne décide jamais. La signature et le jugement
        professionnel restent les vôtres, conformément aux exigences de l'OEAQ.
      </p>

      <div className="agent-grid">
        <AgentCard title="Ce qu'il fait"     items={[
          "Suggère des comparables et leurs ajustements",
          "Détecte les écarts entre approches",
          "Rédige des brouillons de notes et de narratif",
          "Vérifie la cohérence des données du dossier",
          "Résume un dossier ou une visite en quelques lignes"
        ]}/>
        <AgentCard title="Ce qu'il ne fait pas" items={[
          "Signer un rapport ou une attestation",
          "Modifier la valeur marchande sans validation",
          "Communiquer directement avec un client",
          "Conserver des données hors du cabinet"
        ]} muted/>
      </div>

      <div className="agent-prompt">
        <div className="ap-sparkle"><Icon.Sparkle/></div>
        <div>
          <b>Comment l'invoquer.</b>
          <span>
            Le champ « Demander à l'agent » au bas de chaque dossier est toujours
            disponible. Des suggestions contextuelles apparaissent selon l'étape :
            « Élargir le rayon », « Rédiger le narratif », « Vérifier l'attestation ».
          </span>
        </div>
      </div>
    </section>
  );
}

function AgentCard({ title, items, muted }) {
  return (
    <div className={`agent-card ${muted ? "muted" : ""}`}>
      <h4>{title}</h4>
      <ul>{items.map((s, i) => <li key={i}>{s}</li>)}</ul>
    </div>
  );
}

/* ============================================================
   BIBLIOTHÈQUE & MODÈLES
   ============================================================ */
function Bibli() {
  return (
    <section id="bibliotheque" className="ah-section">
      <div className="ah-eyebrow">Bibliothèque & Modèles</div>
      <h2 className="ah-title">Tout votre référentiel, au même endroit.</h2>
      <p className="ah-lead">
        La Bibliothèque réunit les données qui alimentent vos analyses : ventes
        comparables, indicateurs de marché, coûts de construction, taux de
        capitalisation. Elle est mise à jour automatiquement via JLR, Centris et
        le rôle municipal.
      </p>
      <div className="biblio-aide">
        <BibliCard k="Ventes"   v="Base de comparables triable et filtrable. Chaque vente affiche son utilisation passée dans vos dossiers."/>
        <BibliCard k="Marchés"  v="Indicateurs par quartier — médiane $/pi², étendue, DOM, tendance trimestrielle."/>
        <BibliCard k="Coûts"    v="Tableaux Marshall & Swift et APCHQ pour l'approche par le coût."/>
        <BibliCard k="Taux"     v="Taux de capitalisation observés par segment et secteur."/>
      </div>
      <h3 className="ah-sub">Modèles de rapport</h3>
      <p>
        Six modèles couvrent les mandats les plus fréquents : hypothécaire, pré-vente,
        successoral, litige, acquisition d'immeuble à revenus et avis de valeur restreint.
        Chaque modèle est conforme aux normes OEAQ — vous pouvez les personnaliser au
        nom de votre cabinet, mais la structure réglementaire est verrouillée.
      </p>
    </section>
  );
}

function BibliCard({ k, v }) {
  return (
    <div className="biblio-aide-card">
      <div className="bac-k">{k}</div>
      <div className="bac-v">{v}</div>
    </div>
  );
}

/* ============================================================
   OEAQ
   ============================================================ */
function OEAQ() {
  return (
    <section id="oeaq" className="ah-section">
      <div className="ah-eyebrow">Conformité OEAQ & Loi 25</div>
      <h2 className="ah-title">Conforme par défaut.</h2>
      <p className="ah-lead">
        Éval Immo a été conçu avec et pour les évaluateurs agréés du Québec.
        Toutes les contraintes professionnelles sont intégrées au flux de travail.
      </p>
      <ul className="checklist">
        <li><Icon.Check/> Attestation OEAQ générée et liée à votre numéro de permis</li>
        <li><Icon.Check/> Synchronisation mensuelle de votre adhésion via le registre OEAQ</li>
        <li><Icon.Check/> Archivage des dossiers et des rapports pendant 7 ans</li>
        <li><Icon.Check/> Journal d'audit horodaté pour chaque modification</li>
        <li><Icon.Check/> Signature finale réservée aux É.A. en règle</li>
        <li><Icon.Check/> Hébergement des données au Québec, conforme à la Loi 25</li>
      </ul>
    </section>
  );
}

/* ============================================================
   RACCOURCIS
   ============================================================ */
function Raccourcis() {
  const groups = [
    { name: "Général", items: [
      { k: ["⌘", "K"],       desc: "Recherche universelle" },
      { k: ["⌘", "/"],       desc: "Ouvrir / fermer l'agent" },
      { k: ["G", "D"],       desc: "Aller à Dossiers" },
      { k: ["G", "B"],       desc: "Aller à Bibliothèque" }
    ]},
    { name: "Dans un dossier", items: [
      { k: ["1"],            desc: "Étape Dossier" },
      { k: ["2"],            desc: "Étape Marché" },
      { k: ["3"],            desc: "Étape Analyse" },
      { k: ["4"],            desc: "Étape Synthèse" },
      { k: ["5"],            desc: "Étape Rapport" },
      { k: ["E"],            desc: "Modifier la section active" },
      { k: ["⌘", "S"],       desc: "Sauvegarder" }
    ]}
  ];
  return (
    <section id="raccourcis" className="ah-section">
      <div className="ah-eyebrow">Raccourcis clavier</div>
      <h2 className="ah-title">Plus vite, sans la souris.</h2>
      <div className="kbd-groups">
        {groups.map(g => (
          <div className="kbd-group" key={g.name}>
            <h4>{g.name}</h4>
            <ul>
              {g.items.map((it, i) => (
                <li key={i}>
                  <span className="kbd-keys">
                    {it.k.map((k, j) => (
                      <React.Fragment key={j}>
                        <kbd>{k}</kbd>
                        {j < it.k.length - 1 && <span className="kbd-plus">+</span>}
                      </React.Fragment>
                    ))}
                  </span>
                  <span className="kbd-desc">{it.desc}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ============================================================
   FAQ
   ============================================================ */
function FAQ() {
  const qs = [
    { q: "Qui peut signer un rapport ?",
      a: "Uniquement les membres du cabinet qui sont évaluateurs agréés en règle auprès de l'OEAQ. Les stagiaires et les adjoint·e·s peuvent collaborer mais pas signer. Le statut est vérifié automatiquement via le registre OEAQ." },
    { q: "Comment l'agent choisit-il les comparables ?",
      a: "Par proximité géographique, similarité de type, d'âge, de superficie et de date de vente. Il propose, vous validez. Les ajustements (état, lot, $/pi²) sont visibles et modifiables." },
    { q: "Mes données sont-elles hébergées au Québec ?",
      a: "Oui. Les serveurs sont situés au Québec et les sauvegardes restent au Canada, conformément à la Loi 25 sur la protection des renseignements personnels." },
    { q: "Combien de temps les dossiers sont-ils conservés ?",
      a: "Sept ans à compter de la signature du rapport, conformément aux normes de l'OEAQ. Vous pouvez exporter les dossiers à tout moment au format PDF + données structurées (JSON, CSV)." },
    { q: "Puis-je modifier un rapport déjà signé ?",
      a: "Non — un rapport signé est verrouillé. Vous pouvez créer une version corrigée (« errata » ou « rapport révisé ») qui référence l'original. L'historique est conservé." },
    { q: "Comment ajouter un membre à mon cabinet ?",
      a: "Dans Paramètres → Membres → Inviter. La personne reçoit un courriel d'activation ; vous définissez ses permissions par défaut. La facturation s'ajuste automatiquement." }
  ];
  return (
    <section id="faq" className="ah-section">
      <div className="ah-eyebrow">Questions fréquentes</div>
      <h2 className="ah-title">Les réponses qui reviennent.</h2>
      <div className="faq-list">
        {qs.map((q, i) => <FAQItem key={i} q={q.q} a={q.a}/>)}
      </div>
    </section>
  );
}

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? "open" : ""}`}>
      <button className="fi-q" onClick={() => setOpen(o => !o)}>
        <span>{q}</span>
        <span className="fi-caret">
          <svg viewBox="0 0 10 6" width="10" height="6"><path d="M0 1l5 4 5-4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </span>
      </button>
      {open && <div className="fi-a">{a}</div>}
    </div>
  );
}

/* ============================================================
   CONTACT
   ============================================================ */
function Contact() {
  return (
    <section id="contact" className="ah-section">
      <div className="ah-eyebrow">Nous joindre</div>
      <h2 className="ah-title">Une question, un commentaire ?</h2>
      <div className="contact-grid">
        <div className="contact-card">
          <h4>Soutien technique</h4>
          <p>Du lundi au vendredi, 8 h à 18 h (HE). Réponse sous deux heures ouvrables.</p>
          <div className="cc-link"><a>support@evalimmo.ca</a></div>
          <div className="cc-link"><a>1 855 555-3814</a></div>
        </div>
        <div className="contact-card">
          <h4>Questions professionnelles</h4>
          <p>Une consultation entre É.A. — méthodologie, interprétation de norme, ajustements complexes.</p>
          <div className="cc-link"><a>methodologie@evalimmo.ca</a></div>
        </div>
        <div className="contact-card">
          <h4>Idées & retours</h4>
          <p>Vos suggestions nourrissent les prochaines mises à jour. Nous lisons tout.</p>
          <div className="cc-link"><a>idees@evalimmo.ca</a></div>
        </div>
      </div>
    </section>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<AidePage/>);
