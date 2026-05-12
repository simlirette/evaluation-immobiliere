---
name: analyse-approche-fta
description: Applique l'approche par flux de trésorerie actualisés (FTA/DCF) pour immeubles revenus/commercial — §9.7 workflow OEAQ
type: analyse
agents:
  - valuation-draft
sources:
  - workflow-evaluateur-agree.md
---

# Skill — Analyse par flux de trésorerie actualisés (FTA / DCF)

## Rôle

Méthode de valorisation par actualisation des flux de trésorerie futurs. Complément
à l'approche revenu par capitalisation directe pour les revenus non stabilisés,
baux complexes et propriétés commerciales en repositionnement.

## Quand utiliser FTA vs capitalisation directe

| Situation | Capitalisation directe | FTA/DCF |
|---|---|---|
| Revenus stables et permanents | Préféré | Optionnel |
| Vacance élevée / baux expirant | Non adapté | Requis |
| Baux hors marché | Difficile | Requis |
| Repositionnement | Non adapté | Requis |
| Portefeuille commercial complexe | Insuffisant | Requis |

## Méthodologie (5 étapes)

1. **Période de projection** : 5–10 ans selon type de bien
2. **Flux annuels** : RBP − Vacance − Charges = RNE, projeté année par année
3. **Valeur terminale** : RNE(N+1) ÷ exit cap rate
4. **Taux d'actualisation** : taux sans risque + primes de risque immobilier
5. **Actualisation** : VP = Flux_N ÷ (1 + r)^N; Valeur = Σ VP(flux) + VP(terminale)

## Paramètres clés à documenter

- Période de projection (N années)
- Taux de croissance des revenus (% par an)
- Taux de vacance normalisé (%)
- Taux d'actualisation (%) + décomposition
- Exit cap rate (%) + justification par rapport au going-in cap rate

## Règles critiques

- Taux d'actualisation ≠ taux de capitalisation (concepts distincts)
- Toutes les hypothèses DOIVENT être documentées et défendables
- Analyse de sensibilité requise pour rapports commerciaux (§9.8)
- Arrondis : cohérents avec la précision des intrants

## Checklist

- [ ] Période de projection justifiée selon type de bien
- [ ] RNE projeté pour chaque année avec hypothèses explicites
- [ ] Valeur terminale calculée avec exit cap rate justifié
- [ ] Taux d'actualisation décomposé (sans risque + primes)
- [ ] VP calculée pour chaque flux + valeur terminale
- [ ] Valeur totale arrondie de manière cohérente
- [ ] Analyse de sensibilité si rapport commercial
