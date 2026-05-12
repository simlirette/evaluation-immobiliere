---
name: redaction-rapport-conformite
description: >
  Rédiger le rapport de non-conformités et le mémo de recommandations correctives
  à l'intention de l'évaluateur pour corriger les défauts identifiés.
type: redaction
agents:
  - compliance-qa
sources:
  - rapport_non_conformites
  - statut_sortie
  - normes_oeaq
---

## Objectif

Produire un rapport de conformité clair et un mémo de corrections actionnable que l'évaluateur peut utiliser pour finaliser son dossier.

## Structure du rapport de non-conformités

```markdown
# Rapport de conformité — Dossier [ID]
**Date :** [date]
**Statut :** [PRET_REVISION_FINALE / BROUILLON / A_REVOIR]

---

## Résumé exécutif

[1–2 phrases sur le statut global et les points les plus critiques]

---

## Blocages (corrections obligatoires avant signature)

[Si aucun : "Aucun blocage identifié."]

### B002 — [Comparable sans source_id]
- **Impact :** Ce comparable ne peut pas être retenu sans traçabilité de la source.
- **Action requise :** Identifier la source de la vente (DLC, Registre foncier, Centris) et ajouter le `source_id`.
- **Délai :** Avant émission du rapport.

---

## Avertissements (corrections recommandées)

[Si aucun : "Aucun avertissement."]

### W003 — [Hypothèse non corroborée]
- **Impact :** La fiabilité de cette hypothèse repose sur une seule source.
- **Recommandation :** Identifier une deuxième source ou modifier le statut de l'hypothèse en "opinion professionnelle".

---

## Éléments conformes ✓

- Données essentielles du dossier : ✓ présentes
- Cohérence temporelle des comparables : ✓ vérifiée
- Unités de mesure : ✓ homogènes (m²)
- Nombre de comparables : ✓ [N] retenus
```

## Mémo de recommandations correctives

Format concis pour l'évaluateur :

```markdown
# Mémo corrections — Dossier [ID]

**Priorité 1 — Bloquant (avant signature) :**
1. [ ] Ajouter source_id pour comparable [adresse] — rechercher acte au Registre foncier
2. [ ] Documenter validation humaine pour ajustement X de [montant $]

**Priorité 2 — Recommandé (qualité du rapport) :**
3. [ ] Rechercher une deuxième source pour l'hypothèse sur [sujet]
4. [ ] Justifier l'utilisation du comparable de [ville] (W002 — distance > 30 km)

**Prochaines étapes :**
1. Corriger les blocages ci-dessus
2. Relancer la validation de conformité
3. Si statut devient PRET_REVISION_FINALE → soumettre à l'évaluateur pour signature
```

## Tonalité et style

- Objectif, factuel, non accusatoire
- Chaque non-conformité doit avoir : description, impact, action corrective
- Éviter le jargon technique — l'évaluateur doit comprendre sans consulter les codes
- Ordonner les corrections par priorité décroissante (bloquants en premier)
- Indiquer si des corrections sont optionnelles vs obligatoires
