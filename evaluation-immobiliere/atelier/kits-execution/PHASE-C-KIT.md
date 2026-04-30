# PHASE C — KIT D'EXÉCUTION OPÉRATIONNEL

## Objectifs vérifiables
- Brancher un run E2E runtime réel sur dossier anonymisé.
- Produire une décision Go/No-Go de phase avec preuves.

## Entrées (repo)
- `integration/AGENTCONFIG-*.yaml`
- `outils/executer_dossiers_pilotes_reels_v0.py`

## Sorties attendues
- `atelier/RAPPORT-BRANCHEMENT-ENGINE-V1.md`
- `tests/reports/case_nominal.report.json`

## Commande de vérification principale
- `python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py`

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
- Phase C pilotée par une commande de preuve unique et des sorties minimales mesurables.
- Format uniforme pour faciliter revue croisée tech/métier/ops.

## Questions ouvertes
- Qui signe le Go/No-Go final de la phase C ? **À valider**.
- Les entrées listées couvrent-elles 100% des cas clients cibles ? **À valider**.
