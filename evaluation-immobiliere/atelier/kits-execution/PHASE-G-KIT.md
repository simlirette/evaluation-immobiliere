# PHASE G — KIT D'EXÉCUTION OPÉRATIONNEL

## Objectifs vérifiables
- Mesurer latence/coût/fiabilité et fixer les SLO.
- Produire une décision Go/No-Go de phase avec preuves.

## Entrées (repo)
- `outils/analyser_delta_runtime_v0.py`
- `outils/analyser_qualite_runtime_v0.py`

## Sorties attendues
- `atelier/BENCH-PERF-COUT-V1.md`
- `atelier/SLO-SLA-V1.md`

## Commande de vérification principale
- `python evaluation-immobiliere/outils/analyser_delta_runtime_v0.py`

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
- Phase G pilotée par une commande de preuve unique et des sorties minimales mesurables.
- Format uniforme pour faciliter revue croisée tech/métier/ops.

## Questions ouvertes
- Qui signe le Go/No-Go final de la phase G ? **À valider**.
- Les entrées listées couvrent-elles 100% des cas clients cibles ? **À valider**.
