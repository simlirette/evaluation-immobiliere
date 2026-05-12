---
name: redaction-fiches-techniques
description: >
  Rédiger les fiches techniques du bien sujet et des comparables dans un format
  standardisé pour inclusion dans le rapport d'évaluation.
type: redaction
agents:
  - data-facts
sources:
  - fiche_bien
  - documents_sources
---

## Objectif

Produire des fiches techniques claires, complètes et sourcées pour le bien sujet et chaque comparable retenu.

## Fiche technique — Bien sujet

```markdown
### BIEN SUJET — Fiche technique

| Champ | Valeur | Source |
|-------|--------|--------|
| Adresse civique | [adresse] | [source_id] |
| Lot cadastral | [matricule] | Registre foncier |
| Type de bien | [type] | Rôle municipal |
| Zonage | [code zone] | Règlement de zonage |
| Superficie terrain | [X] m² | [source_id] |
| Superficie habitable | [X] m² | [source_id] |
| Nombre d'étages | [N] | [source_id] |
| Année de construction | [AAAA] | Rôle municipal / permis |
| Valeur au rôle | [X $] (rôle [AAAA-AAAA]) | Rôle municipal |
| Propriétaire inscrit | [Nom] | Registre foncier |
| Date d'acquisition | [AAAA-MM-JJ] | Acte de vente |
| Prix d'acquisition | [X $] | Registre foncier |
| État général | [excellent / bon / moyen] | Inspection |
| Particularités | [liste] | [source_id] |
```

## Fiche technique — Comparable

```markdown
### COMPARABLE [N] — [Adresse]

| Champ | Valeur | Source |
|-------|--------|--------|
| Adresse | [adresse] | DLC / Centris |
| Source ID | [source_id] | |
| Date de vente | [AAAA-MM-JJ] | Registre foncier / DLC |
| Prix de vente | [X $] | Registre foncier |
| Prix au m² habitabl | [X $/m²] | Calculé |
| Type de bien | [type] | |
| Superficie terrain | [X] m² | |
| Superficie habitable | [X] m² | |
| Année de construction | [AAAA] | |
| État général | [état] | |
| Distance du sujet | [X km] | |
| Score de similarité | [0.0–1.0] | |
| Conditions de vente | [normales / préciser] | |
| Retenu / Rejeté | [décision] | |
| Raison | [justification] | |
```

## Règles de rédaction

- Utiliser le système métrique (m², $/m²) — jamais pi²
- Toute valeur doit être sourcée dans la colonne « Source »
- Les conditions de vente « normales » signifient : vendeur et acheteur consentants, bien informés, sans lien de dépendance, sans contrainte temporelle
- Signaler tout comparable avec conditions anormales et documenter la décision de l'inclure ou l'exclure
- Les scores de similarité sont calculés sur une échelle de 0 (aucune similarité) à 1.0 (identique)
