# Analyse — Approche par flux de trésorerie actualisés (FTA / DCF)

## Source doctrine
workflow-evaluateur-agree.md §9.7 — Approche — Flux de trésorerie actualisés (FTA / DCF)

## Quand utiliser le DCF

- Revenus non stabilisés : vacance élevée, baux expirant bientôt, loyers en escalade contractuelle
- Propriétés en redéveloppement ou repositionnement
- Portefeuilles commerciaux complexes (tours de bureaux, centres commerciaux)
- Mandats exigeant une analyse de sensibilité poussée
- Baux hors marché (above-market ou below-market leases)
- La capitalisation directe suppose des revenus stables — le DCF lève cette hypothèse

## Étape 1 — Définir la période de projection

```
Typiquement 5 à 10 ans selon le type de bien et la nature des baux :
  ├── Immeubles commerciaux avec baux long terme : 10 ans
  ├── Multilogements : 5–7 ans (revenus plus prévisibles)
  └── Propriétés en repositionnement : selon durée de la stratégie
```

## Étape 2 — Projeter les flux de trésorerie annuels

Pour chaque année de la période de projection :
```
  Revenus bruts potentiels (RBP)
  − Vacance et pertes sur créances
  = Revenus bruts effectifs (RBE)
  − Charges d'exploitation (taxes, assurances, entretien, gestion)
  = Revenu net d'exploitation (RNE)
```

Hypothèses de projection :
- Taux de croissance des revenus (par bail ou par marché)
- Taux de vacance normalisé
- Évolution des charges (inflation)

## Étape 3 — Calculer la valeur terminale

```
Valeur terminale = RNE(année N+1) ÷ Exit cap rate (taux de sortie)
```

Taux de sortie (exit cap rate) :
- Généralement légèrement supérieur au taux d'entrée (going-in cap rate)
- Reflète le vieillissement du bien
- Écart typique : 25–50 points de base au-dessus du taux d'entrée

## Étape 4 — Déterminer le taux d'actualisation

```
Composantes :
  ├── Taux sans risque (obligations gouvernementales 10 ans)
  ├── Prime de risque immobilier (liquidité, gestion, marché)
  ├── Prime de risque spécifique au bien (âge, localisation, qualité locataires)
  └── Prime d'illiquidité

Taux typiques Québec 2025 :
  ├── Multirésidentiel : 5,0 % – 6,5 %
  ├── Commercial/bureau : 6,0 % – 8,0 %
  └── Industriel : 5,5 % – 7,0 %
```

## Étape 5 — Actualiser tous les flux

```
VP d'un flux futur = Flux année N ÷ (1 + taux d'actualisation)^N

Valeur par FTA = Σ VP(RNE années 1 à N) + VP(valeur terminale)
```

## Exemple numérique (§9.7) — Immeuble commercial 5 ans

```
Taux d'actualisation : 7,0 %     Exit cap rate : 6,5 %

Année   RNE       Facteur VP (7%)   VP du flux
  1    100 000      0,9346           93 458
  2    103 000      0,8734           89 960
  3    106 090      0,8163           86 601
  4    109 273      0,7629           83 367
  5    112 551      0,7130           80 249

Valeur terminale = 112 551 × (1,02) ÷ 0,065 = 1 765 893
VP valeur terminale = 1 765 893 × 0,7130 = 1 259 082

VALEUR PAR FTA = 93 458 + 89 960 + 86 601 + 83 367 + 80 249 + 1 259 082
              = 1 692 717 $ → arrondi à 1 690 000 $
```

## Cas spéciaux : baux hors marché

### Bail sous le marché (below-market lease)
- Loyer réel < loyer du marché
- Valeur de continuation < valeur marchande stabilisée
- Méthode : DCF avec loyers réels années 1 à N, puis loyers marché années N+1 et suivantes

### Bail sur le marché (above-market lease)
- Loyer réel > loyer du marché
- Valeur de continuation > valeur marchande stabilisée
- Même approche DCF bipartite

## Règles critiques

- Le taux d'actualisation ≠ le taux de capitalisation
- Documenter TOUTES les hypothèses : taux de croissance, vacance, charges, taux d'actualisation, exit cap rate
- Analyse de sensibilité obligatoire dans les rapports commerciaux (§9.8)
- Arrondis cohérents avec la précision des données sources
