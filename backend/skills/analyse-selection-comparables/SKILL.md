---
name: analyse-selection-comparables
description: >
  Sélectionner les comparables les plus pertinents pour une évaluation donnée
  en appliquant des critères rigoureux de similarité, proximité et récence.
type: analyse
agents:
  - comps-market
sources:
  - dlc_donnees_marche
  - centris_mls
  - gestim_plus
  - registre_foncier
---

## Objectif

Constituer un corpus de comparables de qualité qui supportera les conclusions de valeur de l'évaluateur.

## Critères de sélection — Hiérarchie

### Niveau 1 — Critères éliminatoires (un seul critère défaillant = exclusion)

1. **Type de bien identique** : unifamiliale avec unifamiliale, condo avec condo, etc.
   - Exception : conversion ou démolition-reconstruction possible si AMU le justifie
2. **Conditions de vente normales** : pas de vente de liquidation, pas de succession forcée, pas de lien de dépendance confirmé
3. **Source vérifiable** : chaque comparable doit avoir un source_id traçable (acte de vente au Registre foncier ou source commerciale reconnue)

### Niveau 2 — Critères de pondération

| Critère | Score optimal | Pénalité |
|---------|------------|---------|
| Superficie ±10% | 1.0 | -0.1 par tranche de 5% supplémentaire |
| Âge ±5 ans | 1.0 | -0.05 par an supplémentaire |
| Distance < 1 km | 1.0 | -0.05 par km supplémentaire |
| Vente < 6 mois | 1.0 | -0.1 par 3 mois supplémentaires |
| Même quartier | 1.0 | -0.2 si secteur différent |

Score de similarité global = moyenne pondérée des critères (0.0 à 1.0).

**Seuil de rétention :** score ≥ 0.55 pour être retenu comme comparable.

### Niveau 3 — Jugement professionnel

Même avec un bon score, l'évaluateur peut :
- Exclure un comparable pour une raison documentée (micromarché différent, condition atypique non apparente dans les données)
- Retenir un comparable de score plus faible si aucune meilleure vente disponible, avec justification écrite

## Procédure d'analyse

### Étape 1 — Recherche initiale large

Critères de recherche :
```
type_bien = sujet
rayon = 2 km (élargir si < 5 résultats)
période = 24 mois (élargir à 36 si nécessaire)
superficie_min = sujet × 0.70
superficie_max = sujet × 1.30
```

### Étape 2 — Filtrage et scoring

Pour chaque candidat :
1. Calculer score de similarité
2. Vérifier conditions de vente (recherche Registre foncier si doute)
3. Identifier les ventes entre parties liées (mêmes noms, prix aberrant)
4. Documenter la décision : retenu / rejeté + raison

### Étape 3 — Contrôle final

- Minimum 3 comparables retenus (résidentiel)
- Si corpus < 3 : élargir le rayon géographique ou la fenêtre temporelle ET documenter
- Les 3 comparables retenus ne doivent pas tous dater de la même période (éviter le biais temporel)
- Vérifier que les comparables couvrent différents niveaux de prix (pour évaluer la fourchette)

## Signaux d'alerte

- **Prix aberrant** (> 2 écarts-types de la moyenne du secteur) : vérifier l'acte au Registre foncier
- **Vente très rapide** (DOM < 10 jours) : possible vente forcée ou entre parties liées
- **Prix significativement supérieur au rôle** (> 150%) : vérifier si rénovations majeures
- **Multiple ventes du même bien** en < 12 mois : flip, possible problème de qualité ou de titre
