/* eslint-disable */
const { useState, useMemo, useEffect, useRef } = React;

/* ============================================================
   Icons (hairline serif-friendly)
   ============================================================ */
const Icon = {
  Folder: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <path d="M3 6.5h6l2 2.5h10v10.5H3z"/>
    </svg>
  ),
  Template: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <rect x="3.5" y="4.5" width="17" height="15"/>
      <path d="M3.5 9h17M8 9v10.5"/>
    </svg>
  ),
  Archive: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <path d="M3.5 5.5h17v3.5h-17zM5 9v10.5h14V9M10 13h4"/>
    </svg>
  ),
  Library: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <path d="M4 4.5v15M8 4.5v15M12.5 6l5.5 1.5v12L12.5 18z"/>
    </svg>
  ),
  Settings: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 4v3M12 17v3M20 12h-3M7 12H4M17.5 6.5l-2.1 2.1M8.6 15.4l-2.1 2.1M17.5 17.5l-2.1-2.1M8.6 8.6L6.5 6.5"/>
    </svg>
  ),
  Glass: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon glass">
      <circle cx="11" cy="11" r="6"/>
      <path d="M16 16l5 5"/>
    </svg>
  ),
  Grid: () => (
    <svg viewBox="0 0 16 16" fill="currentColor" className="icon"><rect x="1" y="1" width="6" height="6"/><rect x="9" y="1" width="6" height="6"/><rect x="1" y="9" width="6" height="6"/><rect x="9" y="9" width="6" height="6"/></svg>
  ),
  Rows: () => (
    <svg viewBox="0 0 16 16" fill="currentColor" className="icon"><rect x="1" y="2" width="14" height="3"/><rect x="1" y="7" width="14" height="3"/><rect x="1" y="12" width="14" height="3"/></svg>
  ),
  Plus: () => (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" className="icon"><path d="M8 2v12M2 8h12"/></svg>
  ),
  Pin: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M9 3h6l-1 4 3 4-4 1v8l-1 1-1-1v-8l-4-1 3-4z"/>
    </svg>
  ),
  Bell: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" className="icon">
      <path d="M6 17h12l-1.5-2V11a4.5 4.5 0 0 0-9 0v4z"/>
      <path d="M10 19a2 2 0 0 0 4 0"/>
    </svg>
  ),
  Chevron: () => (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M6 4l4 4-4 4"/>
    </svg>
  ),
  ChevronLeft: () => (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M10 4l-4 4 4 4"/>
    </svg>
  ),
  Check: () => (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M3 8.5l3 3 7-7"/>
    </svg>
  ),
  Print: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M7 9V4h10v5M6 9h12a2 2 0 0 1 2 2v5h-4v4H8v-4H4v-5a2 2 0 0 1 2-2zM8 14h8"/>
    </svg>
  ),
  Share: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M12 3v12M8 7l4-4 4 4M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"/>
    </svg>
  ),
  Edit: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M4 20h4l10-10-4-4L4 16v4zM13.5 6.5l4 4"/>
    </svg>
  ),
  Clock: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <circle cx="12" cy="12" r="9"/>
      <path d="M12 7v5l3 2"/>
    </svg>
  ),
  Send: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M5 12h14M13 6l6 6-6 6"/>
    </svg>
  ),
  Sparkle: () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="icon">
      <path d="M12 2l1.8 5.4L19 9l-5.2 1.6L12 16l-1.8-5.4L5 9l5.2-1.6L12 2zM19 14l.9 2.7L22 17.5l-2.1.8L19 21l-.9-2.7L16 17.5l2.1-.8L19 14z"/>
    </svg>
  ),
  Paperclip: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M20 11l-8.5 8.5a4.5 4.5 0 0 1-6.4-6.4l9-9a3 3 0 0 1 4.3 4.3l-8.8 8.8a1.5 1.5 0 0 1-2.1-2.1l7.8-7.8"/>
    </svg>
  ),
  More: () => (
    <svg viewBox="0 0 16 16" fill="currentColor" className="icon">
      <circle cx="3" cy="8" r="1.4"/>
      <circle cx="8" cy="8" r="1.4"/>
      <circle cx="13" cy="8" r="1.4"/>
    </svg>
  ),
  Plug: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M9 3v6M15 3v6M7 9h10v3a5 5 0 0 1-5 5v4"/>
    </svg>
  ),
  Help: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <circle cx="12" cy="12" r="9"/>
      <path d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.6-2.5 2-2.5 3.5"/>
      <circle cx="12" cy="16.5" r=".6" fill="currentColor" stroke="none"/>
    </svg>
  ),
  Sun: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4"/>
    </svg>
  ),
  Moon: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>
    </svg>
  ),
  Seal: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className="icon">
      <path d="M12 2l2.4 2.6 3.4-.6.6 3.4L21 9.6l-1.6 3.1 1.6 3.1-2.6 2.2-.6 3.4-3.4-.6L12 23.4l-2.4-2.6-3.4.6-.6-3.4L3 15.8l1.6-3.1L3 9.6l2.6-2.2.6-3.4 3.4.6z"/>
      <path d="M8.5 12.5l2.5 2.5L16 10"/>
    </svg>
  )
};

/* ============================================================
   Abstract map thumbnails — generated per neighbourhood
   ============================================================ */
const Maps = {
  outremont: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,28 L320,28 M0,58 L320,58 M0,92 L320,92 M0,120 L320,120"/>
        <path d="M40,0 L40,144 M96,0 L96,144 M168,0 L168,144 M232,0 L232,144 M278,0 L278,144"/>
        <path d="M0,40 Q80,46 160,38 T320,52" strokeWidth="1.1"/>
      </g>
      <rect x="106" y="66" width="20" height="20" fill="currentColor" opacity=".5"/>
      <rect x="132" y="62" width="14" height="24" fill="currentColor" opacity=".35"/>
      <rect x="152" y="68" width="12" height="18" fill="currentColor" opacity=".45"/>
      <rect x="186" y="64" width="22" height="22" fill="currentColor" opacity=".4"/>
      <g stroke="var(--navy)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="118" cy="76" r="5"/>
      </g>
      <circle cx="118" cy="76" r="2" fill="var(--navy)"/>
    </svg>
  ),
  plateau: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,40 L320,40 M0,80 L320,80 M0,108 L320,108"/>
        <path d="M50,0 L50,144 M110,0 L110,144 M170,0 L170,144 M220,0 L220,144 M270,0 L270,144"/>
      </g>
      <rect x="120" y="50" width="40" height="28" fill="currentColor" opacity=".45"/>
      <rect x="164" y="50" width="14" height="28" fill="currentColor" opacity=".3"/>
      <rect x="182" y="56" width="20" height="22" fill="currentColor" opacity=".5"/>
      <g stroke="var(--navy)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="140" cy="64" r="5"/>
      </g>
      <circle cx="140" cy="64" r="2" fill="var(--navy)"/>
    </svg>
  ),
  rosemont: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,30 L320,30 M0,72 L320,72 M0,112 L320,112"/>
        <path d="M30,0 L30,144 M80,0 L80,144 M140,0 L140,144 M200,0 L200,144 M260,0 L260,144"/>
      </g>
      <rect x="86" y="84" width="48" height="24" fill="currentColor" opacity=".35"/>
      <g stroke="var(--ink-faint)" strokeWidth="1" fill="var(--paper-hi)" strokeDasharray="3 2">
        <circle cx="110" cy="96" r="5"/>
      </g>
      <circle cx="110" cy="96" r="2" fill="var(--ink-faint)"/>
    </svg>
  ),
  westmount: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,46 Q60,30 140,40 T320,38" strokeWidth="1.2"/>
        <path d="M0,80 L320,80 M0,108 L320,108"/>
        <path d="M48,40 L60,144 M120,38 L130,144 M180,42 L190,144 M240,40 L250,144"/>
      </g>
      <rect x="130" y="60" width="26" height="22" fill="currentColor" opacity=".5"/>
      <rect x="162" y="56" width="18" height="26" fill="currentColor" opacity=".35"/>
      <g stroke="var(--navy)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="146" cy="70" r="5"/>
      </g>
      <circle cx="146" cy="70" r="2" fill="var(--navy)"/>
    </svg>
  ),
  villeray: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,38 L320,38 M0,72 L320,72 M0,106 L320,106"/>
        <path d="M40,0 L40,144 M100,0 L100,144 M160,0 L160,144 M220,0 L220,144 M280,0 L280,144"/>
      </g>
      <rect x="108" y="44" width="44" height="22" fill="currentColor" opacity=".45"/>
      <rect x="166" y="80" width="48" height="22" fill="currentColor" opacity=".4"/>
      <g stroke="var(--verdigris)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="130" cy="56" r="5"/>
      </g>
      <circle cx="130" cy="56" r="2" fill="var(--verdigris)"/>
    </svg>
  ),
  centre: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,30 L320,30 M0,68 L320,68 M0,108 L320,108"/>
        <path d="M40,0 L40,144 M80,0 L80,144 M120,0 L120,144 M160,0 L160,144 M200,0 L200,144 M240,0 L240,144 M280,0 L280,144"/>
      </g>
      <rect x="124" y="38" width="20" height="60" fill="currentColor" opacity=".55"/>
      <rect x="148" y="44" width="14" height="54" fill="currentColor" opacity=".4"/>
      <rect x="168" y="50" width="18" height="48" fill="currentColor" opacity=".5"/>
      <g stroke="var(--verdigris)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="134" cy="68" r="5"/>
      </g>
      <circle cx="134" cy="68" r="2" fill="var(--verdigris)"/>
    </svg>
  ),
  "mile-end": () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,40 L320,40 M0,80 L320,80 M0,116 L320,116"/>
        <path d="M70,0 L70,144 M150,0 L150,144 M220,0 L220,144"/>
      </g>
      <rect x="86" y="50" width="58" height="24" fill="currentColor" opacity=".4"/>
      <g stroke="var(--ink-faint)" strokeWidth="1" fill="var(--paper-hi)" strokeDasharray="3 2">
        <circle cx="116" cy="62" r="5"/>
      </g>
      <circle cx="116" cy="62" r="2" fill="var(--ink-faint)"/>
    </svg>
  ),
  pointe: () => (
    <svg className="map" viewBox="0 0 320 144" preserveAspectRatio="none" aria-hidden="true">
      <g stroke="currentColor" strokeWidth=".6" fill="none">
        <path d="M0,90 Q60,86 140,80 T320,72" strokeWidth="1.2"/>
        <path d="M0,40 L320,40 M0,110 L320,110"/>
        <path d="M40,0 L48,90 M120,0 L130,80 M200,0 L208,75 M270,0 L278,72"/>
      </g>
      <rect x="150" y="46" width="58" height="22" fill="currentColor" opacity=".5"/>
      <g stroke="var(--ochre)" strokeWidth="1" fill="var(--paper-hi)">
        <circle cx="172" cy="58" r="5"/>
      </g>
      <circle cx="172" cy="58" r="2" fill="var(--ochre)"/>
    </svg>
  )
};

/* ============================================================
   Sidebar
   ============================================================ */
function Sidebar({ active, counts, pinned = [], recents = [], currentDossier = null }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => (window.EvalImmoTheme ? window.EvalImmoTheme.get() : "light"));
  const menuRef = useRef(null);

  useEffect(() => {
    function onChange(e) { setTheme(e.detail); }
    window.addEventListener("theme-change", onChange);
    return () => window.removeEventListener("theme-change", onChange);
  }, []);

  function pickTheme(t) {
    if (window.EvalImmoTheme) window.EvalImmoTheme.set(t);
  }

  useEffect(() => {
    if (!menuOpen) return;
    function onDoc(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  return (
    <aside className="sidebar no-select" data-screen-label="01 Sidebar">
      <div className="brand">
        <div className="wordmark">Éval&nbsp;<em>Immo</em></div>
        <div className="tag">Évaluateurs agréés — Québec</div>
      </div>

      {currentDossier && (
        <div className="current-dossier" title={`${currentDossier.addr}, ${currentDossier.city}`}>
          <div className="cd-addr">
            {currentDossier.addr}
            <span className="cd-id numeric">{currentDossier.id}</span>
          </div>
          <div className="cd-city">{currentDossier.city}, Montréal</div>
        </div>
      )}

      <nav className="nav">
        <div className="nav-label">Travail</div>
        <a className={active === "nouveau" ? "active" : ""} href="nouveau-dossier.html">
          <Icon.Plus/>
          <span>Nouveau dossier</span>
        </a>
        <a className={active === "dossiers" ? "active" : ""} href="mes-dossiers.html">
          <Icon.Folder/>
          <span>Dossiers</span>
          <span className="count numeric">{counts.dossiers}</span>
        </a>
        <a className={active === "bibliotheque" ? "active" : ""} href="bibliotheque.html">
          <Icon.Library/>
          <span>Bibliothèque</span>
          <span className="count numeric">348</span>
        </a>
        <a className={active === "modeles" ? "active" : ""} href="modeles.html">
          <Icon.Template/>
          <span>Modèles</span>
          <span className="count numeric">6</span>
        </a>
        <a className={active === "archives" ? "active" : ""} href="archives.html">
          <Icon.Archive/>
          <span>Archives</span>
          <span className="count numeric">142</span>
        </a>

        {pinned.length > 0 && (
          <>
            <div className="nav-label" style={{marginTop: 18}}>Épinglés</div>
            {pinned.map(d => (
              <a key={d.id} className="nav-doc" title={`${d.addr}, ${d.city}`}
                 href={`dossier.html?id=${encodeURIComponent(d.id)}`}>
                <span className={`dot ${d.status}`}/>
                <span className="doc-label">{d.addr}</span>
              </a>
            ))}
          </>
        )}

        {recents.length > 0 && (
          <>
            <div className="nav-label" style={{marginTop: 18}}>Récents</div>
            {recents.map(d => (
              <a key={d.id} className="nav-doc" title={`${d.addr}, ${d.city}`}
                 href={`dossier.html?id=${encodeURIComponent(d.id)}`}>
                <span className={`dot ${d.status}`}/>
                <span className="doc-label">{d.addr}</span>
              </a>
            ))}
          </>
        )}

      </nav>
      <div className="spacer"/>
      <div className="firm-wrap" ref={menuRef}>
        {menuOpen && (
          <div className="firm-menu" role="menu">
            <button role="menuitem" className="firm-menu-item" onClick={() => window.location.href = "parametres.html"}>
              <Icon.Settings/>
              <span>Paramètres</span>
            </button>
            <button role="menuitem" className="firm-menu-item" onClick={() => window.location.href = "aide.html"}>
              <Icon.Help/>
              <span>Aide</span>
            </button>
            <div className="firm-menu-sep"/>
            <div className="theme-toggle-row" role="group" aria-label="Thème">
              <span className="ttr-label">
                {theme === "dark" ? <Icon.Moon/> : <Icon.Sun/>}
                <span>Apparence</span>
              </span>
              <span className="theme-pill">
                <button className={theme === "light" ? "active" : ""} onClick={() => pickTheme("light")}>
                  <Icon.Sun/>Clair
                </button>
                <button className={theme === "dark" ? "active" : ""} onClick={() => pickTheme("dark")}>
                  <Icon.Moon/>Sombre
                </button>
              </span>
            </div>
            <div className="firm-menu-sep"/>
            <button role="menuitem" className="firm-menu-item" onClick={() => window.location.href = "login.html"}>
              <span>Se déconnecter</span>
            </button>
          </div>
        )}
        <button
          className={`firm ${menuOpen ? "open" : ""}`}
          type="button"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(o => !o)}>
          <div className="seal">MT</div>
          <div className="who">
            <div className="name">Maxime Tremblay</div>
            <div className="credential">É.A. <span className="numeric">— OEAQ 4218</span></div>
          </div>
          <Icon.Chevron/>
        </button>
      </div>
    </aside>
  );
}

/* ============================================================
   Dossier card
   ============================================================ */
function DossierCard({ d, onPin }) {
  const statusText = d.status === "complet"
    ? "Complet"
    : d.status === "brouillon"
      ? "Brouillon"
      : "En cours";

  function open() { window.location.href = `dossier.html?id=${encodeURIComponent(d.id)}`; }

  return (
    <article className="dossier-card" data-screen-label={`Dossier ${d.id}`} onClick={open}>
      <div className="card-head">
        <span className={`status-chip ${d.status}`}>
          <span>{statusText}</span>
          {d.status === "encours" && <span className="stage">· {d.stage}/5</span>}
        </span>
        <button
          className={`pin ${d.pinned ? "active" : ""}`}
          title={d.pinned ? "Désépingler" : "Épingler"}
          onClick={(e) => { e.stopPropagation(); onPin(d.id); }}>
          <Icon.Pin/>
        </button>
      </div>

      <div className="addr">
        {d.addr}
        <span className="city">{d.city}, Montréal &nbsp;·&nbsp; <em>{d.type}</em></span>
      </div>

      <div className="facts">
          <div className="fact">
            <div className="k">Année</div>
            <div className={`v ${d.year ? "" : "muted"}`}>{d.year ?? "—"}</div>
          </div>
          <div className="fact">
            <div className="k">Superficie</div>
            <div className={`v ${d.area ? "" : "muted"}`}>
              {d.area ? <>{formatNum(d.area)} pi²</> : "—"}
            </div>
          </div>
          <div className="fact">
            <div className="k">{d.status === "complet" ? "Valeur" : "Stade"}</div>
            <div className={`v ${d.status === "complet" ? "value" : ""}`}>
              {d.status === "complet"
                ? formatMoney(d.value)
                : d.status === "brouillon"
                  ? <span className="muted">Saisie</span>
                  : window.STAGE_LABELS[d.stage] || "—"}
            </div>
          </div>
        </div>

      <div className="foot">
        <span className="client">{d.client}</span>
        <span className="stamp">Mod. {d.modifiedLabel}</span>
      </div>
    </article>
  );
}

/* ============================================================
   Dossier row (list view)
   ============================================================ */
function DossierRow({ d, onPin }) {
  const statusText = d.status === "complet"
    ? "Complet"
    : d.status === "brouillon"
      ? "Brouillon"
      : `En cours · ${d.stage}/5`;

  const stageOrValue = d.status === "complet"
    ? <span className="v value">{formatMoney(d.value)}</span>
    : d.status === "brouillon"
      ? <span className="v muted">Saisie</span>
      : <span className="v">{window.STAGE_LABELS[d.stage] || "—"}</span>;

  return (
    <article className="dossier-row" data-screen-label={`Dossier ${d.id}`}
             onClick={() => window.location.href = `dossier.html?id=${encodeURIComponent(d.id)}`}>
      <div className="col-addr">
        <div className="addr-line">
          <span className={`status-dot ${d.status}`} title={statusText}/>
          <span className="addr">{d.addr}</span>
        </div>
        <div className="city">{d.city}, Montréal</div>
      </div>
      <div className="col-type">{d.type}</div>
      <div className="col-year numeric">{d.year ?? "—"}</div>
      <div className="col-area numeric">
        {d.area ? <>{formatNum(d.area)} pi²</> : "—"}
      </div>
      <div className="col-stage">{stageOrValue}</div>
      <div className="col-client">{d.client}</div>
      <div className="col-modified">{d.modifiedLabel}</div>
      <div className="col-actions">
        <button
          className={`pin ${d.pinned ? "active" : ""}`}
          title={d.pinned ? "Désépingler" : "Épingler"}
          onClick={(e) => { e.stopPropagation(); onPin(d.id); }}>
          <Icon.Pin/>
        </button>
      </div>
    </article>
  );
}

/* ============================================================
   Dropdown — styled-everywhere select (matches page aesthetic)
   ============================================================ */
function Dropdown({ label, value, options, onChange, align = "left" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    function onKey(e) { if (e.key === "Escape") setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const current = options.find(o => (typeof o === "string" ? o : o.value) === value);
  const currentLabel = current
    ? (typeof current === "string" ? current : current.label)
    : value;

  return (
    <div className={`dropdown ${open ? "open" : ""}`} ref={ref}>
      {label && <span className="dd-label">{label}</span>}
      <button
        type="button"
        className="dd-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}>
        <span className="dd-value">{currentLabel}</span>
        <span className="dd-caret">
          <svg viewBox="0 0 10 6" width="9" height="6" aria-hidden="true">
            <path d="M0 1l5 4 5-4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </span>
      </button>
      {open && (
        <div className={`dd-menu dd-menu-${align}`} role="listbox">
          {options.map(o => {
            const v = typeof o === "string" ? o : o.value;
            const l = typeof o === "string" ? o : o.label;
            const active = v === value;
            return (
              <button
                key={v}
                type="button"
                role="option"
                aria-selected={active}
                className={`dd-item ${active ? "active" : ""}`}
                onClick={() => { onChange(v); setOpen(false); }}>
                <span className="dd-item-label">{l}</span>
                {active && <Icon.Check/>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ============================================================
   Format helpers
   ============================================================ */
function formatMoney(v) {
  if (v == null) return "—";
  // 895 000 $ — Quebec style: space as thousands separator, $ after
  return v.toLocaleString("fr-CA").replace(/,/g, " ") + " $";
}
function formatNum(v) {
  return v.toLocaleString("fr-CA").replace(/,/g, " ");
}

Object.assign(window, { Sidebar, DossierCard, DossierRow, Dropdown, Icon, Maps, formatMoney, formatNum });
