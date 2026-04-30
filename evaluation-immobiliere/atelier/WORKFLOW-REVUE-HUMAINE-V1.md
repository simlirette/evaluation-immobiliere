# WORKFLOW REVUE HUMAINE V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Formaliser le workflow Phase E de revue humaine afin que chaque décision évaluateur soit traçable, justifiée et reliée aux artefacts runtime.

## Entrée de workflow
La file de revue humaine est générée par:
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/generer_file_revue_humaine_v0.py
```

Résultat:
- `FILE-REVUE-HUMAINE-V0.csv`;
- `FILE-REVUE-HUMAINE-V0.md`;
- 16 items: 3 P1, 5 P2, 8 P3.

## Priorités
| Priorité | Traitement | SLA cible |
|---|---|---|
| P1 | Blocage, contrat ou conformité critique | Avant toute validation |
| P2 | Warning, artefact manquant ou risque métier significatif | Avant livraison |
| P3 | Confirmation statut, flags mineurs, contrôle documentaire | Avant clôture campagne |

## Décisions possibles
| Décision | Effet |
|---|---|
| `PRET_REVUE` | Le dossier peut être travaillé par un évaluateur |
| `A_CORRIGER` | Une correction est requise avant validation |
| `VALIDE` | L'évaluateur confirme la sortie |
| `REJETE` | Le dossier ou la sortie n'est pas acceptable |

## Règles de justification
- Toute décision `A_CORRIGER` ou `REJETE` doit référencer l'item de revue concerné.
- Toute validation d'un dossier avec warning doit expliquer pourquoi le warning ne bloque pas.
- Tout assouplissement d'un blocage P1 doit être validé par Lead Métier.
- Toute décision doit conserver `session_id`, `run_id`, `reviewer`, `decision`, `notes`, `created_at_utc`.

## Parcours nominal
1. Générer la file de revue.
2. Sélectionner les P1 en premier.
3. Ouvrir le dossier dans `/review/ui`.
4. Lire le statut runtime, les événements et l'index d'artefacts.
5. Enregistrer la décision via `/review`.
6. Lancer `/resume` pour vérifier que la session reste reprenable.
7. Consolider les décisions dans la campagne évaluateurs.

## Conditions de blocage
| Condition | Décision recommandée |
|---|---|
| Artefact critique absent hors stop compliance attendu | `A_CORRIGER` |
| `RESUME_BLOCKED` | `A_CORRIGER` |
| P1 non tranché | Interdire `VALIDE` |
| Source ou provenance non vérifiable | `A_CORRIGER` |
| Écart IA/évaluateur non documenté | `PRET_REVUE` au maximum |

## Go/No-Go Phase E
Décision actuelle: **GO CONDITIONNEL**.

Critères satisfaits:
- file de revue générée;
- UI de revue disponible;
- décision humaine persistée par session;
- reprise vérifiée depuis l'UI/API.

Conditions avant Go final:
- consolidation multi-évaluateurs;
- justification obligatoire côté API;
- vues métier spécialisées comparables/approches/conformité;
- authentification et séparation des rôles.
