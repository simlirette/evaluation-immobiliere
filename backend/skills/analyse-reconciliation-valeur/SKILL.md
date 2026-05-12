---
name: analyse-reconciliation-valeur
description: >
  Effectuer la réconciliation des indicateurs de valeur des trois approches
  et formuler la conclusion de valeur finale motivée.
type: analyse
agents:
  - valuation-draft
sources:
  - calculs_approche_comparative
  - calculs_approche_cout
  - calculs_approche_revenu
  - normes_oeaq
---

## Objectif

Produire une conclusion de valeur unique et motivée à partir des indicateurs des différentes approches, en respectant les principes OEAQ.

## Principe fondamental

**La réconciliation n'est pas une moyenne arithmétique.** C'est un jugement professionnel motivé qui tient compte de :
- La qualité et la quantité des données soutenant chaque approche
- La pertinence de chaque approche pour le type de bien et le mandat
- La cohérence interne de chaque indicateur
- Le type de valeur recherché (marchande, JVM, réelle LFM)

## Processus de réconciliation

### 1. Inventaire des indicateurs

```
Approche comparative : [X $]   — [N] comparables, confiance [haute/moyenne/faible]
Approche par le coût : [X $]   — dépréciation [N]%, confiance [haute/moyenne/faible]
Approche par le revenu : [X $] — TGA [N]%, RNE [X $], confiance [haute/moyenne/faible]
```

### 2. Cohérence inter-approches

Calculer l'écart entre les indicateurs :
```
Écart maximal = (valeur_max - valeur_min) / valeur_min × 100%

Écart ≤ 10% → indicateurs cohérents, réconciliation facile
Écart 10–35% → expliquer la divergence, justifier le poids accordé
Écart > 35% → identifier la cause (données faibles ?), signal CONF007
```

### 3. Pondération par type de bien

**Principes directeurs MEFQ :**

| Type de bien | Approche dominante | Approche secondaire | Approche tertiaire |
|---|---|---|---|
| Résidentiel (occupant) | Comparaison (60–80%) | Coût (20–40%) | Revenu (0–10%) |
| Condo résidentiel | Comparaison (70–90%) | Coût (10–20%) | — |
| Multi-logements | Revenu (50–70%) | Comparaison (30–50%) | Coût (0–10%) |
| Commercial locatif | Revenu (60–80%) | Comparaison (20–30%) | Coût (0–10%) |
| Bâtiment spécialisé | Coût (60–80%) | Comparaison (20–30%) | — |
| Terrain vacant | Comparaison (80–100%) | — | — |
| Hôtel | Revenu / DCF (70–90%) | Coût (10–20%) | — |

**Justifications possibles pour modifier le poids standard :**
- Données de comparaison insuffisantes → augmenter poids coût ou revenu
- Données de revenus non fiables → augmenter poids comparaison
- Bien unique sans comparables → coût prime

### 4. Formulation de la conclusion

```markdown
## Réconciliation et conclusion de valeur

Les trois approches indiquent les valeurs suivantes :
- Approche comparative : [X $] (poids retenu : [N]%)
- Approche par le coût : [X $] (poids retenu : [N]%)
- Approche par le revenu : [X $] (poids retenu : [N]%)

L'approche [comparative / par le revenu / par le coût] reçoit le poids dominant
parce que [justification : marché actif avec nombreuses ventes / bien à revenus
stabilisés / absence de comparables pertinents / etc.].

**Conclusion de valeur marchande à la date de référence [date] :**
**[X $] (arrondis à la tranche de X 000 $)**
```

### 5. Arrondissement de la valeur

- Valeur < 100 000 $ → arrondir à la tranche de 1 000 $
- Valeur 100 000–500 000 $ → arrondir à la tranche de 5 000 $
- Valeur 500 000–1 000 000 $ → arrondir à la tranche de 10 000 $
- Valeur > 1 000 000 $ → arrondir à la tranche de 25 000 $

## Interdictions déontologiques

- Ne jamais choisir la valeur qui convient le mieux au client comme conclusion finale
- Ne jamais appliquer une "fourchette de valeur" sans conclure à une valeur unique
- La valeur finale doit être défendable sur la base des données, pas des préférences
