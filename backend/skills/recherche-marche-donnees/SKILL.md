---
name: recherche-marche-donnees
description: >
  Collecter et analyser les données de marché immobilier québécois (ventes, prix,
  tendances, taux d'inoccupation) pour contextualiser l'évaluation.
type: recherche
agents:
  - data-facts
  - comps-market
sources:
  - dlc_donnees_marche
  - centris_mls
  - gestim_plus
  - rapports_marche_cbre_jll
---

## Objectif

Fournir un contexte de marché rigoureux qui soutient les conclusions de valeur et permet à l'évaluateur de calibrer ses ajustements temporels et géographiques.

## Données de marché à collecter

### Marché résidentiel (unifamiliale, condo, multiplex)

**Sources primaires :**
- **DLC (Données sur les marchés résidentiels)** — ventes déclarées via les chambres immobilières
- **Centris / MLS** — inscriptions actives, historique de prix demandés
- **Registre foncier** — actes de vente bruts (prix payé, date)
- **Chambre immobilière du Grand Montréal (CIGM)** — statistiques mensuelles
- **APCHQ** — mises en chantier résidentielles par secteur

**Indicateurs clés :**
- Nombre de ventes (volume) par secteur × trimestre
- Prix médian et moyen par type (unifamiliale, condo, multiplex)
- Prix au m² habitabl (résidentiel) ou prix au m² de terrain
- Ratio prix demandé / prix vendu (indicator demand pressure)
- Délai de vente médian (jours sur le marché — DOM)
- Taux d'inoccupation résidentiel (SCHL — données annuelles)

### Marché commercial et industriel

**Sources primaires :**
- **GESTIM Plus** — ventes tertiaires, industrielles, commerciales québécoises
- **CBRE / JLL / Colliers** — rapports trimestriels de marché (gratuits en ligne)
- **Altus Group** — rapports coûts de construction + statistiques marché

**Indicateurs clés :**
- TGA par secteur (bureau, commercial de quartier, industriel)
- Taux d'inoccupation commercial / bureaux / industriel
- Loyers nets de marché ($/m²/an)
- Taux de capitalisation à la sortie (exit cap rate)

### Tendances 2024–2026 Québec

**Données de contexte à inclure dans le rapport :**

| Secteur | Tendance | Source |
|---------|---------|--------|
| Résidentiel Montréal | Stabilisation après correction 2022–2023, légère reprise | CIGM |
| Résidentiel Québec | Marché plus stable, moins volatile | IQHFF |
| Multi (5+ logements) | TGA compressé à 3,5–4,5% (Montréal), 4,5–5,5% (régions) | GESTIM |
| Bureaux centre-ville | Inoccupation 18–22%, pression baissière sur loyers | CBRE |
| Industriel léger | Inoccupation < 3%, loyers à la hausse | JLL |

### Ajustement temporel

Si les comparables retenus datent de plus de 6 mois, appliquer un ajustement temporel :

```
Ajustement temporel (%) = Variation de l'indice de prix sur la période
Source de l'indice : SCHL, CIGM, ou IPP (Indice des prix des propriétés)
```

Documenter l'ajustement : "Le marché a progressé de X% entre [date comparable] et [date référence], source : CIGM Q3-2024."

## Format de synthèse attendu

```markdown
## Contexte de marché — [Secteur], [Type de bien]

**Période :** [date début] – [date de référence]
**Activité :** [N] ventes enregistrées dans le secteur
**Prix médian :** X $, variation de Y% sur 12 mois
**DOM médian :** Z jours
**Tendance :** hausse / stabilité / baisse
**Source principale :** DLC / CIGM / Centris

*Implication pour l'évaluation :* Le marché [contexte] suggère que [conclusion sur la fiabilité des comparables et des ajustements retenus].*
```
