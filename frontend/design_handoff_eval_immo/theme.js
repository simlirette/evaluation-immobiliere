/* eslint-disable */
/* Éval Immo — theme init (run as early as possible to avoid FOUC) */
(function() {
  try {
    var t = localStorage.getItem("evalimmo-theme");
    if (!t) {
      t = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    document.documentElement.setAttribute("data-theme", t);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "light");
  }
  window.EvalImmoTheme = {
    get: function() { return document.documentElement.getAttribute("data-theme") || "light"; },
    set: function(t) {
      document.documentElement.setAttribute("data-theme", t);
      try { localStorage.setItem("evalimmo-theme", t); } catch (e) {}
      window.dispatchEvent(new CustomEvent("theme-change", { detail: t }));
    },
    toggle: function() { this.set(this.get() === "dark" ? "light" : "dark"); }
  };
})();
