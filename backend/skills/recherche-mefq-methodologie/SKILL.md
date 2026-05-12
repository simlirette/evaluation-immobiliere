---
name: recherche-mefq-methodologie
description: >
  Appliquer les méthodes du Manuel d'évaluation foncière du Québec (MEFQ) pour
  les calculs de valeur, ajustements et analyses quantitatives.
type: recherche
agents:
  - data-facts
  - comps-market
  - valuation-draft
  - compliance-qa
sources:
  - mefq_manuel
  - normes_oeaq
---

## Objectif

Assurer que les calculs quantitatifs (ajustements, capitalisation, coût) suivent les méthodes standardisées du MEFQ et sont reproductibles.

## Méthodes MEFQ clés

### Approche comparative — grille d'ajustements

**Ajustements en pourcentage (% du prix de vente comparable) :**

| Élément | Fourchette typique | Commentaire |
|---------|------------------|-------------|
| Conditions de vente anormales | -30% à +10% | Vente forcée, lien de dépendance |
| Conditions de financement | -5% à +5% | Prise en charge hypothécaire |
| Ajustement temporel | ±1–3% / trimestre | Selon indice de marché |
| Localisation | ±5–20% | Secteur, vue, accès, bruit |
| Superficie du terrain | ±2–10% | Règle du $/m² marginal décroissant |
| Superficie bâtie | ±3–8% | $/m² habitabl |
| Âge et état | ±1–3% par an d'écart | Âge effectif, pas âge chronologique |
| Équipements | ±2–5% | Garage, piscine, spa, centrale |
| Étages | ±1–3% | Condo : étage élevé vs bas |

**Règle des 30% :** La somme des ajustements bruts (valeur absolue) ne doit pas dépasser 30% du prix de vente du comparable. Au-delà, la comparaison est douteuse → remplacer le comparable.

### Méthode de capitalisation directe (MEFQ § 8.4)

```
Valeur = RNE / TGA

RNE = Revenu Brut Potentiel
    × (1 - Taux d'inoccupation stabilisé)
    - Dépenses d'exploitation normalisées

TGA = extrait du marché (RNE vérifié / prix de vente comparable)
```

**Normalisation des dépenses :**
- Exclure le service de la dette (non opérationnel)
- Exclure la dépréciation comptable
- Inclure une réserve pour remplacement (CapEx normalisé)
- Normaliser les dépenses de gestion si propriétaire-gestionnaire

### Méthode du coût (MEFQ § 7.x)

```
Valeur = Valeur du terrain (séparée)
       + Coût de remplacement neuf (CRN)
       × (1 - Taux de dépréciation global)

Dépréciation globale = Physique + Fonctionnelle + Économique
```

**Dépréciation physique :**
```
Taux = Âge effectif / Durée de vie économique totale
Durée de vie économique : maison bois = 60–80 ans, béton = 80–100 ans
Âge effectif ≤ âge chronologique (entretien supérieur réduit l'âge effectif)
```

### Analyse de régression (MEFQ § 5.x)

Pour les marchés avec > 30 ventes disponibles, la régression linéaire multiple permet :
- Isoler la contribution marginale de chaque caractéristique
- Produire des ajustements fondés sur le marché (pas sur l'opinion)
- Calculer des intervalles de confiance

**Variables typiques :** superficie, âge, nombre de salles de bains, garage, sous-sol fini, localisation (dummy variables par secteur)

### Analyse des tendances (ajustement temporel)

```python
# Calcul de l'ajustement temporel mensuel
mois_ecart = (date_reference - date_vente_comparable).days / 30
ajustement_temporel = taux_variation_mensuel * mois_ecart

# Source taux : Indice CIGM ou SCHL pour le secteur
```

## Contrôles de cohérence

- Valeurs des 3 approches : écart maximum acceptable = 35% (règle CONF007)
- Si écart > 35% : identifier la cause (données faibles, bien atypique) et documenter
- La valeur finale doit se situer dans la plage indiquée par les approches
- Ne jamais choisir la valeur la plus favorable au client comme valeur finale
