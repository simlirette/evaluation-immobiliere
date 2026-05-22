---
name: recherche-npp-appel-offres
description: >
  Normes, processus et exigences pour les mandats d'evaluation obtenus par appel
  d'offres public ou prive : cahier des charges, conformite contractuelle, balises
  de honoraires, livrables attendus, exigences de qualification et obligations de
  divulgation specifiques. Utiliser ce skill pour tout mandat soumis a une procedure
  d'appel d'offres ou de contrat cadre avec un donneur d'ordre institutionnel.
type: recherche
agents:
  - compliance-qa
  - data-facts
sources:
  - 04-oeaq-normes
  - 00-cuspap
  - 05-oeaq-reglements
dependencies:
  - recherche-normes-professionnelles
  - recherche-cadre-legal
---

# Skill : Recherche NPP — Mandats par appel d'offres

## 1. Role et contexte

Ce skill encode les regles professionnelles et contractuelles applicables aux mandats d'evaluation obtenus via des processus d'appel d'offres (AO) — publics ou prives. Il couvre les specificites de :

- **Appels d'offres publics** : municipalites, gouvernements, organismes publics (SEAO, AMP)
- **Appels d'offres prives** : institutions financieres (portefeuilles hypothecaires), fonds immobiliers, societes de gestion
- **Contrats-cadres** (panels d'evaluateurs)
- **Mandats de masse** (evaluations multiples dans une meme operation)

Ces mandats presentent des exigences specifiques de conformite — les obligations professionnelles restent integres independamment des contraintes contractuelles.

---

## 2. Connaissances encodees

### 2.1 Cadre reglementaire des contrats publics au Quebec

| Loi / Reglement | Champ d'application | Seuils AO publics |
|----------------|--------------------|--------------------|
| **Loi sur les contrats des organismes publics (LCOP)** | Ministeres, organismes, etablissements publics | Services prof. : > 100 000 $ |
| **Reglement sur les contrats de services (RCS)** | Details LCOP pour les contrats de services | Precisions sur les criteres |
| **AMP (Autorite des marches publics)** | Surveillance des contrats publics | Plaintes, enquetes |
| **SEAO (Systeme electronique d'appel d'offres)** | Diffusion des AO publics au Quebec | Obligatoire si > 100 000 $ |
| **LCOP municipale (Loi 122 et reglement municipal)** | Municipalites | Variable par municipalite |

### 2.2 Structure d'un appel d'offres pour services d'evaluation

Un cahier des charges type pour services d'evaluation contient :

| Section | Contenu habituel |
|---------|-----------------|
| **Description du mandat** | Type d'evaluation, proprietes visees, usage du rapport |
| **Qualifications requises** | Designation (AACI, CRA), experience, references |
| **Exigences de livraison** | Delai, format, nombre d'exemplaires |
| **Normes applicables** | CUSPAP, NPP OEAQ, normes specifiques (ex. SCHL pour hypothecaire) |
| **Prix et honoraires** | Taux horaire, taux unitaire, structure d'honoraires |
| **Confidentialite** | Clauses NDA, restriction de divulgation |
| **Criteres d'evaluation des offres** | Ponderation prix/qualite technique |
| **Conditions contractuelles** | Responsabilite, assurance, indemnisation |

### 2.3 Obligations professionnelles non susceptibles de derogation contractuelle

Les obligations professionnelles suivantes **s'appliquent independamment des clauses contractuelles** :

| Obligation | Source | Non-derogeable |
|-----------|--------|---------------|
| Independance professionnelle | Art. 9 Code deo., CUSPAP 5.12 | Oui |
| Interdiction remuneration conditionnelle | Art. 29-31 Code deo., CUSPAP 5.12 | Oui |
| Secret professionnel (sauf AO obligation legale) | Art. 51-55 Code deo. | Oui |
| Conservation des dossiers (5 ans OEAQ, 7 ans CUSPAP) | C-26 r. 133, CUSPAP 5.8 | Oui |
| Contenu obligatoire du rapport | NPP Norme 2, CUSPAP 7-8 | Oui |
| Signature par le preparateur | Art. 41 Code deo. | Oui |
| Portee de pratique (AACI vs CRA) | CUSPAP 5.4 | Oui |

**Principe** : Une clause contractuelle qui contreviendrait aux obligations professionnelles de l'evaluateur est inopposable.

### 2.4 Gestion des conflits d'interets dans les AO institutionnels

Les mandats en serie (portefeuilles, panels) augmentent le risque de conflits d'interets :

| Risque | Manifestation | Mesure requise |
|--------|--------------|---------------|
| Interet financier dans l'immeuble | Part dans la propriete, pret hypothecaire | Divulgation au client + retrait si necessaire |
| Relation avec une partie | Courtier, vendeur, acheteur, pret | Divulgation ecrite avant acceptation |
| Evaluations contradictoires | Meme immeuble, valeurs divergentes | Justification documentee |
| Pression commerciale | Volume d'affaires avec le donneur d'ordre | Independance a maintenir malgre la relation |

### 2.5 Honoraires en contexte d'AO

#### Interdiction de remuneration conditionnelle (sauf consultation)

Il est **formellement interdit** d'accepter un mandat d'evaluation (non-consultation) si la remuneration est conditionnelle a :
- Un resultat de valeur specifique
- Une direction de valeur (plus haut ou plus bas)
- L'approbation du preteur
- L'emission d'un permis ou d'une approbation quelconque

#### Structure d'honoraires permises

| Structure | Permise | Conditions |
|-----------|---------|-----------|
| Taux horaire | Oui | Sans condition liee au resultat |
| Forfait par rapport | Oui | Sans condition liee au resultat |
| Forfait par type de propriete | Oui | Tarif etabli avant connaissance de la valeur |
| Bonus sur volume | Oui (avec precaution) | Independance non affectee |
| Bonus si valeur atteint un seuil | Non | Interdit — conditionnelle au resultat |
| % de la valeur (success fee) | Non sauf consultation | Interdit pour evaluation |

#### Honoraires dans les AO publics (LCOP)

- L'offre de prix doit etre precise avant la signature du contrat
- Aucune majoration sans avenant approuve
- Taux de remuneration proposes peuvent etre verifies par l'AMP

### 2.6 Exigences de qualification dans les AO

| Qualification | AO hypothecaire (banques) | AO public municipal | AO gouvernemental |
|--------------|--------------------------|--------------------|--------------------|
| Designation minimum | AACI ou CRA si residentiel | AACI generalement | AACI |
| Experience minimale | 3-5 ans | 5-10 ans selon complexite | Variable |
| References exigees | 3-5 mandats similaires | 3-5 references verifiees | Selon cahier des charges |
| Assurance E&O | 1 M$/3 M$ minimum | Variable (souvent superieur) | Variable |
| Formation specifique | SCHL si mandat SCHL | Variable | Variable |

### 2.7 Livrables et formats attendus

| Type de donneur d'ordre | Format attendu | Normes specifiques |
|------------------------|---------------|-------------------|
| Institution financiere (hypothecaire) | Formulaire prescrit + recertification | CUSPAP 7.1.7 (drive-by), SCHL si assure |
| SCHL (assurance pret) | Formulaire SCHL specifique | Exigences de qualification SCHL |
| Organisme public (evaluation fonciere) | Rapport selon MEFQ + dossier de propriete | NPP Normes 19-22, MEFQ |
| Fonds immobilier / REIF | Narratif complet + model Excel | CUSPAP 8 + standard reporting |
| Succession / partage | Narratif complet | NPP Norme 1, CUSPAP 8 |
| Litige / tribunal | Narratif complet + CV expert | NPP Norme 1 + Code de procedure civile |

### 2.8 Delais et livrables dans les AO

Les AO fixent des delais contractuels. L'evaluateur doit :
- Verifier la faisabilite des delais avant de soumissionner
- Signaler rapidement tout risque de retard
- Ne pas sacrifier la qualite pour respecter le delai

**Principes** :
- Un delai contractuel ne peut forcer la production d'un rapport non conforme
- Si le delai est incompatible avec un travail competent : refuser le mandat ou negocier le delai

---

## 3. Methodologie de recherche

### Etape 1 — Analyser le cahier des charges

Identifier :
- Les obligations contractuelles conformes aux normes professionnelles
- Les clauses pouvant creer un conflit avec les obligations professionnelles
- Les exigences de qualification et les criteres d'evaluation

### Etape 2 — Verifier la conformite professionnelle

Comparer les exigences contractuelles avec :
- NPP OEAQ (normes coercitives et directives)
- CUSPAP 2026 (sections 4-13)
- Code de deontologie OEAQ

Identifier les clauses problematiques et les signaler.

### Etape 3 — Evaluer les risques de conflits d'interets

Pour chaque mandat :
- Verifier tout interet direct ou indirect dans les proprietes visees
- Verifier les relations avec les parties impliquees
- Documenter les conflits identifies et les decisions prises

### Etape 4 — Structurer l'offre de services

Preparer une offre conforme :
- Honoraires non conditionnels au resultat
- Qualifications documentees
- Delais realistes et garantis
- Format de rapport conforme aux normes

---

## 4. Regles critiques

1. **JAMAIS** soumettre une offre d'honoraires conditionnel au resultat de l'evaluation
2. **JAMAIS** accepter une clause contractuelle qui entrainerait une violation des normes professionnelles
3. **TOUJOURS** maintenir l'independance professionnelle, meme avec un donneur d'ordre recurrent
4. **TOUJOURS** divulguer par ecrit tout conflit d'interets avant l'acceptation du mandat
5. **TOUJOURS** conserver les dossiers selon les normes (5 ans OEAQ, 7 ans CUSPAP) — independamment des dispositions contractuelles sur la remise des dossiers
6. Un delai contractuel ne justifie pas un rapport non conforme — refuser ou negocier le delai
7. Le volume d'affaires avec un donneur d'ordre ne doit pas compromettre l'independance
8. Les exigences de format et de livrables doivent etre compatibles avec les normes de rapport
9. L'AO public peut exiger la transmission de donnees a des tiers — verifier la compatibilite avec le secret professionnel
10. Pour les mandats SCHL : verifier les exigences specifiques de qualification SCHL en sus des normes OEAQ/AIC

---

## 5. Checklist de qualite

- [ ] Cahier des charges analyse pour les clauses non conformes aux normes professionnelles
- [ ] Conflits d'interets verifies et documentes
- [ ] Structure d'honoraires verifiee : non conditionnelle au resultat
- [ ] Qualifications verifiees : designation, assurance, experience
- [ ] Delais evalues comme realistes et compatibles avec un travail competent
- [ ] Format de rapport conforme aux normes (NPP Norme 2, CUSPAP 7)
- [ ] Clauses de confidentialite verifiees : compatibles avec le secret professionnel
- [ ] Obligations de conservation des dossiers maintenues independamment du contrat
- [ ] Clauses de responsabilite evaluees (limitation de responsabilite compatible avec les normes)
- [ ] Rapport signe par son preparateur (art. 41 Code deo.)
```

---