# PHASE B — KIT D'EXÉCUTION OPÉRATIONNEL

## Objectifs vérifiables
- Versionner les contrats Aston exécutables et erreurs/retry.
- Produire une décision Go/No-Go de phase avec preuves.

## Entrées (repo)
- `mvp/CONTRATS-DONNEES-V0.yaml`
- `mvp/AGENT-CONTRACTS-V0.yaml`
- `schemas/ops/*.json`

## Sorties attendues
- `atelier/CONTRATS-INTEGRATION-ASTON-V1.yaml`
- `atelier/MATRICE-ERREURS-RETRY-V1.md`

## Commande de vérification principale
- `python evaluation-immobiliere/outils/valider_contrats_runtime_v0.py`

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
- Phase B pilotée par une commande de preuve unique et des sorties minimales mesurables.
- Format uniforme pour faciliter revue croisée tech/métier/ops.

## Questions ouvertes
- Qui signe le Go/No-Go final de la phase B ? **À valider**.
- Les entrées listées couvrent-elles 100% des cas clients cibles ? **À valider**.
