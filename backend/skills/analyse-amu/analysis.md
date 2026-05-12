# Analyse — Analyse du Meilleur Usage (AMU)

> Synthèse exhaustive des pratiques en matière d'AMU dans l'évaluation immobilière québécoise conforme à la Norme de pratique professionnelle OEAQ.

---

## 1. Vue d'ensemble

| Aspect | Détail |
|--------|--------|
| Obligatoire | Oui — étape NPP OEAQ précédant toute approche d'évaluation |
| Position dans le workflow | Après collecte des faits, avant sélection des comparables |
| Artefacts produits | `umpp_conclusion.json` (structuré) + `amu_analyse.md` (narratif) |
| Normes applicables | NPP OEAQ §8, CUSPAP Standards Rule 1 |

---

## 2. Cadre normatif

L'AMU est l'usage qui, parmi tous les usages raisonnables et légalement permis, satisfait simultanément quatre critères et génère la valeur la plus élevée. Cette analyse est obligatoire et doit précéder l'application de toute approche d'évaluation.

Le rapport doit documenter :
- L'usage actuel
- L'usage optimal retenu (UMPP)
- La justification pour chacun des 4 critères
- Les usages alternatifs considérés et pourquoi rejetés
- Comment l'AMU oriente le choix des approches et des comparables

---

## 3. Les quatre critères OEAQ

### 3.1 Légalement permis

- Usage autorisé par le zonage municipal actuel
- Usage conforme au plan d'urbanisme
- Absence de restriction légale (servitude, covenant, désignation patrimoniale)
- Usage actuel dérogatoire → vérifier s'il est protégé ou voué à disparaître
- Restrictions de la Loi sur la protection du territoire agricole (LPTA) si zone verte

### 3.2 Physiquement possible

- Dimensions et forme du terrain permettent l'usage envisagé
- Topographie compatible (pente, drainage, géologie)
- Services publics disponibles (eau, égout, électricité, gaz)
- Accès depuis voie publique
- Contraintes environnementales (zones inondables, milieux humides, contamination)

### 3.3 Financièrement faisable

- L'usage génère un rendement supérieur au coût de développement
- Demande du marché existe pour cet usage dans ce secteur
- Financement disponible pour ce type d'usage
- Période d'absorption raisonnable

### 3.4 Maximalement productif

Parmi tous les usages satisfaisant les 3 critères précédents, l'usage qui génère la valeur foncière la plus élevée. C'est la conclusion finale de l'AMU.

---

## 4. Terrain vacant vs amélioration existante

### 4.1 Terrain vacant

Déterminer l'usage optimal du sol nu :
- Zone R-2 → AMU typique : unifamiliale ou duplex selon densité permise
- Zone commerciale → AMU typique : commerce de détail ou bureau
- Zone industrielle légère → AMU : entrepôt ou manufacture légère
- L'AMU guide directement le choix des comparables de terrains

### 4.2 Amélioration existante — deux analyses parallèles

**Analyse A — AMU du terrain seul** (comme si vacant)
**Analyse B — AMU du terrain avec l'amélioration existante**

Résultats possibles :
- A == B : l'amélioration correspond à l'AMU → évaluer tel quel (cas standard)
- A ≠ B : situation transitoire → évaluer selon l'AMU probable avec ajustement pour coûts de transition → documenter explicitement

Exemple A ≠ B : vieille maison résidentielle sur terrain en zone commerciale dense. L'UMPP est commercial, mais la maison subsiste. L'évaluateur documente la valeur de transition et les coûts de démolition/conversion.

---

## 5. Lien AMU → sélection des approches

| Type de bien | Méthode principale | Méthode secondaire | Note AMU |
|---|---|---|---|
| Unifamiliale | Comparaison | Coût | UMPP = résidentiel confirme comparaison |
| Condo divise | Comparaison | — | UMPP = résidentiel confirme |
| Duplex/Triplex | Comparaison | Revenu | UMPP guide type de comparables |
| Multilogement 4-6 | Revenu | Comparaison | UMPP valide usage locatif |
| Multilogement 7+ | Revenu | Comparaison | Idem |
| Commercial | Comparaison | Coût | UMPP commercial requis avant sélection |
| Industriel | Comparaison | Coût | UMPP industriel guide $/pi² |
| Terrain vacant | Comparaison terrains | — | UMPP = conclusion principale |
| Assurance | Coût seul | — | AMU non requise pour assurance |

---

## 6. Règles critiques et pièges

1. L'AMU doit être documentée même si l'usage actuel == UMPP — l'absence de documentation est une non-conformité.
2. Ne jamais conclure l'UMPP sans vérifier les 4 critères dans l'ordre — un usage illégal (ex: dérogatoire non protégé) ne peut pas être UMPP même s'il est physiquement possible.
3. Pour les terrains en zone agricole (LPTA) : l'usage agricole est le seul légalement permis sauf autorisation CPTAQ — documenter explicitement.
4. Un usage transitoire doit être évalué selon l'UMPP probable, pas selon l'usage actuel — erreur fréquente sanctionnée.
5. L'AMU influence directement le choix des comparables : comparables doivent refléter l'UMPP, pas l'usage actuel si différent.

---

## 7. Checklist de qualité

- [ ] Usage actuel documenté
- [ ] Les 4 critères évalués dans l'ordre (légal → physique → financier → productif)
- [ ] Usages alternatifs considérés et rejetés avec justification
- [ ] Terrain vacant analysé séparément si amélioration existante
- [ ] Conclusion UMPP explicite (usage retenu nommé)
- [ ] Lien UMPP → choix des approches documenté
- [ ] Lien UMPP → type de comparables documenté
- [ ] `umpp_differe_usage_actuel` correctement défini
- [ ] Restrictions légales vérifiées (zonage, LPTA si applicable)
