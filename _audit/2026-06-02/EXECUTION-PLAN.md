# eval-immo execution plan - 2026-06-02

## Scope

This plan converts the June 2 audit into executable work. It targets the current
repository state on `origin/main`, not the older nested `evaluation-immobiliere/`
runtime worktree.

The goal is not only to make the code pass tests. The goal is to make the
project usable by an evaluateur agree in a closed beta, with clear professional
limits, production-grade deployment controls, and evidence that the workflow
works on anonymized real dossiers.

## Current Verified Baseline

- Current repo source of truth: `origin/main` at `532b5b0`.
- Local stale worktree: `main` is ahead 93 and behind 299 versus `origin/main`.
- Frontend typecheck: pass.
- Frontend lint: pass with 2 warnings before this plan execution.
- Frontend tests: 1188 passed.
- Frontend production build: pass, with Next.js workspace-root and deprecated
  `middleware` warnings before this plan execution.
- Backend tests: 961 passed, 3 skipped.
- Anonymized E.A. acceptance fixture: pass.
- Beta E.A. external link: blocked.
- npm audit before this plan execution: 5 advisories, including 2 critical and
  1 high.

## Non-Negotiable Product Boundaries

- eval-immo is an assistant and workbench, not an automatic certified appraisal.
- Every dossier must remain human-in-the-loop.
- A report is not final until reviewed and signed by an E.A.
- No raw client dossier can be accepted for external beta without anonymization,
  retention, and access-control policy.
- Any proxy or incomplete valuation approach must remain visibly marked in
  artifacts and UI until backed by accepted source data.

## Phase 0 - Source Of Truth And Repo Hygiene

### Objective

Make the current repo state unambiguous so future work is not done on stale code.

### Tasks

1. Treat `origin/main` as canonical.
2. Keep the stale local `evaluation-immobiliere/` runtime read-only until any
   unique files are explicitly reconciled.
3. Update README and project docs so they describe the current Next.js plus
   Python backend architecture.
4. Document this execution plan under `_audit/2026-06-02/`.
5. Keep all generated runtime sessions, local virtual environments, `node_modules`,
   and build outputs out of git.

### Done Criteria

- README no longer claims missing BFF/auth/persistence items that are already
  implemented.
- A collaborator can tell which branch/tree to use within 60 seconds.
- `git status` is clean except intentional plan/code changes.

## Phase 1 - Build, Dependency, And CI Hardening

### Objective

Remove known build hygiene warnings and prevent high-risk dependency drift from
reaching beta.

### Tasks

1. Upgrade vulnerable frontend dependencies.
   - Patch Next.js to a fixed 16.2.x release.
   - Upgrade Vitest and `@vitest/coverage-v8` to the secure major if tests pass.
   - Re-run `npm audit`.
2. Migrate Next.js `middleware` file convention to `proxy`.
   - Rename `src/middleware.ts` to `src/proxy.ts`.
   - Rename exported function `middleware` to `proxy`.
3. Pin Turbopack project root.
   - Set `nextConfig.turbopack.root` to the repo root.
   - Eliminate workspace root inference from parent lockfiles.
4. Fix current lint warnings.
5. Add an audit gate to CI once dependency upgrades are stable.

### Done Criteria

- `npm run typecheck` passes.
- `npm run lint` passes with zero warnings if possible.
- `npm test` passes.
- `npm run build` passes without the workspace-root or middleware warnings.
- `npm audit` reports no high or critical advisories, or documented exceptions
  are justified in this file.

## Phase 2 - Production Deployment Readiness

### Objective

Move from local demo readiness to deployable closed beta infrastructure.

### Tasks

1. Railway backend:
   - Set `APP_ENV=production`.
   - Set `EVAL_RUNTIME_API_TOKEN`.
   - Set `EVAL_RUNTIME_ALLOWED_ORIGIN` to the exact Vercel URL.
   - Set `OPENAI_API_KEY` and selected model env.
   - Set `SESSIONS_DIR=/data/sessions`.
   - Set `DATA_CACHE_DIR=/data/data_cache`.
   - Mount persistent volume(s).
2. Vercel frontend:
   - Set `RUNTIME_API_URL` to Railway HTTPS URL.
   - Set `RUNTIME_API_TOKEN` to match Railway backend token.
   - Set Supabase public env values.
3. Supabase:
   - Apply migrations 002, 003, 004 to production.
   - Confirm `profiles.role` supports `bureau_admin` and `evaluateur`.
   - Confirm service-role invite flow is available server-side only.
4. Public data cache:
   - Run `scripts/provision_mamh_cache.py --all` against the production cache
     volume.
   - Confirm SIRF credentials or explicitly mark SIRF unavailable for the beta.
5. Run deployment checks:
   - `python scripts/check_deploy_readiness.py --json`
   - `python scripts/verifier_beta_ea_readiness_v1.py`
   - deployed smoke through Vercel BFF, not direct browser calls to Railway.

### Done Criteria

- Backend `/readiness` returns 200 in production.
- Beta readiness no longer reports `BETA_LIEN_BLOQUE`.
- Runtime is not exposed without token.
- CORS is not wildcard in production.
- Sessions survive redeploy.

## Phase 3 - Security, Privacy, And Legal Closure

### Objective

Close the gap between technical beta and responsible client handling.

### Tasks

1. Finalize Loi 25 data inventory.
2. Finalize retention policy:
   - default retention period;
   - deletion workflow;
   - who can request deletion;
   - what evidence is retained.
3. Centralize or harden access logs.
4. Define backup and restore expectations for runtime sessions.
5. Define incident response for leaked dossier, wrong access, or bad generated
   report.
6. Confirm that E.A. professional responsibility wording is accepted by legal
   and by the pilot E.A.

### Done Criteria

- Written privacy and retention policy is approved for the beta.
- Anonymized beta terms match actual implementation.
- Access logs are reviewable and not silently lost on deploy.

## Phase 4 - E.A. Workflow Validation

### Objective

Prove that an E.A. can actually use the product without developer assistance.

### Tasks

1. Recruit one pilot E.A.
2. Run one guided session on the anonymized acceptance fixture.
3. Run three anonymized real dossiers:
   - residential standard;
   - low-confidence or edge case;
   - dossier with corrections/blocked compliance.
4. Observe and record:
   - confusion points;
   - missing wording;
   - upload and checkpoint friction;
   - comparable selection trust;
   - adjustment override trust;
   - report editing friction;
   - export/package issues.
5. Convert feedback into P0/P1/P2 tickets.

### Done Criteria

- 3 anonymized real dossiers reach package generation or a justified blocked
  state.
- The E.A. signs off that the workflow is useful for a closed pilot.
- All P0 feedback is fixed before wider beta.

## Phase 5 - Valuation And Data Source Maturity

### Objective

Reduce professional risk from weak source data and incomplete valuation inputs.

### Tasks

1. Validate MAMH/Infolot/SIRF cache behavior on production infrastructure.
2. Document when JLR export/API is required versus public-source fallback.
3. Keep Altus/Marshall Swift as a hard gap until actual tables or accepted
   cost sources are available.
4. Ensure every report artifact labels:
   - source provenance;
   - insufficient data;
   - proxy/partial approaches;
   - required human review.
5. Add regression cases for:
   - no usable comparable;
   - fewer than 3 usable comparables;
   - missing cost data;
   - missing income data;
   - source conflict;
   - future sale;
   - PII leak attempt.

### Done Criteria

- No generated report can silently imply certifiability where data is missing.
- E.A. can trace each material value to source inputs.

## Phase 6 - Closed Beta Launch

### Objective

Launch a controlled beta with one bureau or one E.A. while keeping blast radius
small.

### Tasks

1. Share beta link only after Phase 2 and 3 are closed.
2. Limit access to named users.
3. Run daily review of access logs and session errors during beta week 1.
4. Track:
   - time per dossier;
   - blocking failures;
   - corrections by E.A.;
   - report export defects;
   - LLM cost;
   - support requests.
5. Hold a beta retrospective and decide:
   - continue beta;
   - pause and remediate;
   - expand to another E.A.

### Done Criteria

- No P0 security/privacy/professional issue remains open.
- At least one E.A. completes the workflow end-to-end on real anonymized work.
- Product owner has evidence for next commercial decision.

## Execution Started In This Branch

Branch: `codex/audit-execution-plan-2026-06-02`

Initial execution slice:

- Add this plan.
- Align README with current repo state.
- Migrate Next.js proxy convention.
- Configure Turbopack root.
- Fix current lint warnings.
- Upgrade vulnerable frontend dependencies if tests remain green.

Completed in this branch:

- README replaced with the current source of truth for BFF, runtime, auth
  scaffolding, environment variables, verification commands, and beta blockers.
- `src/middleware.ts` migrated to `src/proxy.ts` and exported as `proxy`.
- `next.config.ts` now sets `turbopack.root` to the repo root.
- JSX lint warnings in `src/app/admin/inviter/page.tsx` and
  `src/components/panels/AnalysePanel.tsx` were removed.
- Next.js upgraded from `16.2.4` to `16.2.7`.
- Vitest upgraded from `3.2.4` to `4.1.8`.
- `@vitest/coverage-v8` upgraded from `3.2.4` to `4.1.8`.
- `eslint-config-next` upgraded from `16.2.4` to `16.2.7`.
- npm overrides were added for patched transitive `postcss` and `ws`.
- CI now runs `npm audit --audit-level=high` after `npm ci`.

Verification after execution:

- `npm audit --audit-level=high`: pass, zero vulnerabilities reported.
- `npm run typecheck`: pass.
- `npm run lint`: pass with no warnings.
- `npm test`: pass, 140 files and 1188 tests.
- `npm run build`: pass on Next.js `16.2.7`; previous workspace-root and
  middleware-convention warnings are gone.
- `python -m pytest tests/ -q` from `backend/`: pass, 961 passed and 3 skipped.

Remaining blockers after this local execution slice:

- Phase 2 cannot close locally without real Railway/Vercel/Supabase values,
  production runtime token, strict allowed origin, persistent volumes, public
  data cache provisioning, and OpenAI configuration.
- Phase 3 cannot close without owner-approved privacy, retention, logging,
  backup/restore, incident response, and professional responsibility wording.
- Phase 4 cannot close without one pilot E.A. and three anonymized real dossiers.
- Phase 5 cannot close without real source-data validation and cost/source
  maturity decisions.
- Phase 6 must wait until Phases 2, 3, and E.A. validation are closed.

## Execution Continued On 2026-06-05

Added local execution support for the remaining phases:

- Added `docs/CLOSED-BETA-LAUNCH.md` as the operator checklist for Phases 2
  through 6.
- Added `_audit/2026-06-02/closed_beta_launch_evidence.template.json` as the
  non-secret evidence template for production, privacy, pilot E.A., real
  dossiers, data-source policy, and launch controls.
- Added `backend/scripts/check_closed_beta_launch.py`; it returns non-zero until
  the evidence file proves the closed-beta launch criteria are complete.
- Added backend tests for the closed-beta launch evidence gate.
- Updated `backend/integration/BETA-EA-RUNBOOK-V1.md` to current repo paths and
  current scripts.
- Linked the closed-beta gate from `README.md` and `DEPLOYMENT.md`.

This does not close Phases 2 through 6 by itself. It makes them enforceable.
The remaining work still requires real hosted URLs, dashboard secrets, privacy
approval, pilot E.A. signoff, three anonymized real dossiers, and explicit
data-source decisions.

## Execution Continued For E.A. Improvements On 2026-06-05

Added the E.A.-operator improvement layer:

- Added `_audit/2026-06-02/EA-IMPROVEMENT-PLAN.md`, covering professional
  workfile readiness, NPP/compliance matrix, source provenance, inspection
  workflow, valuation approach controls, human override/finalization, privacy,
  and beta operations.
- Added `professional_workfile_gate(session, require_review=...)` in
  `backend/api.py`.
- Added `npp_compliance_matrix(session)` in `backend/api.py`.
- Added `source_provenance_report(session)` in `backend/api.py`.
- Extended `certifiability_gate` so core professional workfile blockers can
  stop review/package generation.
- Extended package generation so every V1 package can include:
  - `professional_workfile_gate.json`
  - `npp_compliance_matrix.json`
  - `source_provenance.json`
- Updated E.A. acceptance and beta launch docs to require review of those
  artifacts.

Covered immediately:

- mandate/scope minimum evidence;
- effective date;
- subject identification;
- conflict check;
- source provenance;
- sourced comparable minimum;
- comparable selection documentation;
- comparative approach traceability;
- adjustment human validation;
- report draft and human review gates.

Tracked as explicit warnings / later product phases:

- full inspection UI and photo/measurement manifest;
- exact OEAQ/NPP clause mapping after professional/legal review;
- full comparable search universe and exclusion UI;
- cost/income data source maturity;
- field-level override reason log;
- signed/final report state separate from draft package.
