# Project Audit - 2026-05-08

Scope audited:
- Local app: `C:\Users\simon\eval-immo`
- Frontend mockups: `C:\Users\simon\frontend-mockups`, especially `v1-liquid-glass.html`
- GitHub repository: `simlirette/evaluation-immobiliere`

## Executive Verdict

The project is a strong V1 prototype/workbench, not a production-complete real-estate appraisal product.

The visual direction is clear and the current Next.js UI is already close to the `v1-liquid-glass.html` desktop mockup. The Python runtime has useful deterministic orchestration, artifacts, audit traces, compliance gates, assistant routing, review/package flows, and a browser-facing API. However, the project has material gaps in deployment topology, authentication, persistence, production security, real agent execution, test coverage, and responsive UX.

Current completion estimate:
- UI shell and desktop V1 look: 70-80%
- Runtime prototype and deterministic pipeline: 65-75%
- Production data/persistence: 25-35%
- Auth/security/deployment readiness: 25-35%
- Testing/QA/CI: 10-20%
- Agentic product maturity: 35-45%

## Verified Facts

Build and checks:
- `npm.cmd run build` passes when network access is available for Google fonts.
- `.\node_modules\.bin\tsc.cmd --noEmit` passes.
- Local Python is not available as `python`, `py`, or `python3`, so backend compilation/smoke tests could not be run locally.
- `backend/tests` contains fixtures only, no executable test suite.

Git/repository state:
- Local branch is `master`.
- GitHub default branch is `main`.
- Active GitHub code appears to live on branch `frontend`.
- GitHub compare reported no common ancestor between `main` and `frontend`.
- `main` did not expose `README.md` or `package.json` through the GitHub API during this audit.

Important local paths:
- Frontend app: `src/app`, `src/components`, `src/lib/runtime-api.ts`
- Runtime API: `backend/api.py`
- Runtime engine: `backend/engine/runtime.py`
- Historical Supabase schema: `supabase/migrations/001_v3_schema.sql`
- Historical plans archived under `docs/superpowers-optimized/plans/archive`

## What Is Complete Enough

Frontend:
- Next.js 16 app builds successfully.
- Main routes exist: `/`, `/dossiers`, `/dossier/[id]`, `/login`, `/auth/callback`.
- The UI implements the core V1 shell: floating sidebar, tab pill, dossier grid, Dossier/Marche/Analyse/Rapport panels, split report view, loading skeletons, empty state, theme toggle.
- The visual language mostly follows `v1-liquid-glass.html`: warm linen background, floating glass panels, serif wordmark, compact agent messages, rounded search/input controls.

Runtime/API:
- `backend/api.py` exposes local product/runtime/review/ops/assistant routes.
- Runtime sessions are auditable and artifact-based.
- The engine emits events and writes artifacts per pipeline step.
- Compliance flags, warnings, blocking failures, package generation, and internal review workflows exist in prototype form.
- Assistant responses are bounded and explicitly avoid certification.

Architecture:
- The frontend now uses a runtime facade through `src/lib/runtime-api.ts`.
- `src/lib/supabase/queries/*` are currently compatibility shims over the runtime API, not direct Supabase queries.
- Supabase auth scaffolding exists, but it is no longer the active access-control path.

## Critical Gaps

### P0 - Branch and deployment source of truth

The active code is not on the GitHub default branch. Local `master` and remote `frontend` contain the app; `main` is unrelated enough that GitHub could not compare it to `frontend`. This must be fixed before relying on GitHub/Vercel automation.

Impact:
- Vercel or collaborators may deploy/review the wrong branch.
- The repository landing page can look empty or stale.
- Pull requests and future automation will be confusing.

Required outcome:
- Choose one canonical branch, preferably `main`.
- Move active code there or change GitHub default branch to the active branch.
- Add a real README and operating docs on the canonical branch.

### P0 - Runtime API cannot be safely deployed as currently wired

`src/lib/runtime-api.ts` defaults to `http://127.0.0.1:8796`. In production, browser code using that default calls the user's own machine, not Railway or another backend.

Also, the frontend client sends no auth token. The backend supports token auth through `EVAL_RUNTIME_API_TOKEN`, but if the token is enabled, the current browser client cannot call it. If the token is not enabled, the backend is effectively open, and CORS allows `*`.

Relevant files:
- `src/lib/runtime-api.ts`: default runtime URL and fetch wrapper.
- `backend/api.py`: CORS and optional token behavior.

Required outcome:
- Add a Next.js server-side proxy/BFF route for runtime calls.
- Keep `RUNTIME_API_URL` and `RUNTIME_API_TOKEN` server-only.
- Remove browser reliance on `NEXT_PUBLIC_RUNTIME_API_URL` for privileged runtime calls.
- Restrict backend CORS in production.

### P0 - Auth model is inconsistent

The Supabase login page and callback exist, but middleware currently allows every request. The sidebar action is not a real sign-out; it routes back to dossiers.

Impact:
- `/dossiers` and `/dossier/*` are public in the current app.
- Login exists but does not govern the product.
- Future assumptions about user identity, tenancy, and audit ownership will be false.

Required outcome:
- Decide whether V1 is authenticated or explicitly local-only.
- If authenticated, restore middleware protection and make runtime calls user-aware through the BFF.
- If local-only, remove misleading login/auth scaffolding from the V1 UI and docs.

### P0 - Persistence and dossier lifecycle are prototype-only

The UI looks like it supports creation, deletion, pinning, and upload, but these are not full persisted operations:
- New dossier always starts from `case_pilote_residentiel_standard.json`.
- Delete is a no-op.
- Pin is a no-op.
- Upload returns a local in-memory document descriptor and does not ingest/process/persist the file.

Impact:
- The product can demo, but not manage real user dossiers.
- Users can believe work is saved when it is not.
- Any real appraisal workflow will lose or misrepresent state.

Required outcome:
- Define the system of record: runtime filesystem, Supabase, or both.
- Implement archive/delete semantics explicitly.
- Persist pins per user or per local workspace.
- Implement document upload ingestion into the runtime and artifact/source index.

### P1 - Agentic layer is not a real LLM agent loop yet

The backend exposes named agents and routes questions, but assistant responses are deterministic summaries from runtime artifacts. The API itself reports `llm_native_agent_loop_connected: False`.

This is acceptable for a deterministic V1 review workbench, but not for a product marketed as fully agentic.

Required outcome:
- Decide whether V1 stays deterministic or connects a real LLM/agent runtime.
- If LLM is added, implement tool permissions, citation policy, source grounding, prompt/version control, failure modes, and audit logging.
- Keep professional boundaries: no automatic certification or invented evaluator responses.

### P1 - Test coverage is not sufficient

The frontend typechecks and builds, but there are no lint, unit test, backend test, API contract test, or E2E scripts in `package.json`. Backend `tests` currently contains fixtures only.

Required outcome:
- Add minimal test scripts.
- Add backend smoke tests for `/health`, `/app/demo`, `/app/state`, `/app/message`, `/app/review/validate`, `/app/package`.
- Add frontend tests for navigation, empty/loading states, and runtime error states.
- Add E2E happy path with a running runtime API.

### P1 - Frontend has desktop parity but not responsive/product parity

The current UI is close to `v1-liquid-glass.html` on desktop. Missing or incomplete:
- Mobile/tablet layout strategy.
- Responsive dossier grid; it is fixed at 3 columns.
- Runtime/API error states in every panel.
- Empty states inside Dossier/Marche/Analyse/Rapport panels.
- Persisted report edit/save behavior.
- Accessible keyboard/focus states and semantic buttons.
- Consistent French accents and copy polish.
- Filter button has no behavior.

The mockup itself also has no meaningful responsive rules, so responsive UX needs product design rather than direct porting.

### P1 - Regulatory/professional content needs hard boundaries

The current app is safer than the mockup because it says non-certified and requires human validation. Keep that direction. Avoid mockup wording that implies OEAQ certification, inspection, signature, or external evaluator response unless it is truly present.

Required outcome:
- Add a compliance copy matrix.
- Make "draft", "internal review", "evaluator validation required", and "not certified" states explicit.
- Prevent package generation unless review/integrity gates pass.

## UI/UX Analysis Against `v1-liquid-glass.html`

What matches well:
- Floating 200px sidebar over a full-screen background.
- Top tab pill pattern.
- Centered chat-style panel content with 640px max width.
- Warm glass palette and compact professional tone.
- Dossier grid and report split-view pattern.
- Dark mode token structure.

What is weaker in the current app:
- The `v1-liquid-glass.html` mockup feels slightly more premium because it has stronger inset glass shadows, more careful sidebar recent/pinned grouping, and richer report document content.
- Current panel content is sparser and more obviously scaffolded.
- The report editor exists visually, but edit persistence is not implemented.
- Some labels are ASCII-only or simplified (`Marche`, `Prets`, `Generer`) while the mockup uses polished French typography.
- The app uses many inline SVG icons; standardizing on an icon library would improve consistency and maintainability.
- No mobile state exists. The current `h-screen`, fixed sidebar, fixed `paddingLeft: 224px`, and fixed 3-column grids will fail on narrow screens.

Target UX posture:
- Keep the quiet professional workbench style.
- Do not make a landing page.
- First screen should remain operational: dossiers or active dossier.
- Prioritize scanability, provenance, validation status, and next action over decorative content.

## Plan Inventory

Archived:
- `docs/superpowers-optimized/plans/archive/2026-05-06-supabase-auth.archived.md`
- `docs/superpowers-optimized/plans/archive/2026-05-06-v3-supabase-data.archived.md`

Active:
- `docs/superpowers-optimized/plans/2026-05-08-project-completion-sessions.md`

Reason:
- The archived plans describe the older Supabase-direct direction. The active code now uses the Python runtime as the business data source and keeps Supabase only as historical/auth scaffolding.
