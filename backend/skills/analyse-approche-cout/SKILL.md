---
name: analyse-approche-cout
description: >
  Appliquer l'approche par le coût : valeur du terrain, coût de remplacement neuf,
  dépréciation physique/fonctionnelle/économique, pour obtenir la valeur par le coût.
type: analyse
agents:
  - valuation-draft
sources:
  - couts_reference
  - donnees_marche
  - mefq_manuel
---

## Objectif

Calculer la valeur du bien selon l'approche par le coût (valeur terrain + coût de remplacement déprécié) conformément au MEFQ.

## Formule générale

```
Valeur par le coût = Valeur du terrain (séparée)
                   + Coût de remplacement neuf (CRN) des améliorations
                   - Dépréciation acumulée (physique + fonctionnelle + économique)
```

## Étape 1 — Valeur du terrain

**Méthode privilégiée :** Comparaison directe avec terrains vacants vendus récemment dans le secteur.

Si aucun terrain vacant comparable : utiliser la méthode de la valeur résiduelle ou d'abstraction :
```
Valeur terrain = Prix de vente immeuble - Valeur contributive des améliorations
```

**Sources :** DLC (terrains), Registre foncier, portails municipaux (ventes de terrains).

**Note :** Pour les propriétés avec AMU différent du bâtiment existant, utiliser la valeur du terrain selon l'AMU (et non l'usage actuel).

## Étape 2 — Coût de remplacement neuf (CRN)

**Sources de coûts :**

| Source | Usage | Mise à jour |
|--------|-------|-------------|
| Marshall & Swift (Valbridge) | Résidentiel, commercial, industriel | Trimestrielle |
| Altus Group | Multirésidentiel, commercial | Annuelle |
| APCHQ / APECQ | Construction résidentielle Québec | Annuelle |
| Devis d'entrepreneur | Bâtiment neuf ou récemment construit | À la date |

**Facteurs d'ajustement du coût :**
- Facteur régional (Québec vs Montréal vs régions éloignées)
- Facteur temporel (indice de coût de construction depuis la date du guide)
- Type de finitions (standard / moyen / supérieur / luxe)

**Coûts à inclure dans le CRN :**
- Structure (fondation, ossature, toiture)
- Enveloppe (revêtement extérieur, fenêtres, portes)
- Systèmes mécaniques et électriques
- Finitions intérieures
- Aménagements extérieurs permanents
- Frais indirects : honoraires professionnels (10–15%), contingences (5%)

**À exclure du CRN :**
- Valeur du terrain (calculée séparément)
- Mobilier et équipements amovibles

## Étape 3 — Dépréciation accumulée

### a) Dépréciation physique

```
Taux dépréciation physique = Âge effectif / Durée de vie économique totale

Âge effectif : déterminé par l'inspection physique (peut être < âge chronologique si entretien supérieur)
Durée de vie économique : 
  - Maison à ossature bois : 60–75 ans
  - Duplex / triplex : 65–80 ans
  - Multi-logements béton : 80–100 ans
  - Commercial léger (acier/bois) : 40–60 ans
  - Industriel : 40–50 ans
```

### b) Dépréciation fonctionnelle

Perte de valeur due à des déficiences intrinsèques (conception dépassée, équipements obsolètes) :
- Cuisine ou salle de bains hors mode → 2–8% du CRN
- Absence de garage dans un marché où c'est standard → 3–6% du CRN
- Plafonds trop bas → 1–3%
- Plan d'étage peu fonctionnel → 2–5%

### c) Dépréciation économique (externe)

Perte de valeur due à des facteurs hors du contrôle du propriétaire :
- Zone de bruit (aéroport, autoroute) → 5–20%
- Déclin économique du quartier → 5–15%
- Surabondance de l'offre dans le secteur → 5–10%

## Étape 4 — Calcul final

```
CRD (Coût de remplacement déprécié) = CRN × (1 - taux dépréciation globale)
Valeur par le coût = Valeur terrain + CRD
```

## Applicabilité et limites

**Plus fiable pour :**
- Bâtiments neufs ou récents (< 15 ans)
- Biens spécialisés sans comparables (église, école, usine)
- Assurance et expropriation (coût de remplacement)

**Moins fiable pour :**
- Biens anciens avec forte dépréciation → imprécision croissante
- Biens dans des marchés très actifs (comparaison prime)
- Biens générateurs de revenus (revenu prime)
