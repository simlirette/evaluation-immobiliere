---
name: analyse-approche-comparaison
description: >
  Appliquer l'approche par comparaison directe : ajustements par paires,
  grille d'ajustements, indicateurs de valeur et pondération finale.
type: analyse
agents:
  - valuation-draft
sources:
  - comparables_proposes
  - donnees_marche
  - mefq_manuel
---

## Objectif

Produire une conclusion de valeur par l'approche comparative avec une grille d'ajustements documentée, sourcée et conforme aux normes OEAQ.

## Procédure

### 1. Vérification du corpus de comparables

Avant de commencer les ajustements :
- Confirmer que chaque comparable a un `source_id` valide
- Vérifier que les dates de vente sont antérieures à la date de référence
- Confirmer les unités (m², pas pi²)
- Identifier si des ajustements de conditions de vente sont requis

### 2. Grille d'ajustements (par comparable)

**Séquence d'application des ajustements** (ordre obligatoire) :

1. **Conditions de vente** — Ajustement si vente non libre (ex : -15% si vente de liquidation)
2. **Conditions de financement** — Ajustement si financement à des conditions hors marché
3. **Ajustement temporel** — Correction pour l'évolution du marché entre date comparable et date référence
4. **Ajustements de localisation** — Rue, secteur, vue, bruit, accès
5. **Ajustements physiques** — Superficie terrain, superficie bâtie, âge, état, équipements

**Format de la grille :**

```
Comparable 1 — [Adresse] — Prix de vente : 450 000 $

Éléments de comparaison          Sujet      Comp.1      Ajustement ($)
─────────────────────────────────────────────────────────────────────
Prix de vente brut                —          450 000 $       —
Conditions de vente               normales   normales        0 $
Conditions de financement         marché     marché          0 $
Ajustement temporel (+1.5%/3m)   2024-09    2024-03     +6 750 $
─────────────────────────────────────────────────────────────────────
Prix ajusté (conditions/temps)                           456 750 $
─────────────────────────────────────────────────────────────────────
Localisation                      secteur A  secteur B   -9 135 $
Superficie terrain                350 m²     320 m²      +4 500 $
Superficie habitable              130 m²     145 m²      -8 700 $
Âge effectif                      10 ans     15 ans      +3 200 $
État général                      bon        bon              0 $
Garage attaché                    oui        non        +15 000 $
─────────────────────────────────────────────────────────────────────
Total ajustements physiques                             +4 865 $
─────────────────────────────────────────────────────────────────────
Prix ajusté net                                         461 615 $
```

### 3. Indicateurs de valeur

Après ajustement de tous les comparables :
- Calculer la plage : min ajusté à max ajusté
- Calculer la médiane des prix ajustés
- Calculer la moyenne (si distribution symétrique)
- Identifier les comparables les plus similaires pour leur accorder plus de poids

**Pondération :**
```
Comparables avec score similarité ≥ 0.85 → poids élevé (35–40%)
Comparables avec score 0.70–0.85 → poids moyen (25–30%)
Comparables avec score 0.55–0.70 → poids faible (15–20%)
```

### 4. Conclusion par l'approche comparative

```
Indicateur de valeur — Approche comparative : [X $]
Plage : [X $ à X $]
Nombre de comparables : [N]
Comparable dominant : [adresse + raison]
```

## Contrôles de qualité

- Somme des ajustements bruts ≤ 30% du prix comparable (règle MEFQ)
- Aucun ajustement unique > 20% du prix comparable sans justification narrative
- Les ajustements de localisation doivent être supportés par des données de marché (pas par opinion seule)
- Tout ajustement ≥ 25 000 $ → `validation_humaine: true` dans le JSON
