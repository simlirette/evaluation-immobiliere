# Mapping runtime vers knowledge immobilier v0

## Objectif

Preparer la convergence entre le simulateur runtime actuel et un futur moteur
type Aston avec `knowledge.json` persiste.

## Mapping principal

| Artefact runtime | Section knowledge | Usage |
|---|---|---|
| `data-facts.fiche_bien.json` | `mandate`, `subject_property`, `sources` | Donnees de base du mandat et du bien |
| `data-facts.timeline_faits.json` | `subject_property` | Evenements et dates structurantes |
| `*.source_index.json` | `sources` | Index de tracabilite |
| `comps-market.comparables_proposes.json` | `market_evidence` | Comparables retenus et scores |
| `comps-market.justifications_comparables.json` | `market_evidence` | Decisions de selection/exclusion |
| `valuation-draft.calculs_*.json` | `valuation`, `reconciliation` | Calculs deterministes et traces |
| `valuation-draft.hypotheses_explicites.json` | `valuation` | Hypotheses a valider |
| `compliance-qa.*` | `compliance`, `human_review` | Gate QA, recommandations, statut |
| `redaction.*.md` | `redaction` | Brouillon et annexe |
| `runtime_manifest.json` | `audit` | Fingerprint de la sortie |
| `calibration_evaluateurs.json` | `human_review` | Decisions evaluateurs compilees |

## Regles d'integration

- `knowledge.json` ne doit jamais remplacer les artefacts sources; il les
  reference.
- Toute valeur numerique de `knowledge.json` doit garder un lien vers son
  artefact source.
- Les calculs restent executes par Python deterministe, pas par texte libre.
- Les decisions evaluateurs deviennent des entrees `human_review`, pas des
  corrections automatiques.

## Done pour integration Aston

- Une session peut reconstruire `knowledge.json` depuis les artefacts runtime.
- Chaque agent lit seulement son profil.
- Le stream expose les mises a jour de sections.
- Le manifest runtime reference le fingerprint de la knowledge base.

