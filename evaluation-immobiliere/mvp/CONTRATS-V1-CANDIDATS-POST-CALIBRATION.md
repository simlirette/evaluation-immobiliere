# Contrats v1 candidats apres calibration

## Principe

Aucun seuil n'est modifie avant reponse evaluateur. Ce document liste les zones
ou une reponse peut declencher une modification v1.

## Matrice decision -> action

| Signal evaluateur | Zone contrat | Action candidate | Test requis |
|---|---|---|---|
| Blocage `CONF005` juge trop strict | `date_vente_max_delta_days` | Assouplir la fenetre temporelle ou ajouter exception documentee | Cas comparable ancien accepte |
| Blocage `CONF005` confirme | `date_vente_max_delta_days` | Conserver et documenter comme hard gate | Cas comparable ancien bloque |
| Warning `W001` juge bloquant | `confidence_min_warning` | Ajouter seuil bloquant ou statut `A_REVOIR` | Cas faible confiance bloque |
| Warning `W001` juge acceptable | `confidence_min_warning` | Conserver statut `BROUILLON` | Cas faible confiance reste brouillon |
| Warning `W002` juge bloquant | `max_comparable_distance_km_warning` | Ajouter seuil hard pour distance | Comparable eloigne bloque |
| Redaction manquante sur `A_REVOIR` jugee bloquante | Pipeline redaction | Generer brouillon limite meme en revue | Cas A_REVOIR avec brouillon limite |
| Score comparable mal classe | `SCORING-COMPARABLES-V0.yaml` | Ajuster poids ou penalites | Ordre attendu des comparables |
| Trace champ insuffisante | `TRACEABILITY-SPEC.md` | Ajouter champs source ou review_status | Trace incomplete detectee |

## Regle de changement

Chaque changement v1 doit avoir:

- une reponse evaluateur source;
- un item `BACKLOG-V1.md`;
- un test de regression;
- une regeneration du runtime reel;
- une mise a jour du rapport qualite.

