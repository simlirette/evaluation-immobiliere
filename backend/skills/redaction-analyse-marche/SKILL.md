---
name: redaction-analyse-marche
description: >
  Rédiger la section d'analyse de marché d'un rapport d'évaluation immobilière :
  contexte macro, tendances sectorielles, analyse des ventes récentes.
type: redaction
agents:
  - redaction
sources:
  - donnees_marche
  - comparables_proposes
  - justifications_comparables
---

## Objectif

Produire une section d'analyse de marché professionnelle qui contextualise les conclusions de valeur et démontre la maîtrise du marché local par l'évaluateur.

## Structure de la section d'analyse de marché

```markdown
## [N]. Analyse de marché

### [N].1 Contexte macroéconomique

[1 paragraphe : taux d'intérêt, inflation, conjoncture économique Québec,
impact sur le marché immobilier. Données SCHL, BdC, ISQ.]

### [N].2 Marché immobilier — [Secteur géographique]

**Période analysée :** [date début] au [date de référence]

**Activité du marché résidentiel :**
- Nombre de ventes : [N] transactions enregistrées
- Prix médian : [X $], variation de [±N%] sur 12 mois
- Délai de vente médian : [N] jours sur le marché
- Ratio offre/demande : [marché vendeur / équilibré / acheteur]
- Source : [CIGM / DLC / Chambre immobilière Québec]

**Tendance des prix :**
[1–2 phrases sur la direction et la stabilité des prix dans le secteur précis.
Ex : "Le secteur [nom] a enregistré une stabilisation des prix au cours des
12 derniers mois après la correction de 2023, soutenue par la reprise de la
demande et une offre limitée."]

### [N].3 Analyse des ventes comparables retenues

[Tableau synthèse des comparables avec prix, date, superficie, $/m²]

| # | Adresse | Vente | Prix | Superficie | $/m² | Score |
|---|---------|-------|------|-----------|------|-------|
| 1 | [addr] | [date] | [X $] | [X m²] | [X] | [0.xx] |
| 2 | ... | ... | ... | ... | ... | ... |

**Observations :**
[1–2 paragraphes : cohérence du corpus, fourchette de prix, particularités notables]

### [N].4 Conclusion sur la représentativité du marché

[1 paragraphe : Les ventes retenues sont-elles représentatives du marché actif
à la date de référence ? Limitations éventuelles (peu de ventes, secteur atypique).]
```

## Données de marché Québec 2025–2026 à intégrer si pertinent

| Région | Segment | Indicateur | Valeur |
|--------|---------|-----------|-------|
| Grand Montréal | Unifamiliale | Prix médian | ~575 000 $ |
| Grand Montréal | Condo | Prix médian | ~415 000 $ |
| Ville de Québec | Unifamiliale | Prix médian | ~430 000 $ |
| Laval | Unifamiliale | Prix médian | ~530 000 $ |
| Grand Montréal | Plex (2-5) | TGA | 3.5–4.5% |
| Grand Montréal | Bureau | Taux inoccupation | 18–22% |
| Grand Montréal | Industriel | Taux inoccupation | 2–4% |

*Sources : CIGM, SCHL, CBRE Québec, JLL Montréal (2025)*

## Règles de rédaction

- Citer toujours la source et la période couverte par les données
- Ne pas extrapoler les tendances au-delà des données disponibles
- Si les données sont limitées (< 5 ventes dans le secteur), le signaler explicitement
- Distinguer l'analyse macro (province / région) de l'analyse micro (secteur immédiat du sujet)
