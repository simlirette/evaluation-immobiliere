# Intégration — adaptation directe d'Aston

Ce dossier contient les artefacts d'adaptation **directe** de l'infrastructure Aston vers l'évaluation immobilière.
On conserve le cœur Aston et on remplace principalement les modules métier.

## Artefacts disponibles
- `AGENTCONFIG-DATA-FACTS-V0.yaml`
- `AGENTCONFIG-COMPS-MARKET-V0.yaml`
- `AGENTCONFIG-VALUATION-DRAFT-V0.yaml`
- `AGENTCONFIG-COMPLIANCE-QA-V0.yaml`
- `AGENTCONFIG-REDACTION-V0.yaml`
- `TOOL-MAPPING-ASTON-V0.md`
- `PIPELINE-RUNTIME-ASTON-V0.yaml`
- `ORCHESTRATION-CHECKLIST-V0.md`
- `AGENT-SKILLS-MATRIX.md`

## Principe d'intégration
- Garder la structure Aston (engine/orchestration/events).
- Adapter seulement les briques métier immobilières (prompts/tools/rules/outputs).
- Limiter les modifications infra au strict nécessaire.
- Declarer les skills projet par agent dans `skills_allowed`, puis les exposer via le runtime sans charger toute la connaissance dans chaque etape.

## Ordre d'intégration recommandé
1. data-facts
2. comps-market
3. valuation-draft
4. compliance-qa
5. redaction
