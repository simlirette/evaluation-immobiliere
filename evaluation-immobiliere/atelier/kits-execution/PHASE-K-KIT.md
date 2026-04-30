# PHASE K — KIT D'EXÉCUTION OPÉRATIONNEL

## Objectifs vérifiables
- Déployer canary et stabiliser J+7.
- Produire une décision Go/No-Go de phase avec preuves.

## Entrées (repo)
- `atelier/RUNBOOK-OPERATIONS-PRE-REPONSES.md`
- `schemas/ops/ops_handoff_manifest_v0.schema.json`

## Sorties attendues
- `atelier/PLAN-DEPLOIEMENT-CANARY-V1.md`
- `atelier/RAPPORT-STABILISATION-J7.md`

## Commande de vérification principale
- `python evaluation-immobiliere/outils/ops_doctor_v0.py`

## Critères d’acceptation testables
- [ ] Sorties produites et versionnées.
- [ ] Commande de vérification exécutée sans erreur bloquante.
- [ ] Risques critiques avec owner + mitigation datée.
- [ ] Dépendances phase suivante documentées explicitement.

## Risques majeurs et mitigations
| Risque | Mitigation | Owner |
|---|---|---|
| Données insuffisantes | Utiliser fixtures + tracer écart réel/simulé | Lead Runtime |
| Ambiguïté métier | Validation conjointe Lead Métier + Product | Lead Métier |
| Régression qualité | Exécuter tests runtime/ops ciblés | QA/Platform |

## Dépendances
- Dépend des livrables validés de la phase précédente.
- Bloque le passage à la phase suivante en cas de No-Go.

## Décisions prises
- Phase K pilotée par une commande de preuve unique et des sorties minimales mesurables.
- Format uniforme pour faciliter revue croisée tech/métier/ops.

## Questions ouvertes
- Qui signe le Go/No-Go final de la phase K ? **À valider**.
- Les entrées listées couvrent-elles 100% des cas clients cibles ? **À valider**.
