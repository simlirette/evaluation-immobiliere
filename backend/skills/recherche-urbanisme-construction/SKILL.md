---
name: recherche-urbanisme-construction
description: >
  Analyser le zonage, les règlements d'urbanisme, les permis de construction
  et les contraintes physiques affectant le potentiel de développement et la valeur.
type: recherche
agents:
  - data-facts
sources:
  - reglements_municipaux
  - permis_construction
  - pafio
  - schema_amenagement
---

## Objectif

Déterminer l'usage légal permis, les contraintes physiques et réglementaires, et leur impact sur la valeur du bien.

## 1. Zonage et usages permis

**Source :** Règlement de zonage municipal + PAFIO (Plan d'affectation du territoire)

**Informations à extraire :**
- Code de zone (ex : R-1, CM-3, I-2)
- Usages permis principaux (résidentiel unifamilial, commercial de détail, industriel léger)
- Usages complémentaires et accessoires permis
- Usages dérogatoires protégés (non conformes mais légalement maintenus)

**Restrictions dimensionnelles :**
- Superficie minimale du lot
- Frontage minimal (largeur de façade)
- Coefficient d'occupation du sol (COS) — ratio surface plancher / superficie terrain
- Coefficient d'emprise au sol (CES) — % du terrain pouvant être couvert
- Hauteur maximale (nombre d'étages ou mètres)
- Reculs obligatoires (avant, latéraux, arrière)
- Densité résidentielle (logements / hectare)

**Impact valeur :**
- Bien sous-utilisé par rapport à son potentiel maximum → valeur terrain peut dominer
- Bien sur-densifié (non conforme) → risque de non-renouvellement

### Analyse du meilleur et meilleur usage (AMU)

**Critères AMU (4 tests obligatoires) :**
1. **Légalement permis** : Le zonage permet-il l'usage envisagé ?
2. **Physiquement possible** : La configuration du lot le permet-elle ?
3. **Financièrement faisable** : L'usage génère-t-il une valeur supérieure au coût ?
4. **Maximalement productif** : Parmi les usages faisables, lequel maximise la valeur ?

**AMU terrain nu** : Quel est le meilleur usage si le terrain était vide ?
**AMU tel qu'amélioré** : Les améliorations existantes représentent-elles le meilleur usage ?

Si AMU tel qu'amélioré ≠ AMU terrain nu → analyse de démolition / conversion potentielle.

## 2. Permis de construction et historique

**Source :** Service d'urbanisme municipal (accès en personne ou en ligne selon la municipalité)

**Permis à vérifier :**
- Permis de construction originaux (date, entrepreneur, description travaux)
- Permis d'agrandissement ou de transformation
- Permis de démolition (le cas échéant)
- Certificats d'occupation / conformité

**Signaux d'alerte :**
- Agrandissements sans permis → non-conformité → risque légal
- Changement d'usage non autorisé
- Travaux refusés dans le passé → contrainte physique ou réglementaire

## 3. Contraintes physiques et environnementales

**Zones à risque :**
- Zone inondable (100 ans, 20 ans) — PMAD, carte des zones inondables MELCC
- Zone de glissement de terrain — carte de stabilité MRNF
- Zone de bruit (aéroport, autoroute) — Plan d'exposition au bruit (PEB)
- Présence d'un cours d'eau → bande riveraine 10–15 m inconstructible (PPRLPI)

**Servitudes d'utilité publique :**
- Lignes haute tension Hydro-Québec (dépréciation selon distance)
- Emprise de pipeline (OPG, Énergir)
- Réseaux d'aqueduc et d'égout (servitudes de passage)

## 4. Synthèse impact sur la valeur

```
BIEN CONFORME AU ZONAGE :
→ Pas d'ajustement négatif requis
→ Analyser le potentiel de densification si sous-utilisé

BIEN NON CONFORME (dérogatoire protégé) :
→ Dépréciation fonctionnelle si les améliorations ne peuvent être reconstruites
→ Note dans les conditions limitatives : "L'usage actuel est non conforme mais maintenu"

TERRAIN EN ZONE À RISQUE :
→ Dépréciation selon nature et gravité du risque
→ Hypothèse extraordinaire si risque non quantifié
→ Recommander évaluation environnementale si nécessaire
```
