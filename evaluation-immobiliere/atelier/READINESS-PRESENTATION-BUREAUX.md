# READINESS PRÉSENTATION BUREAUX D’ÉVALUATEURS

## Objectif
Disposer d’une checklist factuelle “présentable client” avec preuves minimales exigées avant démonstration commerciale/professionnelle.

## Checklist de readiness (Go/No-Go)

### 1) Crédibilité métier
- [ ] 3 dossiers pilotes représentatifs avec comparaison IA vs évaluateur.
- [ ] Écarts documentés et justifiés (pas seulement “pass/fail”).
- [ ] Critères d’acceptation métier signés.

### 2) Traçabilité et auditabilité
- [ ] Chaque conclusion du rapport est rattachée à une source.
- [ ] Audit runtime (JSONL) disponible pour les dossiers montrés.
- [ ] Historique des corrections humaines conservé.

### 3) Qualité technique
- [ ] Tests runtime/API/ops pass sur baseline.
- [ ] Aucun échec bloquant de contrat/schéma.
- [ ] Démonstration session/start/stream fonctionnelle.

### 4) Conformité et sécurité minimale
- [ ] Contrôle accès (RBAC minimal) défini.
- [ ] Secrets et données sensibles gérés hors repo.
- [ ] Politique de rétention et journal d’accès définies.

### 5) Exploitation opérationnelle
- [ ] Runbook incident et rollback disponibles.
- [ ] Point de contact hypercare défini.
- [ ] Plan de montée en charge progressive décrit.

## Preuves minimales à apporter en réunion
- Rapport pilote runtime.
- Extraits audit/source_index.
- Résultats tests de non-régression.
- Matrice risques + mitigations + owners.
- Décision Go/No-Go consolidée.

## Mapping risques → mitigations → owner
| Criticité | Risque | Mitigation | Owner |
|---|---|---|---|
| Critique | Valeur non défendable | Revue humaine obligatoire + justification | Lead Métier |
| Critique | Donnée sensible exposée | Secrets manager + anonymisation + contrôle accès | SecOps |
| Majeure | Non reproductibilité runtime | Fixtures versionnées + tests de cohérence | Lead Runtime |
| Majeure | Rejet évaluateurs | Calibration terrain + boucle feedback | Product + Métier |

## Décisions prises
- Exiger une preuve objective par axe (métier/tech/sécu/ops) avant toute présentation bureau.
- Utiliser le même vocabulaire que le plan directeur (runtime, scoring, homologation, hypercare).

## Questions ouvertes
- Quel niveau de détail sécurité peut être partagé selon type de client? **À valider**.
- Faut-il inclure une démonstration live ou uniquement un dossier rejoué? **À valider**.
