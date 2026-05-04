# SPEC UI EVALUATEUR V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Définir et démarrer l'interface évaluateur Phase E pour traiter la file de revue humaine, ouvrir un dossier, inspecter les artefacts, tracer la décision et préparer la validation finale.

## Statut Phase E
Décision actuelle: **GO CONDITIONNEL**.

Mise a jour produit: l'interface devient une revue dossier exploitable avant
revue externe finale. Elle consomme `/session/summary` pour l'etat consolide et
`/review/dossier` pour la synthese metier, puis `/artifact` pour lire les
artefacts JSON/Markdown indexes dans la session.

Une première UI exploitable est disponible:
- fichier: `evaluation-immobiliere/ui/evaluateur_review.html`;
- routes: `/review/ui`, `/evaluateur`, `/evaluateur/revue`;
- source file de revue: `/ops/review_queue`;
- source fixtures: `/fixtures`;
- ouverture dossier: `/start`;
- intégrité et artefacts: `/status`, `/artifacts`;
- décision humaine: `/review`;
- reprise: `/resume`.

## Écrans et zones
| Zone | Données | Action |
|---|---|---|
| File | Items `FILE-REVUE-HUMAINE-V0.csv` via `/ops/review_queue` | Sélection item P1/P2/P3 |
| Session | `session_id`, `dossier_id`, `status` | Ouvrir le dossier lié à la fixture |
| Artefacts | `artifact_index_v1` avec bytes et SHA-256 | Vérifier présence et traçabilité |
| Décision | `decision`, `reviewer`, `notes` | Enregistrer `review.json` |
| Événements | Stream SSE `/stream` | Lire le déroulé runtime |
| Reprise | Résultat `/resume` | Vérifier `RESUME_READY` |

## Workflow UI
1. Charger la file de revue.
2. Sélectionner un item prioritaire.
3. Ouvrir le dossier lié au `dossier_id`.
4. Inspecter statut, événements et artefacts.
5. Enregistrer une décision humaine.
6. Lancer la reprise pour prouver l'intégrité persistée.

## États de workflow
| État | Sens |
|---|---|
| `PRET_REVUE` | Dossier prêt pour revue évaluateur |
| `A_CORRIGER` | Correction requise avant validation |
| `VALIDE` | Validation humaine effectuée |
| `REJETE` | Dossier rejeté ou non exploitable |

## Résultat de preuve
La commande Phase E a généré la file de revue:
- items: 16;
- P1: 3;
- P2: 5;
- P3: 8.

## Limites restantes
- L'UI démarre une session depuis fixture; elle ne récupère pas encore une session existante issue d'un run long réel.
- Les décisions sont persistées par session, pas encore consolidées dans une campagne multi-évaluateurs.
- Les artefacts sont listés, mais leur visualisation métier détaillée reste à spécialiser par type.
- L'authentification et les rôles évaluateur/reviewer ne sont pas encore actifs.

## Critères de suite
- Ajouter une vue détaillée comparables/approches/conformité par artefact.
- Relier les décisions UI à `REPONSES-EVALUATEURS.csv` ou à un registre de campagne.
- Bloquer `VALIDE` si les notes obligatoires ou la justification d'override sont absentes.
