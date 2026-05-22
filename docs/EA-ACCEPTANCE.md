# Acceptance dossier anonymise - eval-immo

This workflow is the final pre-production acceptance pass with an anonymized real-style appraisal dossier. It does not certify a value. It produces evidence that an evaluateur agree can review before deciding whether the system is acceptable for bureau pilot use.

## Fixture

Use a JSON case file with:

- `dossier_id`, `date_reference`, `type_bien`, `adresse_anonymisee`
- At least 3 comparable sales with `source_id`, `prix_vente`, `date_vente`
- Human-validated adjustments with `source_id` and `validation_humaine: true`
- Hypotheses tied to `source_ids`
- No direct identifiers: no personal names, email, phone, postal code, raw civic address, or owner/client identity

Reference fixture:

```bash
backend/tests/fixtures/acceptance/ea_acceptance_anonymized_residential.json
```

## Run

From `backend/`:

```bash
python scripts/run_ea_acceptance.py tests/fixtures/acceptance/ea_acceptance_anonymized_residential.json \
  --sessions-dir runtime_sessions_acceptance \
  --evaluator-id <supabase-user-id-or-reviewer-id> \
  --reviewer "Nom interne anonymise" \
  --json
```

The script runs:

1. Anonymization and dossier completeness preflight
2. Runtime pipeline in strict mode
3. Internal review validation
4. V1 package generation
5. `acceptance_ea_report.json` evidence file

## Pass Criteria

The report status must be `PASS`, with all checks true:

- `anonymization`
- `runtime_ready`
- `review_valide`
- `certifiability_gate`
- `package_ready`
- `no_external_evaluator_answers`

The generated package must keep:

- `requires_human_validation: true`
- `certification_automatic: false`
- `external_evaluator_responses_included: false`

## Evidence To Keep

For each acceptance run, retain:

- The anonymized input fixture
- `acceptance_ea_report.json`
- `session.json`
- `result.json`
- `review.json`
- `artifact_index.json`
- `package_v1/manifest_v1.json`
- `package_v1/paquet_v1.zip`

## Failure Handling

If status is `BLOCKED`, do not proceed to bureau pilot. Fix the blocking check first:

- `anonymization`: remove direct identifiers and rerun
- `runtime_ready`: inspect `result.json` blocking failures
- `certifiability_gate`: inspect gate blocking errors and missing artifacts
- `package_ready`: inspect PDF/report/package generation

## Scope Limit

This workflow proves the software path can process an anonymized appraisal dossier and produce a review package. It is not an OEAQ certification, does not replace the evaluateur agree, and must not be treated as a signed appraisal report.
