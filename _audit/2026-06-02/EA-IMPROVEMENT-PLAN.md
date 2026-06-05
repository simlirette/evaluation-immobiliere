# E.A. Improvement Plan - 2026-06-05

## Objective

Move eval-immo from a strong technical beta toward a defensible E.A. workfile
system. The product must help an evaluateur agree review, correct, document,
and sign professional work. It must not imply automatic certification.

## Product Principle

The product should not be framed as "AI generates an appraisal". It should be
framed as "AI assists construction of an auditable professional workfile".

## Phase EA-1 - Professional Workfile Gate

### Scope

Create a gate that checks whether a dossier has the minimum workfile evidence an
E.A. needs before package generation.

### Required Coverage

- mandate and scope details;
- intended use and report format;
- effective date;
- anonymized or controlled subject identification;
- conflict check artifact;
- source ids and source index;
- at least three sourced comparables for sales comparison;
- manual review decision before package;
- draft report availability;
- explicit non-certification limits.

### Execution

Implemented in this branch:

- `professional_workfile_gate(session, require_review=...)`
- package manifest embeds `professional_workfile_gate`
- package ZIP includes `professional_workfile_gate.json`
- review/package gates surface professional workfile blockers

## Phase EA-2 - NPP / Professional Compliance Matrix

### Scope

Produce a reportable matrix showing which professional report/workfile elements
are satisfied, missing, warning-only, or not applicable.

### Required Coverage

- mandate/scope;
- subject identification;
- effective date;
- intended use/user;
- conflict check;
- highest and best use / UMPP;
- inspection evidence;
- source provenance;
- comparable selection and exclusions;
- valuation approaches;
- assumptions and limiting conditions;
- human review/signoff.

### Execution

Implemented in this branch:

- `npp_compliance_matrix(session)`
- package manifest embeds `npp_compliance_matrix`
- package ZIP includes `npp_compliance_matrix.json`

Remaining product work:

- map the matrix to exact OEAQ/NPP clause references after legal/professional
  review;
- expose the matrix in the frontend review UI.

## Phase EA-3 - Source Provenance And Comparable Defensibility

### Scope

Every material fact and valuation conclusion must be traceable.

### Required Coverage

- source id;
- source type/name;
- source date or retrieval date;
- document path or artifact path;
- validation status;
- reason for inclusion/exclusion;
- comparable search universe, not only selected rows.

### Execution

Implemented in this branch:

- `source_provenance_report(session)`
- package manifest embeds `source_provenance`
- package ZIP includes `source_provenance.json`

Remaining product work:

- persist full comparable search universe from JLR/public-source search;
- expose exclusion reasons in UI;
- add page/section citations for uploaded documents.

## Phase EA-4 - Inspection And Physical Condition Workflow

### Scope

Support professional field inspection evidence.

### Required Coverage

- inspection date;
- inspector / E.A. id;
- photos and photo manifest;
- measurements and area evidence;
- condition notes;
- renovations;
- site improvements;
- zoning/use constraints;
- environmental or legal red flags.

### Current State

Partially supported through input timeline/hypotheses and uploads. Not yet a
dedicated E.A. inspection workflow.

### Required Execution

- add frontend inspection panel;
- add backend `inspection_evidence.json`;
- require photo/measurement manifest for real beta unless explicitly scoped out.

## Phase EA-5 - Valuation Approach Controls

### Scope

Each approach must be explicitly completed, not applicable, insufficient, or
blocked.

### Required Coverage

- sales comparison: minimum sourced comparable count and adjustment evidence;
- cost approach: accepted cost-source decision;
- income approach: rent/expense/cap-rate evidence or clear non-applicability;
- reconciliation: weights and reasons;
- no silent certifiability where a material approach is missing.

### Current State

Comparative approach has strong gates. Cost and income artifacts exist but need
stronger real-source maturity before professional reliance.

### Required Execution

- add approach applicability UI controls;
- strengthen report wording when cost/income are not applicable or insufficient;
- add beta data-source policy decisions to the launch gate.

## Phase EA-6 - Human Override And Finalization

### Scope

Separate AI draft, E.A. revision, E.A. approval, and signed export.

### Required Coverage

- every AI suggestion editable;
- changes logged with who/when/why;
- final package impossible without E.A. approval;
- signed/final state separate from draft package;
- exported report keeps non-certification watermark until final approval.

### Current State

Internal review and package gates exist. The product still needs richer
field-level override logs and a true signed/final state.

### Required Execution

- add override reason fields in UI;
- append `workfile_override_log.jsonl`;
- add finalization state after package review;
- add watermark removal only after explicit E.A. signoff.

## Phase EA-7 - Privacy And Professional Operations

### Scope

Make real client handling responsible under Quebec privacy and professional
expectations.

### Required Coverage

- data inventory;
- retention and deletion;
- access logs;
- backup/restore;
- incident response;
- named users only;
- no raw client files before contract/approval.

### Current State

Closed-beta evidence gate exists and blocks launch until these are documented.

## Definition Of Done

The project is E.A.-ready for a closed beta when:

- production readiness is green;
- closed-beta evidence gate is green;
- professional workfile gate is green for each pilot dossier;
- NPP matrix and source provenance are included in every package;
- one pilot E.A. completes three anonymized real dossiers;
- all P0 security/privacy/professional/workflow feedback is closed.
