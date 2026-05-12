---
name: analyse-amu
description: >
  Analyse du Meilleur Usage (AMU/UMPP) obligatoire selon NPP OEAQ. Utiliser ce skill
  pour évaluer les 4 critères OEAQ (légalement permis, physiquement possible,
  financièrement faisable, maximalement productif) et produire umpp_conclusion.json
  et amu_analyse.md avant toute approche d'évaluation.
type: analyse
agents:
  - amu-analyst
sources:
  - fiche_bien.json
  - source_index.json
  - urbanisme_zonage
  - normes_professionnelles
---

# Skill : Analyse du Meilleur Usage (AMU)

## 1. Rôle et contexte

Ce skill encode la méthodologie AMU obligatoire selon la Norme de pratique professionnelle OEAQ. Il doit être appliqué **avant toute approche d'évaluation** et avant la sélection des comparables.

L'AMU détermine l'UMPP (Usage le Meilleur et le Plus Profitable) — l'usage qui, parmi tous les usages raisonnables et légalement permis, génère la valeur foncière la plus élevée.

**Artefacts produits :**
- `umpp_conclusion.json` → lu par l'agent `comps-market` pour guider la sélection des comparables
- `amu_analyse.md` → lu par l'agent `redaction` pour la section AMU du rapport

---

## 2. Connaissances encodées

### 2.1 Les quatre critères OEAQ (ordre obligatoire)

| Critère | Questions clés |
|---------|---------------|
| **1. Légalement permis** | Zonage autorise-t-il cet usage? Restrictions légales (servitudes, LPTA, patrimoine)? Usage dérogatoire protégé ou voué à disparaître? |
| **2. Physiquement possible** | Terrain (dimensions, forme, topographie) compatible? Services publics disponibles? Accès voie publique? Contraintes environnementales? |
| **3. Financièrement faisable** | Rendement > coût de développement? Demande de marché? Financement disponible? |
| **4. Maximalement productif** | Parmi les usages satisfaisant les 3 critères, lequel génère la valeur foncière maximale? |

### 2.2 Terrain vacant vs amélioration existante

**Terrain vacant** : analyser directement l'usage optimal du sol.

**Amélioration existante** : mener deux analyses parallèles :
1. AMU du terrain seul (comme si vacant)
2. AMU du terrain avec amélioration existante

Si résultats identiques → évaluer tel quel (cas standard).
Si différents → situation transitoire, documenter et ajuster pour coûts de conversion.

### 2.3 Lien AMU → méthodes d'évaluation

| UMPP retenu | Méthode principale | Conséquence sur comparables |
|---|---|---|
| Résidentiel unifamilial | Comparaison | Comparables résidentiels |
| Plex 2-5 logements | Comparaison + revenu | Comparables multifamiliaux |
| Multilogement 6+ | Revenu | Immeubles locatifs similaires |
| Commercial | Comparaison | Ventes commerciales $/pi² |
| Industriel | Comparaison + coût | Ventes industrielles |
| Terrain | Comparaison terrains | Terrains similaires |

---

## 3. Méthodologie

### Étape 1 — Identifier l'usage actuel

Lire `fiche_bien.json` : champ `type_bien` et `zone`.

### Étape 2 — Évaluer le critère légal

Vérifier le zonage (zone dans le case). Identifier les restrictions possibles selon le type de bien et la zone. Conclure : `legalement_permis: true/false`.

### Étape 3 — Évaluer le critère physique

Vérifier les caractéristiques terrain dans la fiche bien (surface, configuration). Conclure : `physiquement_possible: true/false`.

### Étape 4 — Évaluer la faisabilité financière

Évaluer si le marché supporte cet usage dans cette zone. Pour V0 sans données de marché réelles : `financierement_faisable: true` si usage est conforme au type de bien fourni.

### Étape 5 — Déterminer l'usage maximalement productif

Parmi les usages satisfaisant les 3 critères, identifier celui qui génère la valeur la plus élevée. En général : l'usage actuel si conforme au zonage.

### Étape 6 — Documenter l'UMPP

Comparer UMPP avec usage actuel :
- Si UMPP == usage actuel : `umpp_differe_usage_actuel: false`
- Si UMPP ≠ usage actuel : `umpp_differe_usage_actuel: true` + documenter la situation transitoire

### Étape 7 — Produire les artefacts

Remplir `umpp_conclusion.json` avec les résultats structurés.
Rédiger `amu_analyse.md` avec la narrative des 4 critères et la conclusion.

---

## 4. Règles critiques

1. **TOUJOURS** documenter l'AMU même si UMPP == usage actuel — l'absence est une non-conformité NPP
2. **TOUJOURS** évaluer les 4 critères dans l'ordre — un usage illégal ne peut pas être UMPP
3. **TOUJOURS** analyser le terrain seul ET avec amélioration si bâtiment présent
4. **JAMAIS** conclure l'UMPP sans avoir vérifié le zonage — erreur sanctionnable
5. **JAMAIS** sélectionner des comparables avant de connaître l'UMPP
6. Pour les terrains en zone agricole (LPTA) : UMPP = agricole sauf autorisation CPTAQ explicite
7. Un usage dérogatoire non protégé ≠ légalement permis pour l'AMU

---

## 5. Checklist de qualité

- [ ] Usage actuel documenté dans la conclusion
- [ ] Les 4 critères évalués dans l'ordre
- [ ] Usages alternatifs considérés et justification du rejet
- [ ] Terrain seul analysé (si amélioration existante)
- [ ] Conclusion UMPP explicite avec usage nommé
- [ ] `umpp_differe_usage_actuel` correctement défini
- [ ] Lien UMPP → approches documenté
- [ ] Lien UMPP → type de comparables documenté
- [ ] Restrictions légales pertinentes identifiées
