/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

const SECTIONS = [
  { id: "profil",       label: "Profil",        icon: "user" },
  { id: "cabinet",      label: "Cabinet",       icon: "building" },
  { id: "membres",      label: "Membres",       icon: "users" },
  { id: "integrations", label: "Intégrations",  icon: "plug" },
  { id: "utilisation",  label: "Utilisation",   icon: "chart" },
  { id: "securite",     label: "Sécurité",      icon: "lock" },
  { id: "preferences",  label: "Préférences",   icon: "settings" }
];

function ParametresPage() {
  const pinnedDossiers = useMemo(() => window.DOSSIERS.filter(x => x.pinned), []);
  const recentDossiers = useMemo(
    () => window.DOSSIERS.slice().sort((a, b) => b.modifiedAt.localeCompare(a.modifiedAt)).slice(0, 3),
    []
  );
  const counts = useMemo(() => ({ dossiers: window.DOSSIERS.length }), []);

  // Allow ?section=cabinet style deep links
  const initial = new URLSearchParams(location.search).get("section") || "profil";
  const [section, setSection] = useState(initial);

  function pickSection(id) {
    setSection(id);
    const u = new URL(location.href);
    u.searchParams.set("section", id);
    history.replaceState(null, "", u);
  }

  const SectionView = (
    section === "profil"       ? SectionProfil :
    section === "cabinet"      ? SectionCabinet :
    section === "membres"      ? SectionMembres :
    section === "integrations" ? SectionIntegrations :
    section === "utilisation" ? SectionUtilisation :
    section === "securite"     ? SectionSecurite :
                                 SectionPreferences
  );

  return (
    <div className="app" data-screen-label="07 Paramètres">
      <Sidebar active="" counts={counts} pinned={pinnedDossiers} recents={recentDossiers}/>

      <div className="main">
        <div className="topbar param-topbar">
          <div className="pagehead param-head">
            <div>
              <h1>Paramètres</h1>
              <div className="subtitle">
                Personnalisez votre profil, votre cabinet, vos intégrations et la sécurité.
              </div>
            </div>
          </div>
        </div>

        <div className="param-body">
          {/* Sub-nav */}
          <aside className="param-nav">
            {SECTIONS.map(s => (
              <button
                key={s.id}
                className={`pn-item ${section === s.id ? "active" : ""}`}
                onClick={() => pickSection(s.id)}>
                <SettingsIcon name={s.icon}/>
                <span>{s.label}</span>
              </button>
            ))}
          </aside>

          {/* Section */}
          <section className="param-main">
            <SectionView/>
          </section>
        </div>
      </div>
    </div>
  );
}

function SettingsIcon({ name }) {
  const common = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "user":     return <svg {...common}><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></svg>;
    case "building": return <svg {...common}><path d="M5 21V5l8-2v18M5 21h14v-9l-6-2"/><path d="M9 8h1M9 12h1M9 16h1M15 13h1M15 17h1"/></svg>;
    case "users":    return <svg {...common}><circle cx="9" cy="9" r="3"/><circle cx="17" cy="10" r="2.4"/><path d="M3 20a6 6 0 0 1 12 0M14 20a4.5 4.5 0 0 1 8 0"/></svg>;
    case "plug":     return <svg {...common}><path d="M9 3v6M15 3v6M7 9h10v3a5 5 0 0 1-5 5v4"/></svg>;
    case "card":     return <svg {...common}><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 11h18M7 15h3"/></svg>;
    case "chart":    return <svg {...common}><path d="M4 20V8M10 20V4M16 20v-9M22 20H2"/></svg>;
    case "lock":     return <svg {...common}><rect x="4.5" y="11" width="15" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>;
    case "settings": return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>;
    default: return null;
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(<ParametresPage/>);
