# Closed Beta Launch

This document is the operator path for Phases 2 through 6. It turns the remaining work into evidence that can be checked before the beta link is shared.

Do not put secrets in the evidence file. Record only URLs, booleans, non-identifying ids, and paths to generated evidence.

## 1. Production Environment

Complete the Railway, Vercel, Supabase, and source-cache setup from `DEPLOYMENT.md`.

Required evidence:

- Vercel production HTTPS URL.
- Railway backend HTTPS URL.
- Backend `/readiness` returns 200 in production.
- Vercel BFF smoke runs through the frontend URL, not directly against Railway.
- Matching runtime token exists on Vercel and Railway.
- `EVAL_RUNTIME_ALLOWED_ORIGIN` is the exact Vercel origin.
- `SESSIONS_DIR` is on persistent storage.
- `DATA_CACHE_DIR` is on persistent storage.
- MAMH cache is provisioned on the production data volume.
- OpenAI provider env is configured.

Commands:

```bash
cd backend
python scripts/check_deploy_readiness.py --production --json
python scripts/verifier_beta_ea_readiness_v1.py --strict-link
python scripts/smoke_beta_ea_link_v1.py --base-url https://<vercel-domain> --token <runtime-token> --role supervisor --require-external-ready
```

## 2. Privacy And Legal

Owner approval is required before any real client material is used.

Required evidence:

- Loi 25 data inventory approved.
- Retention period set between 1 and 90 days.
- Deletion workflow approved.
- Access logs are reviewable during beta week 1.
- Backup/restore expectations defined.
- Incident response defined.
- Professional disclaimer approved: eval-immo assists the E.A.; it does not certify value automatically.
- Raw client files remain disabled unless a specific contract is signed.

## 3. Pilot E.A.

Use one pilot E.A. first.

Required evidence:

- Non-identifying pilot E.A. id or internal user id.
- Beta terms accepted.
- Guided workflow signoff recorded.

## 4. Real Dossier Acceptance

Run three anonymized real dossiers:

- `standard_residential`
- `edge_or_low_confidence`
- `correction_or_blocked`

For each dossier, record:

- Non-identifying dossier id.
- Confirmation that the dossier is anonymized.
- Acceptance status: `PASS` or `JUSTIFIED_BLOCKED`.
- Path to package manifest or blocked-state evidence.
- `professional_workfile_gate.json` reviewed and not blocked.
- `npp_compliance_matrix.json` reviewed by the pilot E.A.
- `source_provenance.json` reviewed for traceability.
- `p0_open_count: 0`.

Use:

```bash
cd backend
python scripts/run_ea_acceptance.py <anonymized-case.json> --sessions-dir runtime_sessions_acceptance --evaluator-id <pilot-ea-id> --reviewer "<internal reviewer>" --json
```

For every package that reaches review, inspect:

```text
package_v1/professional_workfile_gate.json
package_v1/npp_compliance_matrix.json
package_v1/source_provenance.json
```

Warnings in these files can remain only if the pilot E.A. accepts them as beta
scope limitations. Blocking items must be fixed before launch.

## 5. Data Source Policy

Before launch, make these decisions explicit:

- `mamh_validated`: production MAMH cache has been validated.
- `infolot_validated`: live Infolot smoke has been run where network access is approved.
- `sirf_status`: `configured` or `explicitly_disabled_for_beta`.
- `jlr_policy`: `required`, `manual_export`, or `not_required_for_beta`.
- `cost_approach_status`: `accepted_source_available` or `explicitly_marked_incomplete`.
- `insufficient_data_blocking_policy`: weak source data has a blocking policy.

## 6. Final Launch Gate

Copy the template:

```bash
copy _audit\2026-06-02\closed_beta_launch_evidence.template.json _audit\2026-06-02\closed_beta_launch_evidence.json
```

Fill it with non-secret evidence, then run:

```bash
cd backend
python scripts/check_closed_beta_launch.py ..\_audit\2026-06-02\closed_beta_launch_evidence.json --json
```

The beta link can be shared only when the script returns:

```json
{
  "status": "READY_FOR_CLOSED_BETA",
  "ok": true
}
```

## Stop Conditions

Do not launch if any of these is true:

- Any P0 security, privacy, professional, or workflow issue is open.
- The beta evidence gate returns `BLOCKED`.
- Production `/readiness` returns non-200.
- The Vercel BFF smoke fails.
- Any real dossier contains direct identifiers.
- The pilot E.A. has not signed off on workflow usefulness.
