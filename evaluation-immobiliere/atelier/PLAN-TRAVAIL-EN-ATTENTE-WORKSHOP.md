# En attendant le workshop - plan d'execution concret

## Ce qu'on peut faire maintenant sans dependre des evaluateurs

### 1. Preparer l'ossature produit

- Definir le flux cible v1: Intake -> Data/Facts -> Comps -> Valuation Draft -> Compliance QA -> Redaction.
- Definir les entrees/sorties standard de chaque agent.
- Garder la decision finale chez l'evaluateur.

### 2. Construire le cadre qualite

- Ebaucher une checklist conformite: sections obligatoires, unites, dates, sources.
- Definir les statuts de sortie: `BROUILLON`, `A_REVOIR`, `PRET_REVISION_FINALE`.
- Distinguer les controles bloquants des warnings.

### 3. Preparer la tracabilite

- Schema de journalisation des hypotheses, sources et ajustements.
- Convention pour lier chaque conclusion a une source.
- Audit JSONL pour chaque execution runtime.

### 4. Preparer la mesure d'impact

- Baseline actuelle: temps moyen par dossier, retours qualite, retards.
- KPIs cibles v1: gain de temps, taux de corrections, completude documentaire.
- Format de reponses evaluateurs compilable.

### 5. Preparer un jeu de cas tests

- Fixtures representant des cas simples et des cas bloques.
- Gabarit de dossier anonymise.
- Simulation runtime et rapport d'integrite.

## Sorties attendues avant workshop

- Questionnaire finalise.
- Gabarit de reponses evaluateurs.
- Matrice MVP prete a compiler.
- Script de compilation reponses -> matrice -> rapport.
- Schema de donnees minimal.
- Definition des KPIs et mode de mesure.

## Commandes de preparation

```bash
python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py
python evaluation-immobiliere/outils/prioriser_mvp.py
```

## Critere ready for workshop

Toutes les questions ou les evaluateurs doivent trancher sont explicites, mesurables et rattachees a une decision produit.
