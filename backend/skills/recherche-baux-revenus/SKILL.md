---
name: recherche-baux-revenus
description: >
  Analyser les baux en place, les revenus locatifs et les dépenses d'exploitation
  pour préparer l'approche par le revenu (capitalisation directe ou FTA/DCF).
type: recherche
agents:
  - data-facts
  - valuation-draft
sources:
  - baux_locatifs
  - declarations_proprietaire
  - etats_financiers
---

## Objectif

Constituer le tableau de revenus et dépenses d'exploitation normalisés (état proforma) pour le bien évalué.

## Procédure

### 1. Inventaire des baux

Pour chaque bail en place :
- Locataire (anonymisé si résidentiel — « Locataire A »)
- Surface louée (m²) et numéro d'unité
- Loyer mensuel brut ($ / mois)
- Loyer annuel brut ($ / an)
- Date de début et date d'expiration du bail
- Type de bail : brut / net / double net / triple net (NNN)
- Clauses d'escalade (indexation annuelle, révision aux 5 ans)
- Droit de renouvellement et conditions
- Baux hors marché : loyer actuel vs loyer de marché → indiquer la différence

### 2. Calcul du revenu brut potentiel (RBP)

```
RBP = Σ (loyer annuel × superficie) pour toutes les unités
    + Revenus accessoires (stationnement, entreposage, antennes)
    + Revenus de services (buanderie, vending)
```

**Distinctions importantes :**
- Loyer économique (bail en vigueur) vs loyer de marché (taux courant pour unités similaires)
- Si bail hors marché (< 85% ou > 115% du marché), ajustement requis pour l'approche revenu

### 3. Taux d'inoccupation et créances irrécouvrables

- Taux d'inoccupation stabilisé (TIS) : taux marché selon secteur et type de bien
  - Résidentiel Montréal 2025 : 2–4%
  - Bureau centre-ville : 15–25%
  - Commercial de quartier : 6–10%
  - Industriel : 3–6%
- Créances irrécouvrables : généralement 0,5–1% du RBP résidentiel

```
REP (revenu effectif potentiel) = RBP × (1 - TIS) - créances
```

### 4. Charges d'exploitation (dépenses normalisées)

| Poste | Résidentiel | Commercial |
|-------|------------|-----------|
| Taxes foncières | ✓ | ✓ (sauf NNN) |
| Assurances | ✓ | ✓ (sauf NNN) |
| Entretien et réparations | 5–8% du RBP | 3–5% du RBP |
| Gestion immobilière | 5–8% du REP | 3–5% du REP |
| Services publics (espaces communs) | ✓ | selon bail |
| Réserve pour remplacement (CapEx) | 1–2% du RBP | 1–2% du RBP |

### 5. Revenu net d'exploitation (RNE)

```
RNE = REP - Dépenses d'exploitation normalisées
    (AVANT service de la dette — le financement n'affecte pas la valeur)
```

### 6. Taux global d'actualisation (TGA)

Le TGA doit être extrait du marché (analyse de ventes avec revenus vérifiés) :
```
TGA = RNE d'une vente comparable / prix de vente de cette transaction
```

- Valeur = RNE / TGA

**Sources TGA :** GESTIM Plus, CBRE, Altus, JLL (rapports marchés), transactions DLC avec revenus.

## Signaux d'alerte

- Loyers significativement inférieurs au marché → baux protégés, locataires de longue date
- Rotation élevée des locataires → risque opérationnel
- Dépenses réelles < 25% du RBP pour immeuble résidentiel → données incomplètes
- TGA < 3% ou > 8% pour multirésidentiel Montréal → vérifier la cohérence
