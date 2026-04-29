# Guide de compilation des reponses evaluateurs

Objectif: transformer les reponses terrain en matrice priorisee sans refaire le travail a la main.

## Fichiers

- `QUESTIONNAIRE-EVALUATEURS.md`: questions qualitatives pour preparer ou animer le workshop.
- `REPONSES-EVALUATEURS-TEMPLATE.csv`: gabarit a dupliquer par evaluateur.
- `REPONSES-EVALUATEURS.csv`: fichier consolide a remplir avec toutes les lignes de reponses.
- `RAPPORT-VALIDATION-REPONSES.md`: rapport genere des erreurs/warnings avant compilation.
- `MATRICE-PRIORISATION-MVP.csv`: matrice compilee et scoree.
- `MATRICE-PRIORISATION-MVP.md`: rapport humain genere.

## Remplissage attendu

Chaque ligne represente l'avis d'un evaluateur pour une tache.

Colonnes importantes:

- `respondant_id`: identifiant anonymise, ex. `EVAL-001`.
- `role`: senior, intermediaire, conformite, direction, etc.
- `segment`: residentiel, commercial, agricole, mixte.
- `phase`: `intake`, `data_facts`, `comps_market`, `valuation_draft`, `compliance_qa`, `redaction`.
- `tache`: nom stable de la tache.
- `temps_moyen_min`: temps moyen par dossier.
- `frequence_par_mois`: volume mensuel approximatif.
- `douleur_1_5`: friction ressentie.
- `risque_conformite_1_5`: impact si erreur.
- `automatisation_potentielle_1_5`: potentiel d'assistance IA.
- `complexite_technique_1_5`: difficulte estimee.
- `disponibilite_donnees_1_5`: facilite d'acces aux donnees.
- `validation_humaine_obligatoire`: `oui` ou `non`.
- `decision_non_delegable`: `oui` ou `non`.

## Compiler

```bash
python evaluation-immobiliere/outils/valider_reponses_evaluateurs.py
python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py
python evaluation-immobiliere/outils/prioriser_mvp.py
```

Le validateur:

- confirme que les colonnes attendues sont presentes;
- bloque les scores hors plage, les booleens invalides et les phases incoherentes;
- detecte les doublons `respondant_id` + `tache`;
- tolere un fichier vide ou des lignes gabarit non remplies.

Le compilateur:

- moyenne les champs numeriques par tache;
- conserve les commentaires uniques;
- applique la majorite pour les champs oui/non;
- calcule `valeur_score`, `readiness_score` et `score_mvp`;
- regenere le rapport Markdown.

## Decision produit

La matrice sert a identifier les meilleurs candidats MVP, mais ne remplace pas la decision finale. Une tache avec `decision_non_delegable=oui` peut rester prioritaire si le produit vise l'assistance, la verification ou la preparation du brouillon.
