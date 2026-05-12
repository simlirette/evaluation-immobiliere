---
name: redaction-rapport-evaluation
description: >
  Rédiger le rapport d'évaluation complet conforme aux normes OEAQ :
  identification du bien, approches, réconciliation, hypothèses, certification.
type: redaction
agents:
  - redaction
sources:
  - fiche_bien
  - calculs_approche_comparative
  - calculs_approche_cout
  - calculs_approche_revenu
  - statut_sortie
  - normes_oeaq
---

## Objectif

Produire un brouillon de rapport d'évaluation structuré, professionnel et conforme aux normes OEAQ, prêt pour la révision et la signature de l'évaluateur agréé.

## Modèle de rapport — Forme complète

```markdown
# RAPPORT D'ÉVALUATION IMMOBILIÈRE
## BROUILLON NON CERTIFIÉ — Produit par assistant IA

> **AVERTISSEMENT :** Ce document est un brouillon préparé à titre d'aide à la
> rédaction. Il ne constitue pas un rapport d'évaluation certifié au sens des
> normes OEAQ et ne peut être utilisé à des fins légales, de financement ou de
> litige sans révision et signature d'un évaluateur agréé (É.A.) membre en
> règle de l'OEAQ.

---

## 1. Page de garde

| Champ | Valeur |
|-------|--------|
| Dossier | [ID] |
| Client | [Nom du client] |
| Adresse du bien | [Adresse complète] |
| Type de bien | [Type] |
| Objet du rapport | [Estimer la valeur marchande / JVM / etc.] |
| Usage prévu | [Financement / succession / vente / etc.] |
| Date de référence | [AAAA-MM-JJ] |
| Date de rédaction | [AAAA-MM-JJ] |
| Préparé par | [Nom É.A., numéro de membre OEAQ — À COMPLÉTER] |

---

## 2. Certification (à compléter par l'évaluateur)

Je soussigné(e), [NOM], évaluateur(trice) agréé(e), membre de l'OEAQ
(numéro : ______), certifie que :

- [ ] Je n'ai pas d'intérêt présent ou futur dans le bien évalué
- [ ] Mes honoraires ne sont pas conditionnels au résultat de l'évaluation
- [ ] L'analyse a été conduite avec objectivité et impartialité
- [ ] Les conclusions sont étayées par les données présentées dans ce rapport

Signature : _________________ Date : _________________

---

## 3. Identification du bien

### 3.1 Description et localisation

[Description du bien : adresse, secteur, voisinage, accessibilité]

### 3.2 Description physique

| Caractéristique | Détail | Source |
|----------------|--------|--------|
| Type de bâtiment | [type] | [source] |
| Superficie terrain | [X] m² | [source] |
| Superficie habitable | [X] m² | [source] |
| Nombre d'étages | [N] | [source] |
| Année de construction | [AAAA] | [source] |
| État général | [état] | Inspection |
| Zonage | [code] | [source] |

### 3.3 Situation juridique

- Propriétaire inscrit : [Nom]
- Lot cadastral : [matricule]
- Charges réelles : [liste ou "aucune connue"]

---

## 4. Définition de la valeur recherchée

**Type de valeur :** [Valeur marchande / Juste valeur marchande (JVM) / Valeur réelle LFM]

**Définition applicable :**
[Citer la définition légale ou jurisprudentielle pertinente selon le mandat]

**Date de référence :** [date]

---

## 5. Analyse du meilleur et meilleur usage (AMU)

### Terrain nu
[Quel serait le meilleur usage si le terrain était vacant ? Légalement permis, physiquement possible, financièrement faisable, maximalement productif.]

### Tel qu'amélioré
[Le bien actuel représente-t-il le meilleur usage ? Si non, analyser le potentiel de conversion.]

**Conclusion AMU :** [Conclusion en 1–2 phrases]

---

## 6. Approche(s) de valeur

### 6.1 Approche par comparaison directe

[Grille d'ajustements + indicateur de valeur]

**Indicateur — Approche comparative : [X $]**

### 6.2 Approche par le coût (si applicable)

[Valeur terrain + CRD]

**Indicateur — Approche par le coût : [X $]**

### 6.3 Approche par le revenu (si applicable)

[RBP, RNE, TGA, valeur]

**Indicateur — Approche par le revenu : [X $]**

---

## 7. Réconciliation et conclusion de valeur

[Motiver le poids accordé à chaque approche]

**VALEUR [MARCHANDE / JVM] ESTIMÉE À LA DATE DU [date] :**
# [X $]

---

## 8. Hypothèses et conditions limitatives

### Hypothèses ordinaires (standard)
- Le titre de propriété est sain et non litigieux
- Absence de contamination environnementale non divulguée
- Conformité aux codes du bâtiment et règlements municipaux
- Les informations fournies par le client sont réputées exactes

### Hypothèses extraordinaires (si applicable)
[Mentionner tout écart par rapport aux hypothèses ordinaires]

---

## 9. Annexes

- A. Fiches des comparables retenus
- B. Cartes de localisation
- C. Photos du bien (à insérer)
- D. Liste des sources et références documentaires
```

## Principes de rédaction

- **Clarté :** Chaque conclusion doit être compréhensible par un non-spécialiste
- **Traçabilité :** Chaque donnée doit référencer sa source entre parenthèses
- **Objectivité :** Présenter les éléments défavorables aussi bien que favorables
- **Conformité OEAQ :** Respecter la structure minimale requise par les NPP (mars 2025)
