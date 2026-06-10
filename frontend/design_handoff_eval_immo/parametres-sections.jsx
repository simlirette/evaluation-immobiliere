/* eslint-disable */
/* ============================================================
   Éval Immo — Paramètres : section views
   ============================================================ */

/* Helpers — local to this file */
function P_Card({ title, desc, action, children, tight }) {
  return (
    <section className={`param-card ${tight ? "tight" : ""}`}>
      <div className="pc-head">
        <div>
          <h3>{title}</h3>
          {desc && <div className="pc-desc">{desc}</div>}
        </div>
        {action}
      </div>
      <div className="pc-body">{children}</div>
    </section>
  );
}

function P_Row({ k, v, muted }) {
  return (
    <div className="pc-row">
      <div className="pc-k">{k}</div>
      <div className={`pc-v ${muted ? "muted" : ""}`}>{v}</div>
    </div>
  );
}

function P_Toggle({ on, onChange, label, desc }) {
  return (
    <label className="pc-toggle">
      <div className="ptg-text">
        <div className="ptg-label">{label}</div>
        {desc && <div className="ptg-desc">{desc}</div>}
      </div>
      <span className={`switch ${on ? "on" : ""}`} onClick={() => onChange(!on)}>
        <span className="switch-knob"/>
      </span>
    </label>
  );
}

/* ============================================================
   PROFIL
   ============================================================ */
function SectionProfil() {
  return (
    <>
      <div className="param-hero">
        <div className="ph-avatar">MT</div>
        <div className="ph-info">
          <h2>Maxime Tremblay</h2>
          <div className="ph-meta">
            <span className="ph-pill"><Icon.Seal/> É.A. — OEAQ 4218</span>
            <span className="dot-sep">·</span>
            <span>Tremblay Évaluations</span>
            <span className="dot-sep">·</span>
            <span>Évaluateur agréé depuis 2009</span>
          </div>
        </div>
        <button className="btn secondary">Modifier la photo</button>
      </div>

      <P_Card title="Identité" action={<button className="btn ghost">Modifier</button>}>
        <P_Row k="Prénom"  v="Maxime"/>
        <P_Row k="Nom"     v="Tremblay"/>
        <P_Row k="Titre"   v="Évaluateur agréé, associé"/>
        <P_Row k="Langues" v="Français · Anglais"/>
      </P_Card>

      <P_Card title="Coordonnées" action={<button className="btn ghost">Modifier</button>}>
        <P_Row k="Courriel" v="maxime@tremblay-eval.ca"/>
        <P_Row k="Téléphone" v="514 555-7421"/>
        <P_Row k="Cellulaire" v="514 555-3089"/>
      </P_Card>

      <P_Card
        title="Adhésion professionnelle"
        desc="Vérifiée auprès du registre de l'OEAQ. Synchronisée chaque mois."
        action={<span className="pc-status ok"><Icon.Check/> En règle</span>}>
        <P_Row k="N° de membre OEAQ" v={<span className="numeric">4218</span>}/>
        <P_Row k="Permis d'exercice"  v={<span className="numeric">2009-A-4218</span>}/>
        <P_Row k="Renouvellement"     v="31 mars 2027"/>
        <P_Row k="Champs de pratique" v="Résidentiel · Multilogements · Commercial léger"/>
      </P_Card>

      <P_Card
        title="Signature manuscrite"
        desc="Apparaît sur tous les rapports finaux et les certificats d'évaluation."
        action={<button className="btn ghost">Refaire</button>}>
        <div className="signature-preview">
          <svg viewBox="0 0 320 80" preserveAspectRatio="none">
            <path d="M10,55 C30,20 60,75 90,40 S140,15 170,50 S230,75 270,30 C290,10 310,40 315,60"
              stroke="var(--ink)" strokeWidth="1.8" fill="none" strokeLinecap="round"/>
          </svg>
          <div className="sig-meta">
            <div>Maxime Tremblay, É.A.</div>
            <div>OEAQ 4218 — signature numérisée le 12 janvier 2024</div>
          </div>
        </div>
      </P_Card>
    </>
  );
}

/* ============================================================
   CABINET
   ============================================================ */
function SectionCabinet() {
  return (
    <>
      <P_Card title="Identification" action={<button className="btn ghost">Modifier</button>}>
        <P_Row k="Raison sociale" v="Tremblay Évaluations inc."/>
        <P_Row k="NEQ"            v={<span className="numeric">1170 392 488</span>}/>
        <P_Row k="N° d'entreprise" v={<span className="numeric">789 234 561 RC0001</span>}/>
        <P_Row k="Forme juridique" v="Société par actions"/>
      </P_Card>

      <P_Card title="Adresse du cabinet" action={<button className="btn ghost">Modifier</button>}>
        <P_Row k="Adresse" v="2120, rue Stanley, bureau 800"/>
        <P_Row k="Ville"   v="Montréal (Québec) H3A 1R8"/>
        <P_Row k="Téléphone" v="514 555-1840"/>
        <P_Row k="Courriel"  v="info@tremblay-eval.ca"/>
        <P_Row k="Site web"  v="tremblay-eval.ca"/>
      </P_Card>

      <P_Card
        title="Logo & papier en-tête"
        desc="Le logo apparaît sur la page titre et l'en-tête de chaque rapport."
        action={<button className="btn secondary">Téléverser</button>}>
        <div className="logo-preview">
          <div className="lp-logo">
            <span className="lp-mark">T·É</span>
          </div>
          <div className="lp-info">
            <div className="lp-name">Tremblay Évaluations</div>
            <div className="lp-sub">SVG · 4,2 Ko · téléversé le 8 janv. 2025</div>
          </div>
        </div>
      </P_Card>

      <P_Card title="Couleurs de marque" desc="Utilisées sur la page titre des rapports.">
        <div className="brand-swatches">
          <div className="swatch">
            <span className="sw-color" style={{background:"#1c3559"}}/>
            <span className="sw-name">Primaire</span>
            <span className="sw-hex numeric">#1C3559</span>
          </div>
          <div className="swatch">
            <span className="sw-color" style={{background:"#b88a3e"}}/>
            <span className="sw-name">Accent</span>
            <span className="sw-hex numeric">#B88A3E</span>
          </div>
          <div className="swatch">
            <span className="sw-color" style={{background:"#1f1e1c"}}/>
            <span className="sw-name">Texte</span>
            <span className="sw-hex numeric">#1F1E1C</span>
          </div>
        </div>
      </P_Card>
    </>
  );
}

/* ============================================================
   MEMBRES
   ============================================================ */
const MEMBERS = [
  { name: "Maxime Tremblay",  role: "É.A. — Associé principal", oeaq: "4218", email: "maxime@tremblay-eval.ca",  status: "active", since: "2009" },
  { name: "Émilie Lapointe",  role: "É.A. — Associée",          oeaq: "5891", email: "emilie@tremblay-eval.ca",  status: "active", since: "2016" },
  { name: "Jean-François Côté", role: "É.A. stagiaire",         oeaq: "—",    email: "jf@tremblay-eval.ca",      status: "active", since: "2024" },
  { name: "Sophie Bélanger",  role: "Adjointe administrative",  oeaq: "—",    email: "sophie@tremblay-eval.ca",  status: "active", since: "2018" },
  { name: "Camille Pelletier", role: "Recherchiste — temps partiel", oeaq: "—", email: "camille@tremblay-eval.ca", status: "invited", since: "—" }
];

function SectionMembres() {
  return (
    <>
      <P_Card
        title="Membres du cabinet"
        desc="Gérer les accès, les rôles et les permissions de votre équipe."
        action={<button className="btn accent"><Icon.Plus/> Inviter</button>}>
        <div className="member-table">
          <div className="mt-head">
            <div>Personne</div>
            <div>Rôle</div>
            <div className="num">OEAQ</div>
            <div>Statut</div>
            <div></div>
          </div>
          {MEMBERS.map((m, i) => (
            <div className="mt-row" key={i}>
              <div className="mt-person">
                <div className="mt-avatar">{m.name.split(" ").map(w => w[0]).slice(0,2).join("")}</div>
                <div>
                  <div className="mt-name">{m.name}</div>
                  <div className="mt-email">{m.email}</div>
                </div>
              </div>
              <div className="mt-role">{m.role}</div>
              <div className="num">{m.oeaq !== "—" ? <span className="numeric">{m.oeaq}</span> : <span className="muted">—</span>}</div>
              <div>
                <span className={`mt-pill ${m.status}`}>
                  {m.status === "active" ? "Actif" : "Invitation envoyée"}
                </span>
              </div>
              <div className="mt-actions">
                <button className="btn ghost btn-sm">Gérer</button>
              </div>
            </div>
          ))}
        </div>
      </P_Card>

      <P_Card title="Permissions par défaut" desc="Ce qu'un nouveau membre peut faire à son arrivée.">
        <P_Toggle on={true}  onChange={() => {}} label="Créer des dossiers" desc="Ouvrir de nouveaux dossiers d'évaluation."/>
        <P_Toggle on={true}  onChange={() => {}} label="Consulter la bibliothèque" desc="Accéder aux ventes, marchés, coûts et taux."/>
        <P_Toggle on={false} onChange={() => {}} label="Signer des rapports" desc="Réservé aux É.A. en règle uniquement."/>
        <P_Toggle on={false} onChange={() => {}} label="Modifier les modèles" desc="Peut affecter tous les dossiers en cours."/>
      </P_Card>
    </>
  );
}

/* ============================================================
   INTÉGRATIONS
   ============================================================ */
const INTEGRATIONS = [
  { id: "oeaq",    name: "Registre OEAQ",        desc: "Synchronise vos adhésions, permis et certificats.", status: "connected", since: "12 janv. 2024" },
  { id: "jlr",     name: "JLR — Ventes immobilières", desc: "Importez automatiquement les ventes comparables.", status: "connected", since: "22 mars 2024" },
  { id: "centris", name: "Centris",              desc: "Données des fiches MLS résidentielles.", status: "connected", since: "22 mars 2024" },
  { id: "role",    name: "Rôle d'évaluation Montréal", desc: "Pré-charge les caractéristiques au moment de la création.", status: "connected", since: "1 mai 2024" },
  { id: "docusign",name: "DocuSign",             desc: "Signature électronique des rapports et attestations.", status: "available", since: null },
  { id: "qb",      name: "QuickBooks",           desc: "Facturation des mandats et suivi des honoraires.", status: "available", since: null },
  { id: "outlook", name: "Microsoft Outlook",    desc: "Synchronisation du calendrier et des rendez-vous de visite.", status: "available", since: null }
];

function SectionIntegrations() {
  return (
    <>
      <P_Card
        title="Intégrations connectées"
        desc="Les sources qui alimentent vos dossiers."
        tight>
        <div className="int-grid">
          {INTEGRATIONS.map(i => (
            <div className={`int-card ${i.status}`} key={i.id}>
              <div className="int-head">
                <div className="int-logo">{i.name.split(" ")[0].slice(0, 2)}</div>
                <span className={`int-status ${i.status}`}>
                  {i.status === "connected" ? <><span className="d"/> Connecté</> : "Disponible"}
                </span>
              </div>
              <div className="int-name">{i.name}</div>
              <div className="int-desc">{i.desc}</div>
              <div className="int-foot">
                {i.status === "connected"
                  ? <>
                      <span className="int-meta">Depuis {i.since}</span>
                      <button className="btn ghost btn-sm">Gérer</button>
                    </>
                  : <button className="btn secondary btn-sm" style={{marginLeft:"auto"}}>Connecter</button>}
              </div>
            </div>
          ))}
        </div>
      </P_Card>
    </>
  );
}

/* ============================================================
   UTILISATION
   ============================================================ */
function SectionUtilisation() {
  return (
    <>
      <P_Card title="Utilisation — mai 2026" desc="Vos compteurs ce mois-ci.">
        <div className="usage-grid">
          <Usage k="Dossiers ouverts"     v={12} max={25}/>
          <Usage k="Rapports signés"      v={8}  max={null} kind="count"/>
          <Usage k="Comparables consultés" v={146} max={null} kind="count"/>
          <Usage k="Stockage"             v={"6,4 Go"} max={"50 Go"} kind="storage"/>
        </div>
      </P_Card>

      <P_Card title="Répartition de vos dossiers" desc="Vos 12 dossiers actifs par type de mandat.">
        <div className="breakdown">
          <BD k="Hypothécaire" v={5} total={12} color="var(--navy)"/>
          <BD k="Pré-vente"    v={3} total={12} color="var(--ochre)"/>
          <BD k="Successoral"  v={2} total={12} color="var(--verdigris)"/>
          <BD k="Litige"       v={1} total={12} color="var(--oxblood)"/>
          <BD k="Acquisition"  v={1} total={12} color="var(--ink-mute)"/>
        </div>
      </P_Card>

      <P_Card title="Historique mensuel" desc="Dossiers ouverts par mois sur les 6 derniers mois.">
        <div className="history-bars">
          {[
            { m: "Déc.", n: 11 },
            { m: "Janv.", n: 11 },
            { m: "Févr.", n: 12 },
            { m: "Mars", n: 16 },
            { m: "Avril", n: 18 },
            { m: "Mai", n: 14 }
          ].map((x, i) => {
            const pct = (x.n / 20) * 100;
            return (
              <div className="hb-col" key={i}>
                <div className="hb-val numeric">{x.n}</div>
                <div className="hb-bar"><span style={{height: `${pct}%`}}/></div>
                <div className="hb-m">{x.m}</div>
              </div>
            );
          })}
        </div>
      </P_Card>

      <div className="billing-note">
        <div className="bn-icon"><Icon.Seal/></div>
        <div className="bn-text">
          <b>La facturation est gérée par votre cabinet.</b>
          <span>
            L'abonnement de <b>Tremblay Évaluations</b> couvre 4 utilisateurs. Pour
            consulter les factures ou modifier le forfait, contactez votre administrateur ou
            <a> écrivez à facturation@evalimmo.ca</a>.
          </span>
        </div>
      </div>
    </>
  );
}

function BD({ k, v, total, color }) {
  const pct = (v / total) * 100;
  return (
    <div className="bd-row">
      <div className="bd-k">{k}</div>
      <div className="bd-bar">
        <span style={{width: `${pct}%`, background: color}}/>
      </div>
      <div className="bd-v numeric">{v}</div>
    </div>
  );
}

function Usage({ k, v, max, kind = "count" }) {
  let pct = 0;
  if (max != null) {
    if (kind === "storage") pct = 13; // 6.4 / 50
    else if (typeof v === "number") pct = Math.min(100, (v / max) * 100);
  }
  return (
    <div className="usage">
      <div className="us-k">{k}</div>
      <div className="us-v numeric">
        {v} {max != null && <span className="us-max">/ {max}</span>}
      </div>
      {max != null && (
        <div className="us-bar">
          <span className="us-fill" style={{width: `${pct}%`}}/>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   SÉCURITÉ
   ============================================================ */
function SectionSecurite() {
  const [twofa, setTwofa] = useState(true);
  const [sso, setSso] = useState(true);
  const [autosign, setAutosign] = useState(false);

  return (
    <>
      <P_Card title="Mot de passe" action={<button className="btn ghost">Changer</button>}>
        <P_Row k="Dernière modification" v="il y a 4 mois"/>
        <P_Row k="Robustesse"            v={<span className="strength good">Excellent</span>}/>
      </P_Card>

      <P_Card title="Authentification" desc="Comment vous accédez à votre cabinet.">
        <P_Toggle on={twofa} onChange={setTwofa}
          label="Double authentification"
          desc="Code unique envoyé par appli (Authenticator, Microsoft Authy)."/>
        <P_Toggle on={sso} onChange={setSso}
          label="Connexion via Microsoft 365"
          desc="Activée pour tous les membres du cabinet."/>
        <P_Toggle on={autosign} onChange={setAutosign}
          label="Signature biométrique sur les rapports"
          desc="Confirmation par Touch ID / Windows Hello à la signature finale."/>
      </P_Card>

      <P_Card title="Sessions actives" action={<button className="btn ghost">Tout déconnecter</button>}>
        <div className="session">
          <div className="sess-icon">💻</div>
          <div className="sess-main">
            <div className="sess-name">MacBook Pro — Maxime · cette session</div>
            <div className="sess-meta">Safari · Montréal, QC · IP 24.122.•.• · Connecté il y a 4 h</div>
          </div>
          <span className="sess-tag current">Actuel</span>
        </div>
        <div className="session">
          <div className="sess-icon">📱</div>
          <div className="sess-main">
            <div className="sess-name">iPhone — Maxime</div>
            <div className="sess-meta">App iOS · Outremont, QC · Connecté il y a 2 jours</div>
          </div>
          <button className="btn ghost btn-sm">Déconnecter</button>
        </div>
        <div className="session">
          <div className="sess-icon">💻</div>
          <div className="sess-main">
            <div className="sess-name">Windows — Bureau (cabinet)</div>
            <div className="sess-meta">Edge · Montréal, QC · Connecté il y a 1 semaine</div>
          </div>
          <button className="btn ghost btn-sm">Déconnecter</button>
        </div>
      </P_Card>

      <P_Card
        title="Journal d'audit"
        desc="Conservé 7 ans conformément aux normes de l'OEAQ et à la Loi 25.">
        <ul className="audit">
          <li>
            <div className="au-when">Aujourd'hui · 14:22</div>
            <div className="au-what"><b>Maxime Tremblay</b> a signé le rapport <i>2026-0411</i>.</div>
          </li>
          <li>
            <div className="au-when">Hier · 09:08</div>
            <div className="au-what"><b>Émilie Lapointe</b> a ouvert un dossier <i>2026-0418</i>.</div>
          </li>
          <li>
            <div className="au-when">Il y a 3 jours</div>
            <div className="au-what"><b>Système</b> a synchronisé le registre OEAQ.</div>
          </li>
          <li>
            <div className="au-when">Il y a 5 jours</div>
            <div className="au-what"><b>Maxime Tremblay</b> a invité <i>camille@tremblay-eval.ca</i>.</div>
          </li>
        </ul>
        <button className="btn ghost" style={{alignSelf:"flex-start"}}>Voir tout le journal</button>
      </P_Card>
    </>
  );
}

/* ============================================================
   PRÉFÉRENCES
   ============================================================ */
function SectionPreferences() {
  const [agentAuto, setAgentAuto] = useState(true);
  const [emailDigest, setEmailDigest] = useState(true);
  const [deadline, setDeadline] = useState(true);

  return (
    <>
      <P_Card title="Affichage" desc="Comment l'application se présente pour vous.">
        <P_Row k="Langue de l'interface" v="Français (Canada)"/>
        <P_Row k="Format des nombres"    v={<span className="numeric">895 000,00 $</span>}/>
        <P_Row k="Unité de superficie"   v="pi² (pieds carrés)"/>
        <P_Row k="Fuseau horaire"        v="Amérique / Montréal (UTC −5)"/>
      </P_Card>

      <P_Card title="Agent IA" desc="L'assistant qui suggère et automatise dans vos dossiers.">
        <P_Toggle on={agentAuto} onChange={setAgentAuto}
          label="Suggestions automatiques de comparables"
          desc="L'agent vous propose des ventes pertinentes à chaque ouverture de dossier."/>
        <P_Toggle on={true} onChange={() => {}}
          label="Rédaction assistée des notes"
          desc="L'agent peut générer un brouillon de notes à partir des données du dossier."/>
        <P_Toggle on={false} onChange={() => {}}
          label="Signature automatique des rapports"
          desc="Désactivé. La signature finale reste manuelle, conformément à l'OEAQ."/>
      </P_Card>

      <P_Card title="Notifications" desc="Ce qui vous arrive par courriel et dans l'application.">
        <P_Toggle on={deadline}    onChange={setDeadline}    label="Échéances de mandats à venir"        desc="Rappel 3 jours, 1 jour et le matin même."/>
        <P_Toggle on={emailDigest} onChange={setEmailDigest} label="Sommaire hebdomadaire par courriel" desc="Tous les lundis matin — dossiers à signer, marchés notables."/>
        <P_Toggle on={true}        onChange={() => {}}       label="Mises à jour de l'OEAQ"             desc="Avis, normes et changements réglementaires."/>
      </P_Card>
    </>
  );
}

Object.assign(window, {
  SectionProfil, SectionCabinet, SectionMembres,
  SectionIntegrations, SectionUtilisation, SectionSecurite, SectionPreferences
});
