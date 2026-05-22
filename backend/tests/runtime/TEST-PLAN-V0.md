# TEST-PLAN-V0 — Runtime Pilot Cases

These pilot cases are JSON-compatible YAML fixtures. They are stored with a
`.yaml` extension to match the runtime test plan, but are parsed with the
standard-library JSON parser so the Railway backend image does not need a YAML
dependency.

## Scope

The plan validates the deterministic runtime pipeline from `mandat-intake`
through `redaction` using small residential fixtures. External calls and LLM
calls must not be required. Every case asserts:

- expected runtime status;
- expected blocking rule prefixes;
- required artifact files;
- absence of unhandled exceptions.

## Cases

| ID | Fixture | Purpose | Expected status |
|---|---|---|---|
| T01 | `T01_nominal_unifamiliale.yaml` | Clean unifamiliale dossier with 3 usable comparables | `PRET_REVISION_FINALE` |
| T02 | `T02_missing_source_id.yaml` | Comparable without `source_id` must block source traceability | `A_REVOIR` |
| T03 | `T03_future_sale_date.yaml` | Sale after `date_reference` must block chronology | `A_REVOIR` |
| T04 | `T04_unit_mismatch.yaml` | Subject/comparable surface units mismatch must block | `A_REVOIR` |
| T05 | `T05_sensitive_adjustment_unvalidated.yaml` | Adjustment >= 25 000 $ without human validation must block | `A_REVOIR` |

## Required Artifacts

Each successful runtime invocation must produce at least:

- `mandat-intake.conflit_interets.json`
- `data-facts.fiche_bien.json`
- `comps-market.comparables_proposes.json`
- `valuation-draft.calculs_approche_comparative.json`
- `compliance-qa.statut_sortie.json`

For blocking cases, the runtime may stop after `compliance-qa`; that behavior is
intentional.
