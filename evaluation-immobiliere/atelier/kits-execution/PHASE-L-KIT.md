# PHASE L — KIT D'EXÉCUTION OPÉRATIONNEL

## Objectifs vérifiables
- Piloter hypercare et backlog v2.
- Produire une décision Go/No-Go de phase avec preuves.

## Entrées (repo)
- `atelier/RAPPORT-VALIDATION-REPONSES.md`
- `tests/reports/summary.md`

## Sorties attendues
- `atelier/PLAN-HYPERCARE-V1.md`
- `atelier/BACKLOG-AMELIORATION-V2.md`

## Commande de vérification principale
- `python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py`

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
- Phase L pilotée par une commande de preuve unique et des sorties minimales mesurables.
- Format uniforme pour faciliter revue croisée tech/métier/ops.

## Questions ouvertes
- Qui signe le Go/No-Go final de la phase L ? **À valider**.
- Les entrées listées couvrent-elles 100% des cas clients cibles ? **À valider**.
