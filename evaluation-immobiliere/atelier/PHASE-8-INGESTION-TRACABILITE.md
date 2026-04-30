# Phase 8 - Ingestion PDF et tracabilite champ par champ

## Objectif

Transformer les rapports PDF anonymises en dossiers normalises auditables, sans attendre les reponses des evaluateurs.

Cette phase ne calibre pas encore les seuils metier finaux. Elle professionnalise la chaine d'entree:

- PDF anonymise source;
- texte extrait;
- fixture pilote active;
- `dossier_normalise.json`;
- `trace_champs.json`;
- rapport d'ingestion.

## Livrables ajoutes

- `mvp/DOSSIER-NORMALISE-V0.yaml`
- `outils/preparer_ingestion_pdf_v0.py`
- `tests/test_ingestion_pdf_v0.py`

## Commande sur les rapports reels

```bash
python evaluation-immobiliere/outils/preparer_ingestion_pdf_v0.py \
  --pdf C:\Users\simon\spaCy\D-REEL\anonymises\D-REEL-001.pdf \
  --pdf C:\Users\simon\spaCy\D-REEL\anonymises\D-REEL-002.pdf \
  --pdf C:\Users\simon\spaCy\D-REEL\anonymises\D-REEL-003.pdf
```

Si les textes extraits sont absents, fournir `--pdftotext-exe` avec le chemin local vers `pdftotext.exe`.

## Sorties locales ignorees par Git

- `evaluation-immobiliere/runtime_pilotes_reels/ingestion_v0/MANIFESTE-INGESTION-PDF-V0.json`
- `evaluation-immobiliere/runtime_pilotes_reels/ingestion_v0/RAPPORT-INGESTION-PDF-V0.md`
- `evaluation-immobiliere/runtime_pilotes_reels/ingestion_v0/<dossier_id>/dossier_normalise.json`
- `evaluation-immobiliere/runtime_pilotes_reels/ingestion_v0/<dossier_id>/trace_champs.json`

## Critere de passage

- Les trois rapports anonymises produisent un dossier normalise.
- Chaque dossier contient une trace de champs.
- Les champs approximes, inferes ou issus de textes masques restent marques pour revue humaine.
- Aucun chemin absolu local de PDF n'est ecrit dans les artefacts produits.
