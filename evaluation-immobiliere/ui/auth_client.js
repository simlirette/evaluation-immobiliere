(function () {
  const storageKey = "evaluationImmobiliereAuthV1";
  const defaultState = { role: "supervisor", token: "" };

  function load() {
    try {
      return { ...defaultState, ...JSON.parse(localStorage.getItem(storageKey) || "{}") };
    } catch (_error) {
      return { ...defaultState };
    }
  }

  function save(state) {
    localStorage.setItem(storageKey, JSON.stringify({ role: state.role || "supervisor", token: state.token || "" }));
  }

  function authHeaders(extra = {}) {
    const state = load();
    const headers = { ...extra, "X-Runtime-Role": state.role || "supervisor" };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    return headers;
  }

  async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: authHeaders({ "Content-Type": "application/json", ...(options.headers || {}) })
    });
    const text = await response.text();
    const body = text ? JSON.parse(text) : {};
    if (!response.ok) throw new Error(body.error || body.code || response.statusText);
    return body;
  }

  async function fetchEventStream(url, onEvent) {
    const response = await fetch(url, { headers: authHeaders({ Accept: "text/event-stream" }) });
    const text = await response.text();
    if (!response.ok) {
      let body = {};
      try {
        body = text ? JSON.parse(text) : {};
      } catch (_error) {
        body = {};
      }
      throw new Error(body.error || body.code || response.statusText);
    }

    let count = 0;
    text.split(/\n\n+/).forEach((block) => {
      if (!block.trim()) return;
      const eventLine = block.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = block.split("\n").find((line) => line.startsWith("data:"));
      const eventName = eventLine ? eventLine.replace("event:", "").trim() : "message";
      if (!dataLine) return;
      count += 1;
      onEvent(eventName, JSON.parse(dataLine.replace("data:", "").trim()));
    });
    return count;
  }

  function mount(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const state = load();
    container.innerHTML = `
      <select data-auth-role aria-label="Role runtime">
        <option value="supervisor">supervisor</option>
        <option value="evaluator">evaluator</option>
        <option value="ops">ops</option>
      </select>
      <input data-auth-token type="password" placeholder="token API">
      <button data-auth-save>Sauver auth</button>
      <button data-auth-clear>Effacer</button>
      <span data-auth-status class="muted">auth...</span>
    `;
    const role = container.querySelector("[data-auth-role]");
    const token = container.querySelector("[data-auth-token]");
    const status = container.querySelector("[data-auth-status]");
    role.value = state.role || "supervisor";
    token.value = state.token || "";

    async function refreshStatus() {
      try {
        const payload = await fetchJson("/auth/status");
        status.textContent = payload.enabled ? `${payload.role}: ${payload.authorized ? "autorise" : payload.reason}` : "auth desactivee";
      } catch (error) {
        status.textContent = error.message;
      }
    }

    container.querySelector("[data-auth-save]").addEventListener("click", () => {
      save({ role: role.value, token: token.value });
      refreshStatus();
    });
    container.querySelector("[data-auth-clear]").addEventListener("click", () => {
      save({ role: "supervisor", token: "" });
      role.value = "supervisor";
      token.value = "";
      refreshStatus();
    });
    refreshStatus();
  }

  window.RuntimeAuth = { load, save, headers: authHeaders, fetchJson, fetchEventStream, mount };
})();
