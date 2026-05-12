---
name: recherche-registre-cadastre
description: >
  Recherche et extraction des informations cadastrales, foncieres et de droits
  de propriete applicables a l'evaluation immobiliere au Quebec. Utiliser ce
  skill pour les questions sur le cadastre, le registre foncier, les donnees
  publiques immobilieres, les droits reels et les mutations.
type: recherche
agents:
  - data-facts
  - comps-market
sources:
  - 21-cadastre-donnees
  - 22-droits-fonciers
---

# Skill : Recherche registre et cadastre

## 1. Role et contexte

Ce skill encode la connaissance complete sur le systeme d'information fonciere du Quebec et les standards internationaux d'evaluation massive, afin de soutenir le pipeline d'evaluation immobiliere. Il couvre :

- Les quatre registres publics du Quebec (Registre foncier, Cadastre, Greffe de l'arpenteur general, Registre du domaine de l'Etat)
- Le systeme de publicite fonciere et les droits reels
- Les sources de donnees publiques et ouvertes
- Les standards IAAO applicables a l'evaluation massive
- Les statistiques officielles du marche immobilier

L'agent qui utilise ce skill doit etre en mesure d'identifier, localiser et extraire toute information cadastrale, fonciere ou relative aux droits de propriete necessaire a une evaluation immobiliere au Quebec.

---

## 2. Connaissances encodees

### 2.1 Architecture des registres publics du Quebec

| Registre | Fonction | Operateur | Depuis |
|---|---|---|---|
| Registre foncier | Transactions immobilieres, droits sur les immeubles | Officier de la publicite fonciere (MRNF/Justice) | 1841 |
| Cadastre du Quebec | Representation sur plan des proprietes foncieres, numero de lot | MRNF | 1860 (renove depuis 1994) |
| Greffe de l'arpenteur general | Documents d'arpentage officiels | Arpenteur general du Quebec | -- |
| Registre du domaine de l'Etat | Terres publiques du gouvernement | MRNF | -- |

### 2.2 Numero de lot -- cle universelle

Le **numero de lot** est la cle d'acces commune qui relie :
- Le plan cadastral (forme, mesures, superficie)
- Le registre foncier (droits, transactions, historique)
- Le role d'evaluation municipale (valeur fonciere, categorie)
- Le compte de taxes municipal

**Seuil critique** : lots >= 1 000 000 = lots renoves (renovation cadastrale depuis 1994). Lots < 1 000 000 = anciens cadastres (paroisse, canton, circonscription fonciere requise).

### 2.3 Donnees cadastrales disponibles

| Donnee | Service gratuit (Infolot) | Service payant (Infolot) |
|---|---|---|
| Recherche par numero de lot, adresse, code postal | Oui | Oui |
| Forme et position du lot | Oui | Oui |
| Mesures (dimensions) | Non | Oui |
| Superficie et contenance | Non | Oui |
| Nom du proprietaire a la creation du lot | Non | Oui |
| Extraction vectorielle georeferencee | Non | Oui (logiciels SIG requis) |

### 2.4 Registre foncier -- contenu

- Historique complet des transactions depuis la creation de l'immeuble
- Transferts de propriete (vente, cession, donation, declaration de transmission)
- Hypotheques (conventionnelles, legales, de construction)
- Servitudes et droits de passage
- Declarations de copropriete
- Declarations de residence familiale
- Radiations (mainlevees)
- Copies certifiees de documents juridiques

**Acces** : compte client requis, frais selon grille tarifaire MRNF.

### 2.5 Index des immeubles et Index des noms

| Index | Contenu | Cle de recherche |
|---|---|---|
| Index des immeubles | Fiche immobiliere par lot : tous les actes lies a un immeuble immatricule | Numero de lot |
| Index des noms | Inscriptions avant 1860 + inscriptions ne pouvant etre dans l'Index des immeubles | Nom de la personne |

### 2.6 Types de droits reels

- **Propriete** : droit d'user, jouir et disposer d'un immeuble
- **Hypotheque** : surete grevant un immeuble pour garantir une obligation
- **Servitude** : charge imposee sur un immeuble (fonds servant) en faveur d'un autre (fonds dominant)
- **Droit de passage** : variete de servitude permettant l'acces
- **Copropriete** : division d'un immeuble en fractions
- **Residence familiale** : protection du lieu de residence familiale
- **Usufruit** : droit d'user et jouir temporairement d'un immeuble appartenant a un tiers

### 2.7 Publicite fonciere -- principes

1. L'inscription rend les droits **opposables a tous** (nul ne peut pretendre les ignorer)
2. La publicite **ne cree ni ne confere aucun droit** -- les droits naissent a la signature du contrat
3. L'Officier de la publicite fonciere doit agir avec **impartialite**
4. Le personnel n'est **pas autorise a exprimer un avis** sur un acte en preparation

**Cadre legislatif** :
- Code civil du Quebec, Livre IX (De la publicite des droits)
- Loi sur les bureaux de publicite des droits (L.R.Q., ch. B-9)
- Reglement sur la publicite fonciere (C.c.Q., r. 6)

### 2.8 Droit de mutation ("taxe de bienvenue")

Percu par les municipalites lors de tout transfert de propriete (vente, cession, declaration de transmission, donation).

### 2.9 Indice de difficultes financieres

| Type d'acte | Signification |
|---|---|
| Avis de vente pour impot foncier | Defaut de paiement des taxes municipales |
| Faillite | Declaration de faillite du proprietaire |
| Hypotheque de construction | Probleme de financement de construction |
| Preavis d'exercice | Defaut de paiement -- institution financiere entame des recours |
| Saisie | Saisie judiciaire de l'immeuble |

### 2.10 Statistiques officielles du marche immobilier

Produites mensuellement par le Registre foncier. Quatre indicateurs :
1. Nombre de ventes par plage de prix (< 250k$, 250k-500k$, > 500k$)
2. Nombre de transferts de propriete
3. Nombre d'hypotheques
4. Indice de difficultes financieres

**Regle de comptabilisation** : seul le premier droit apparaissant a l'acte est comptabilise.

**Decoupage regional** : 17 regions administratives. Region 10 (Nord-du-Quebec) redistribuee dans regions 02, 08 et 09. Les circonscriptions foncieres chevauchant plusieurs regions sont associees a celle comptant le plus de lots.

**Donnees ouvertes** : totalite sur Donnees Quebec (donneesquebec.ca), licence Creative Commons 4.0.

### 2.11 Sources de donnees pour l'evaluation

| Source | Donnees | Acces |
|---|---|---|
| Infolot (cadastre) | Forme, position, mesures, superficie | Gratuit (basique) / Payant (complet) |
| Registre foncier en ligne | Transactions, droits, historique, hypotheques | Payant (compte client) |
| Roles d'evaluation municipaux | Valeur fonciere, categorie, superficie | Variable selon municipalite |
| Donnees Quebec | Statistiques marche, roles evaluation, donnees ouvertes | Gratuit (CC 4.0) |
| Statistiques du Registre foncier | Ventes, transferts, hypotheques, difficultes | Gratuit (mensuel) |

### 2.12 Standards IAAO

Les standards IAAO sont **consultatifs et volontaires**. En cas de conflit, l'USPAP et les lois provinciales prevalent. Standards cles :

| Standard | Application |
|---|---|
| Mass Appraisal of Real Property | Evaluation massive |
| Automated Valuation Models (AVMs) | Modeles d'evaluation automatisee |
| Ratio Studies | Etudes de ratios evaluation/valeur marchande, COD, PRD |
| Data Quality | Collecte, verification, validation, precision |
| Verification and Adjustment of Sales | Fiabilite des comparables |
| Digital Cadastral Maps | Cartes cadastrales numeriques |
| Property Tax Policy | Politique fiscale immobiliere |
| International Property Measurement Standards | Mesure normalisee des batiments |

---

## 3. Methodologie de recherche

### Etape 1 -- Identification du bien

1. Obtenir le **numero de lot** via Infolot (recherche par adresse, code postal ou numero)
2. Verifier si le lot est **renove** (>= 1 000 000) ou non
3. Si lot non renove : identifier le nom du cadastre (paroisse, canton) et la circonscription fonciere
4. Extraire les donnees cadastrales de base : forme, mesures, superficie, position

### Etape 2 -- Extraction des droits fonciers

1. Consulter l'**Index des immeubles** du Registre foncier avec le numero de lot
2. Identifier tous les droits inscrits : propriete, hypotheques, servitudes, copropriete
3. Retracer l'historique des transferts de propriete et les prix de vente anterieurs
4. Verifier l'existence de declarations de residence familiale ou d'avis de difficultes financieres
5. Pour les immeubles anciens : consulter l'**Index des noms** (avant 1860)

### Etape 3 -- Collecte des donnees de marche

1. Extraire les **statistiques du Registre foncier** pour la region administrative visee
2. Identifier les tendances (variation des ventes, hypotheques, difficultes financieres)
3. Consulter les **donnees ouvertes** sur Donnees Quebec pour les roles d'evaluation et comparables
4. Croiser avec le role d'evaluation municipale (valeur fonciere, categorie d'immeuble)

### Etape 4 -- Validation et croisement

1. Verifier la coherence entre superficie cadastrale et superficie au role d'evaluation
2. Comparer les prix de vente inscrits au registre foncier avec les valeurs au role
3. Identifier les droits (servitudes, hypotheques) pouvant affecter la valeur
4. Contextualiser avec les statistiques regionales du marche

---

## 4. Regles critiques

### Interdictions

- **NE JAMAIS** confondre le cadastre avec un bornage -- le cadastre ne determine pas les limites de propriete
- **NE JAMAIS** considerer l'inscription au registre foncier comme creant un droit -- la publicite ne cree ni ne confere aucun droit
- **NE JAMAIS** se fier uniquement a l'Index des immeubles pour valider les titres -- un avis juridique professionnel peut etre requis
- **NE JAMAIS** extrapoler les statistiques de marche sans tenir compte du decoupage circonscription fonciere / region administrative
- **NE JAMAIS** appliquer les standards IAAO comme des obligations -- ils sont consultatifs et volontaires ; les lois provinciales prevalent

### Pieges courants

- **Lots non renoves** (< 1 000 000) : les donnees en ligne sont limitees. Faut le nom du cadastre + circonscription fonciere
- **Comptabilisation statistique** : la regle du "premier droit a l'acte" sous-estime le volume reel quand un acte contient plusieurs droits de meme nature
- **Region 10 (Nord-du-Quebec)** : n'apparait pas dans les statistiques regionales car ses donnees sont redistribuees dans les regions 02, 08 et 09
- **Declarations de copropriete** : un lot peut contenir plusieurs fractions, chacune ayant sa propre fiche
- **Hypotheques de construction** : font partie de l'indice de difficultes financieres, mais ne signifient pas necessairement un defaut

---

## 5. Checklist de qualite

- [ ] Le numero de lot a ete identifie et sa validite verifiee (lot renove ou ancien)
- [ ] Les donnees cadastrales de base ont ete extraites (forme, mesures, superficie)
- [ ] L'Index des immeubles a ete consulte pour les droits inscrits
- [ ] L'historique des transactions et les prix de vente anterieurs ont ete retracees
- [ ] Les charges affectant l'immeuble (hypotheques, servitudes) ont ete identifiees
- [ ] Les statistiques de marche regionales ont ete collectees et contextualisees
- [ ] Les donnees cadastrales et du role d'evaluation ont ete croisees pour coherence
- [ ] Les limites des donnees ont ete documentees (lots non renoves, decoupage regional)
- [ ] Aucune conclusion juridique n'a ete tiree sans mention de la necessite d'un avis professionnel
- [ ] Les sources de donnees sont citees avec leur niveau d'acces (gratuit/payant)
