---
name: recherche-npp-jvm
description: >
  Normes et methodologie pour la determination de la juste valeur marchande (JVM)
  en contexte fiscal, successoral, entre actionnaires et aux fins de fiscalite
  corporative. Utiliser ce skill pour les mandats JVM hors evaluation fonciere
  ordinaire : reorganisation, succession, divorce, financement, litige.
type: recherche
agents:
  - data-facts
  - valuation-draft
  - compliance-qa
sources:
  - 04-oeaq-normes
  - 00-cuspap
  - 16-droit-immobilier
dependencies:
  - recherche-normes-professionnelles
---

# Skill : Recherche NPP — Juste valeur marchande (JVM)

## 1. Role et contexte

Ce skill encode les regles professionnelles, methodologiques et contextuelles applicables aux mandats de determination de la juste valeur marchande (JVM) en contexte non routinier. Il couvre les principales situations ou la JVM s'ecarte des modalites standard de l'evaluation fonciere ou hypothecaire :

- Fiscalite corporative (reorganisation, don, actionnaires)
- Succession et partage du patrimoine familial
- Divorce et separation (partage de la residence)
- Litige (dommages, actions en responsabilite, separation actionnaires)
- Financement specialise (mezzanine, fonds propres)
- Droit de retrait (copropriete indivise, actionnaires)

Ta mission : fournir aux agents valuation-draft et compliance-qa les regles de definition, de methodologie et de divulgation applicables a ces mandats specifiques.

---

## 2. Connaissances encodees

### 2.1 Definition de la JVM (fiscalite canadienne)

La **juste valeur marchande (JVM)** au sens fiscal canadien est :

> Le prix le plus eleve, en argent ou en equivalent monetaire, qu'un bien pourrait atteindre sur un marche libre entre des parties independantes ayant chacune toutes les informations pertinentes, agissant librement et sans contrainte.

Source : Agence du revenu du Canada (ARC), IT-170R, Interpretation Bulletin E-2.

Differences cles avec la **valeur reelle** (art. 43 LFM) :
- La JVM est une notion fiscale federale; la valeur reelle est une notion fiscale municipale quebecoise
- La JVM peut s'appliquer a la date d'un evenement fiscal specifique (don, transfert, reorganisation)
- Les hypotheses de base sont similaires mais le contexte d'application differe

### 2.2 Contextes d'application de la JVM

| Contexte | Loi / Reference | Particularites |
|----------|----------------|----------------|
| Don de biens immobiliers | LIR art. 69, 248 | JVM au moment du don; presomption de disposition |
| Roulement 85(1) | LIR art. 85 | JVM minimale pour les biens transferes |
| Achat-vente entre actionnaires | LIR art. 84, 84.1 | Eviter le dividende repute |
| Succession | LCC, LIR art. 70(5) | JVM a la date du deces (presomption de disposition) |
| Divorce / partage | CCQ art. 417, 422 | JVM a la date de la demande ou de la vente |
| Droit de retrait (copropriete indivise) | CCQ art. 1022 | JVM de la quote-part |
| Expropriation | Loi E-25 | Valeur marchande (proche JVM mais cadre distinct) |
| Evaluation aux fins de litige | NPP Normes 1, 5 | Consultation ou evaluation formelle |

### 2.3 Methodologie JVM — immobilier

La determination de la JVM immobiliere suit les memes methodes que l'evaluation standard (comparaison, revenu, cout), mais avec des precisions contextuelles :

#### Differences methodologiques cles

| Element | Evaluation standard | JVM fiscale |
|---------|-------------------|-------------|
| Date | Date de reference du role | Date de l'evenement fiscal |
| Marche | Marche local actuel | Marche libre, hypothetique si retroactif |
| Hypotheses | Conditions courantes | Peut necessiter hypotheses extraordinaires |
| Usage | UMPP ou usage actuel | UMPP au sens fiscal |
| Rapport | Narratif ou formulaire | Toujours narratif complet pour litige/fiscal |

#### Methodes privilegiees par type d'immeuble

| Type d'immeuble | Methode privilegiee | Methodes complementaires |
|-----------------|--------------------|-----------------------|
| Residentiel libre | Comparaison directe | Cout si neuf/special |
| Immeuble a revenus | Revenu (MRB/TGA) | Comparaison |
| Commercial | Comparaison + revenu | Cout si special |
| Industriel | Cout + comparaison | Revenu si location possible |
| Terrain vague | Comparaison | Residuelle si developpement |

### 2.4 Facteurs specifiques JVM

#### A. JVM en contexte de succession (art. 70(5) LIR)

- La JVM doit etre etablie **a la date du deces** — evaluation retrospective
- Marche tel qu'il existait a cette date
- Toutes donnees contemporaines de la date de deces
- Hypotheses extraordinaires si l'immeuble a ete vendu depuis

#### B. JVM en reorganisation corporative

- L'evaluateur peut etre amene a evaluer des droits partiels (actions, hypotheques)
- Decote pour illiquidite possible (si marche restreint)
- Coordination avec fiscaliste pour les consequences

#### C. JVM en copropriete indivise — droit de retrait

- Evaluer la quote-part de l'indivis (pas l'immeuble entier)
- Decote possible pour absence de controle (co-indivisaire minoritaire)
- Documenter la structure juridique de l'indivision

### 2.5 Regles NPP applicables

#### Norme 1 — L'acte d'evaluation

Regles coercitives specifiquement pertinentes :
- **Regle 1.1** : Aucune erreur ayant portee significative
- **Regle 1.2, el. 3** : But et definition de la valeur — preciser JVM et sa source juridique
- **Regle 1.2, el. 4** : Date d'evaluation = date de l'evenement fiscal, pas la date du rapport
- **Regle 1.2, el. 6** : Reserves et hypotheses extraordinaires si evaluation retrospective
- **Regle 1.2, el. 12** : Plus d'une methode sauf circonstances justifiant le contraire

#### Norme 5 — Consultation

Si le mandat est une consultation fiscale (pas une evaluation formelle) :
- Regle 5.1 (COERCITIVE) : etudes dont le but n'est pas d'estimer la valeur
- L'evaluateur peut donner une opinion sur l'adequation d'une valeur utilisee
- Raisonnement condition : raisonnement fiscal (impot a payer) vs valeur marchande intrinseque

### 2.6 Contenu obligatoire du rapport JVM

En plus du contenu standard de la Norme 2 (rapport narratif complet), un rapport JVM doit inclure :

1. **Definition exacte de la JVM retenue** (reference fiscale, jurisprudence si applicable)
2. **Date d'evaluation** distincte de la date de rapport (si retrospective)
3. **Evenement fiscal declencheur** (don, deces, transfert, divorce, etc.)
4. **Hypotheses extraordinaires** si etat de l'immeuble a la date d'evaluation inconnu
5. **Utilisation prevue du rapport** (declaration fiscale, negociation, litige)
6. **Utilisateur autorise** nomme explicitement (contribuable, succession, avocat, ARC si applicable)
7. **Restrictions d'utilisation** claires
8. **Ventes anterieures du sujet** < 3 ans avant la date effective

### 2.7 Jurisprudence fiscale — JVM immobiliere

| Decision | Principe retenu |
|----------|----------------|
| **Gold Seal Salmon** | La JVM est une question de fait — expertise d'evaluateurs requis |
| **Bibby** | Methode de comparaison privilegiee quand donnees suffisantes |
| **Cadillac Fairview** | Approche revenu pour immeubles commerciaux de qualite investissement |
| **ARC — Interpretation Bulletin IT-170R** | Definition de la JVM; parties independantes; absence de contrainte |

---

## 3. Methodologie de recherche

### Etape 1 — Identifier le contexte fiscal/juridique

Determiner :
- L'evenement declencheur (deces, don, vente, reorganisation, divorce)
- La date de l'evaluation (date de l'evenement, pas la date du rapport)
- La loi applicable (LIR federale, CCQ, etc.)
- L'utilisateur du rapport et son but

### Etape 2 — Choisir la definition de la valeur

- JVM fiscale federale (LIR) : definition ARC
- Valeur marchande (CCQ, divorce) : definition CCQ
- Valeur au sens de la Loi E-25 (expropriation) : cadre distinct
- Preciser dans le rapport la definition retenue et sa source

### Etape 3 — Collecte de donnees historiques (si retrospectif)

- Transactions comparables autour de la date de l'evenement
- Conditions du marche a la date de l'evenement (indices, publications)
- Etat physique de l'immeuble a la date de l'evenement (photos, dossiers, inspections anterieures)

### Etape 4 — Application des methodes

- Appliquer au moins deux methodes d'evaluation
- Si une methode est ecartee : justifier explicitement
- Reconcilier en une opinion de JVM unique

### Etape 5 — Redaction du rapport

- Format : toujours narratif complet pour mandats fiscaux ou litigieux
- Preciser les hypotheses extraordinaires
- Identifier nommement les utilisateurs autorises
- Inclure les restrictions d'utilisation

---

## 4. Regles critiques

1. **TOUJOURS** utiliser la date de l'evenement fiscal comme date d'evaluation — pas la date du rapport
2. **TOUJOURS** definir la JVM retenue en citant sa source juridique
3. **TOUJOURS** nommer les utilisateurs autorises (ARC, avocats, parties a un litige)
4. **JAMAIS** utiliser le rapport pour un usage non prevu sans autorisation ecrite du client
5. **JAMAIS** confondre JVM fiscale federale et valeur reelle municipale (art. 43 LFM)
6. **JAMAIS** accepter une remuneration conditionnelle au resultat (sauf consultation avec divulgation)
7. Pour les evaluations retrospectives : documenter les sources disponibles a la date de l'evenement
8. En copropriete indivise : evaluer la quote-part, pas l'immeuble entier sans decote
9. En contexte de litige : le rapport peut etre soumis a un expert adverse — exigence de rigueur maximale
10. Toujours verifier si un rapport de consultation (Norme 5) est plus approprie qu'une evaluation formelle

---

## 5. Checklist de qualite

- [ ] L'evenement fiscal declencheur est identifie et documente
- [ ] La definition exacte de la JVM retenue est citee avec sa source
- [ ] La date d'evaluation correspond a la date de l'evenement (pas la date du rapport)
- [ ] Les utilisateurs autorises sont nommes explicitement
- [ ] L'usage autorise est clairement defini
- [ ] Au moins deux methodes d'evaluation sont appliquees ou le rejet est justifie
- [ ] Les hypotheses extraordinaires sont documentees (evaluation retrospective)
- [ ] Les ventes anterieures du sujet (< 3 ans) sont analysees
- [ ] Les restrictions d'utilisation sont incluses dans le rapport
- [ ] Le format de rapport est narratif complet (si fiscal ou litigieux)
- [ ] Les donnees sont contemporaines de la date d'evaluation
- [ ] La JVM federale n'est pas confondue avec la valeur reelle municipale
```

---