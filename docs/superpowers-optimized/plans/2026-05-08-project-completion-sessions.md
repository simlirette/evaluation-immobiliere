# Project Completion Plan - Session-Based

Status: active source of truth as of 2026-05-08.

Goal: finish `evaluation-immobiliere` without leaving hidden gaps across product, frontend, runtime, security, persistence, QA, and deployment.

Working principle: complete the product as a runtime-backed agentic workbench first. Do not revive the old Supabase-direct data plan unless a session explicitly decides Supabase is the system of record.

## Definition of Done

The project is complete when:
- The canonical GitHub branch is aligned with the deploy branch.
- A user can open the app, authenticate if enabled, create/open a dossier, attach sources, run or inspect runtime artifacts, ask each agent a question, validate internal review, generate a package, and return later without losing state.
- The runtime is not exposed publicly without auth.
- The frontend matches the `v1-liquid-glass.html` desktop direction and has usable tablet/mobile behavior.
- Critical flows have automated tests and a documented manual QA checklist.
- README and environment docs let a new developer run frontend + backend locally.

## Session 1 - Repository And Product Source Of Truth

Outcome:
- One canonical branch and one active plan.
- Clear README and local runbook.

Tasks:
- Decide canonical GitHub branch: move active `frontend`/local `master` code to `main`, or set `frontend` as default.
- Verify Vercel deploy branch matches the canonical branch.
- Replace Create Next App README with product-specific setup.
- Document local frontend/backend startup, required env vars, and known limitations.
- Add `.env.example` entries for frontend and runtime deployment.
- Keep archived plans in `docs/superpowers-optimized/plans/archive`.

Acceptance:
- GitHub default branch shows the real app.
- README states the active architecture: Next.js frontend + Python runtime API.
- `docs/project-audit-2026-05-08.md` and this plan are referenced from README.

Suggested commands:
- `git branch -avv`
- `npm.cmd run build`
- `.\node_modules\.bin\tsc.cmd --noEmit`

## Session 2 - Runtime API Security And BFF Proxy

Outcome:
- Browser never calls privileged runtime endpoints directly.
- Runtime can be deployed behind a token without breaking the app.

Tasks:
- Add Next.js server route proxy, for example `src/app/api/runtime/[...path]/route.ts`.
- Move runtime URL/token to server-only env vars: `RUNTIME_API_URL`, `RUNTIME_API_TOKEN`.
- Update `src/lib/runtime-api.ts` to call `/api/runtime/*` from the browser.
- Add request timeout and readable error mapping.
- Restrict backend CORS for production or document that the BFF is the only exposed caller.
- Make backend token required outside local dev.

Acceptance:
- App works locally through proxy.
- App works with backend token enabled.
- Direct browser calls to Railway runtime are not required.
- Runtime errors render as UI error states, not endless loaders.

Files likely touched:
- `src/lib/runtime-api.ts`
- `src/app/api/runtime/[...path]/route.ts`
- `backend/api.py`
- `.env.example`
- `README.md`

## Session 3 - Auth And User/Tenant Model

Outcome:
- Auth behavior is intentional and internally consistent.

Decision required:
- Option A: authenticated V1 using Supabase Auth.
- Option B: local-only V1 with no login UI.

If Option A:
- Restore middleware protection for `/dossiers` and `/dossier/*`.
- Make `/login` redirect authenticated users.
- Wire real sign-out in sidebar.
- Pass authenticated user context to runtime through the BFF.
- Add audit user fields where runtime writes sessions/reviews/packages.

If Option B:
- Remove or hide `/login` and `/auth/callback`.
- Remove unused Supabase client code from active paths.
- Make local-only status explicit in UI and README.

Acceptance:
- No misleading login page.
- Protected routes are actually protected if auth is enabled.
- Runtime audit logs can identify the acting user or explicitly mark local dev.

Files likely touched:
- `middleware.ts`
- `src/app/login/*`
- `src/app/auth/callback/route.ts`
- `src/components/layout/SidebarFooter.tsx`
- `backend/api.py`

## Session 4 - Dossier Lifecycle And Persistence

Outcome:
- Dossiers have real lifecycle semantics.

Tasks:
- Choose system of record for dossiers and sessions.
- Replace demo-only creation with a real dossier/session creation API.
- Define archive/delete semantics. Do not pretend to delete immutable audit sessions unless archival is the intended behavior.
- Persist pin/unpin state.
- Fix navigation state after creating a dossier so tab changes use the new slug, not `nouveau`.
- Add loading, empty, and error states for dossier fetch failures.

Acceptance:
- Create dossier creates a distinct persistent record.
- Pin survives refresh.
- Archive/delete behavior survives refresh and is named correctly.
- Switching tabs after creating a dossier stays on the created dossier.

Files likely touched:
- `src/app/dossier/[id]/page.tsx`
- `src/components/layout/Sidebar.tsx`
- `src/lib/runtime-api.ts`
- `backend/api.py`
- runtime storage/session model

## Session 5 - Document Upload And Source Ingestion

Outcome:
- Uploads become source artifacts, not local UI-only rows.

Tasks:
- Add runtime endpoint for document upload or source registration.
- Persist uploaded files in the chosen store.
- Add file type and size validation.
- Update source index and dossier facts after ingestion.
- Render ingestion status per document.
- Handle upload failure and retry.

Acceptance:
- Uploading a PDF/image creates a durable source entry.
- Refreshing the page keeps uploaded documents.
- Agent Dossier can cite uploaded source IDs.
- Invalid files produce clear UI errors.

Files likely touched:
- `src/components/shared/DropZone.tsx`
- `src/components/panels/DossierPanel.tsx`
- `src/lib/runtime-api.ts`
- `backend/api.py`
- `backend/engine/runtime.py`

## Session 6 - Agentic Runtime Maturity

Outcome:
- The project is honestly agentic, or clearly deterministic.

Decision required:
- Keep deterministic assistant for V1, or connect a real LLM-backed agent loop.

If deterministic:
- Rename/copy to avoid overclaiming.
- Keep artifact-based responses and clear limitations.
- Improve response templates and next-action routing.

If LLM-backed:
- Add provider integration behind the backend, not directly in the browser.
- Define per-agent prompts/configs.
- Add tool permissions and source citation requirements.
- Add prompt/version metadata to audit logs.
- Add timeouts, retries, budget limits, and redaction rules.
- Ensure agents cannot certify value or invent external evaluator responses.

Acceptance:
- `llm_native_agent_loop_connected` is either true with real implementation or the product copy says deterministic assistant/workbench.
- Every agent answer cites artifacts or says what is missing.
- Agent responses have tests/golden fixtures.

Files likely touched:
- `backend/api.py`
- `backend/engine/runtime.py`
- `backend/engine/skills.py`
- `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml`
- frontend panel copy

## Session 7 - Valuation, Compliance, And Professional Boundaries

Outcome:
- The product cannot accidentally present a draft as a certified appraisal.

Tasks:
- Create a compliance copy matrix for every status shown in UI.
- Review report/package generation gates.
- Add explicit source coverage indicators.
- Validate date/reference/source consistency before package generation.
- Remove mockup copy that implies OEAQ certification unless backed by real signed review.
- Add "human evaluator required" boundary in report, package, and assistant outputs.

Acceptance:
- No generated UI/report text claims certification automatically.
- Package generation is blocked when integrity or review gates fail.
- The report clearly distinguishes draft, internal review, and externally signed deliverable.

Files likely touched:
- `backend/api.py`
- `backend/engine/runtime.py`
- `src/components/panels/RapportPanel.tsx`
- `src/components/shared/RapportDoc.tsx`

## Session 8 - Frontend V1 Liquid Glass Parity

Outcome:
- Current app reaches the desired visual target from `v1-liquid-glass.html`.

Tasks:
- Align spacing, shadows, sidebar grouping, tab pill, report artifact, and report split panel with mockup.
- Polish French UI copy and accents.
- Add real behavior or hide non-functional controls such as filter.
- Standardize icons with a library or shared components.
- Add panel-level empty/error states.
- Persist report edit/save or remove edit affordance until supported.
- Keep the professional workbench feel; do not add landing-page/marketing UI.

Acceptance:
- Desktop screenshots visually match the V1 direction.
- Non-functional controls are removed or implemented.
- Copy is consistent and professional.
- Report split view is usable and saves when edit is offered.

Files likely touched:
- `src/app/globals.css`
- `src/components/layout/*`
- `src/components/panels/*`
- `src/components/shared/*`
- `src/constants/app.ts`

## Session 9 - Responsive UX And Accessibility

Outcome:
- The app works beyond a wide desktop viewport.

Tasks:
- Define breakpoints for desktop, tablet, mobile.
- Convert fixed 3-column dossier grid to responsive columns.
- Replace fixed sidebar layout with a mobile drawer or bottom navigation.
- Ensure tab bar does not overflow.
- Add focus-visible states and keyboard access.
- Add ARIA labels for icon-only buttons.
- Test text overflow with long addresses and long agent responses.

Acceptance:
- Usable at 390px, 768px, 1024px, and desktop.
- No overlapping UI.
- Keyboard users can navigate core workflows.

Files likely touched:
- `src/app/dossiers/page.tsx`
- `src/app/dossier/[id]/page.tsx`
- `src/components/layout/*`
- `src/components/shared/*`
- `src/app/globals.css`

## Session 10 - Automated QA And CI

Outcome:
- Regressions become visible before deployment.

Tasks:
- Add package scripts: `typecheck`, `lint`, `test`, `test:e2e`.
- Add backend tests using available Python tooling.
- Add API contract tests for runtime endpoints.
- Add frontend component or integration tests for core panels.
- Add Playwright E2E happy path with runtime running.
- Add visual screenshot checks for V1 Liquid Glass desktop and mobile.
- Configure GitHub Actions on canonical branch.

Acceptance:
- CI runs on PRs.
- Build, typecheck, tests, and E2E are documented.
- At least one full happy path is automated.

Files likely touched:
- `package.json`
- `.github/workflows/*`
- `backend/tests/*`
- frontend test files
- README

## Session 11 - Deployment Hardening

Outcome:
- Vercel + runtime backend deployment is repeatable.

Tasks:
- Verify Vercel project branch and env vars.
- Verify Railway backend start command and healthcheck.
- Add production env checklist.
- Add runtime token and CORS validation.
- Document deployment rollback.
- Add smoke test after deploy: frontend loads, runtime health, app state, demo create, review/package.

Acceptance:
- Fresh deployment can be reproduced from README.
- Production app does not call browser localhost.
- Runtime is not publicly writable without auth.
- `/health` and frontend build are monitored.

Files likely touched:
- `vercel.json`
- `backend/railway.json`
- `README.md`
- deployment docs

## Session 12 - Pilot Launch Checklist

Outcome:
- A controlled pilot can run without hidden assumptions.

Tasks:
- Create one realistic pilot dossier.
- Run full flow: create, attach sources, inspect facts, comparables, analysis, report, internal validation, package.
- Record all manual steps and unresolved risks.
- Capture screenshots for desktop/tablet/mobile.
- Review generated report text for professional boundaries.
- Freeze known limitations in release notes.

Acceptance:
- Pilot user can complete the workflow.
- Known limitations are documented.
- No P0/P1 issues remain open.

## Session Order Rules

Do not start visual polish before Sessions 1-4 are done, except for small copy fixes.
Do not connect an LLM before the runtime security/BFF session is done.
Do not deploy publicly before auth/security and deployment sessions are done.
Do not call the product production-ready until tests and pilot checklist pass.
