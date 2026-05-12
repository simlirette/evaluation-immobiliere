---
name: analyse-approche-revenu
description: >
  Appliquer l'approche par le revenu (capitalisation directe et DCF) pour
  les immeubles à revenus : multi-logements, commercial, industriel.
type: analyse
agents:
  - valuation-draft
sources:
  - revenus_depenses
  - baux_locatifs
  - donnees_marche
  - mefq_manuel
---

## Objectif

Calculer la valeur d'un immeuble à revenus selon l'approche par le revenu (capitalisation directe ou FTA/DCF) conformément aux normes OEAQ.

## Méthode 1 — Capitalisation directe

### Formule

```
Valeur = RNE / TGA

RNE = Revenu net d'exploitation
TGA = Taux global d'actualisation (extrait du marché)
```

### Calcul du RNE

```
Revenu brut potentiel (RBP)
  = Σ loyers annuels de marché × superficie
  + Revenus accessoires (stationnement, entreposage)

(-) Inoccupation et créances
  = RBP × Taux d'inoccupation stabilisé (TIS)
  (résidentiel Mtl 2025 : 2–4% ; commercial : 6–12%)

= Revenu effectif brut (REB)

(-) Dépenses d'exploitation normalisées
  - Taxes foncières
  - Assurances bâtiment
  - Entretien et réparations (5–8% RBP résidentiel)
  - Gestion (5–8% REB si gestion externe)
  - Déneigement / aménagement paysager
  - Services publics (espaces communs)
  - Réserve pour remplacement (1–2% RBP)

= Revenu net d'exploitation (RNE)
```

**Important :** Le RNE est calculé AVANT le service de la dette. Le financement n'affecte pas la valeur marchande.

### Extraction du TGA

Le TGA doit être tiré du marché, pas établi arbitrairement :

```
TGA = RNE vérifié d'une transaction comparable / Prix de vente de cette transaction
```

**Sources TGA Québec 2025 :**

| Segment | TGA typique | Source |
|---------|------------|--------|
| Multi 5–12 log. Montréal | 3.5–4.5% | GESTIM / CBRE |
| Multi 5–12 log. régions | 4.5–5.5% | GESTIM |
| Multi 13+ log. Montréal | 3.0–4.0% | CBRE / JLL |
| Commercial de quartier | 5.0–6.5% | GESTIM |
| Bureau classe B | 6.0–8.0% | CBRE |
| Industriel léger | 4.0–5.5% | JLL / Colliers |

**Minimum 3 transactions pour établir le TGA de marché.** Si données insuffisantes : indiquer W005 (TGA non extrait du marché).

### Baux hors marché

Si le loyer en vigueur ≠ loyer de marché :
- **Loyer sous le marché** : Calculer la valeur avec loyers actuels (valeur continuation) ET avec loyers de marché (valeur stabilisée). La valeur est entre les deux selon le terme résiduel des baux.
- **Loyer sur le marché** : Idem — valeur favorable temporaire, ajustement si renouvellement incertain.

## Méthode 2 — Flux de trésorerie actualisés (FTA/DCF)

### Quand utiliser le DCF

- Flux de revenus irréguliers ou en période de stabilisation
- Immeubles commerciaux avec baux à terme fixe (clauses d'escalade)
- Hôtels, RPA (flux complexes)
- Projets de développement (pré-construction)

### Structure du DCF

```
Période de projection : 10 ans standard
Taux d'actualisation (r) : TGA + prime de risque
  (résidentiel stable : r ≈ TGA + 0.5–1.5%)

Valeur terminale (année 11) :
  = RNE année 11 / Taux de capitalisation sortant (exit cap rate)
  (exit cap rate ≥ TGA d'entrée — marché plus mature)

Valeur actuelle = Σ (CF_t / (1+r)^t) + Valeur terminale / (1+r)^10
```

### Analyse de sensibilité

Toujours produire une analyse de sensibilité sur :
- Taux d'inoccupation ± 2%
- TGA ± 25 points de base
- Taux d'actualisation ± 50 points de base

## Applicabilité

**Capitalisation directe appropriée si :**
- Revenus stables et prévisibles
- TGA extrait du marché disponible
- Multi-logements résidentiel standard

**DCF préférable si :**
- Flux variables (construction, rénovation majeure)
- Baux commerciaux avec escalades connues
- Immeuble en période de stabilisation (< 90% d'occupation)
