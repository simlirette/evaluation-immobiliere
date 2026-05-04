# Analyse — Registre foncier, cadastre et données immobilières

> Synthèse exhaustive du système d'information foncière du Québec, des registres publics, des sources de données immobilières et des standards IAAO applicables à l'évaluation immobilière.

---

## 1. Architecture du système d'information foncière du Québec

Le Québec dispose de quatre registres publics complémentaires formant le système d'information foncière :

### 1.1 Registre foncier

Le registre foncier compile toutes les transactions immobilières réalisées au Québec depuis 1841. Il est opéré par l'Officier de la publicité foncière (ministère des Ressources naturelles et des Forêts / Justice).

**Contenu** :
- Historique complet des transactions depuis la création de l'immeuble
- Transferts de propriété (vente, cession, donation, déclaration de transmission)
- Hypothèques (conventionnelles, légales, de construction)
- Servitudes et droits de passage
- Déclarations de copropriété
- Déclarations de résidence familiale
- Radiations (mainlevées)
- Copies certifiées de documents juridiques

**Accès** : Registre foncier du Québec en ligne, compte client requis, frais selon grille tarifaire du MRNF.

**Utilisations pour l'évaluateur** :
- Retracer l'historique des transactions effectuées sur un immeuble depuis sa création
- Vérifier avant l'achat d'une propriété (prix de vente antérieur, noms des propriétaires, hypothèques légales)
- Consulter les documents contenant les droits inscrits (transferts, charges, radiations)
- Obtenir une copie certifiée d'un document juridique
- Inscrire une transaction pour officialiser et publiciser tout nouveau droit

### 1.2 Cadastre du Québec

Registre public présenté sous forme de plan qui illustre les propriétés foncières du Québec en leur attribuant un numéro de lot. Opéré par le MRNF.

**Fonction** : représentation sur plan des propriétés foncières, attribution du numéro de lot.

**Rénovation cadastrale** : processus de modernisation entamé en 1994 pour remplacer les anciens cadastres (paroisses, cantons, circonscriptions foncières) par un cadastre unique et unifié.

**Distinction critique** :
- Lots rénovés : numéro ≥ 1 000 000
- Lots non rénovés : numéro < 1 000 000 → nécessitent le nom du cadastre et la circonscription foncière pour la recherche

**Données disponibles via Infolot** :

| Donnée | Consultation gratuite | Consultation payante |
|--------|----------------------|---------------------|
| Recherche par numéro de lot, adresse, code postal | Oui | Oui |
| Forme et position du lot sur le plan | Oui | Oui |
| Mesures (dimensions du lot) | Non | Oui |
| Superficie et contenance | Non | Oui |
| Nom du propriétaire à la création du lot | Non | Oui |
| Extraction vectorielle géoréférencée (SIG) | Non | Oui |

**Limite importante** : si un lot n'a pas fait l'objet de la rénovation cadastrale, il ne sera pas possible de le localiser directement sur le plan dans Infolot.

### 1.3 Greffe de l'arpenteur général du Québec

Registre public qui consigne tous les documents préparés sous l'autorité de l'arpenteur général du Québec. Contient les documents d'arpentage officiels.

### 1.4 Registre du domaine de l'État

Registre public qui présente sous forme de carte interactive l'information foncière relative aux terres du gouvernement. Opéré par le MRNF.

---

## 2. Publicité foncière — Principes fondamentaux

Le système de publicité foncière du Québec repose sur des principes établis par le Code civil du Québec (Livre IX — De la publicité des droits).

### 2.1 Principes

1. **Opposabilité** : l'inscription au registre rend les droits opposables à tous (nul ne peut prétendre les ignorer)
2. **Non-création de droits** : la publicité ne crée ni ne confère aucun droit — les droits naissent à la signature du contrat
3. **Impartialité** : l'Officier de la publicité foncière doit agir avec impartialité
4. **Neutralité** : le personnel n'est pas autorisé à exprimer un avis sur un acte en préparation

### 2.2 Cadre législatif

- Code civil du Québec, Livre IX (De la publicité des droits)
- Loi sur les bureaux de publicité des droits (L.R.Q., ch. B-9)
- Règlement sur la publicité foncière (C.c.Q., r. 6)

### 2.3 Index des immeubles et Index des noms

| Index | Contenu | Clé de recherche | Période |
|-------|---------|-----------------|---------|
| Index des immeubles | Fiche immobilière par lot : tous les actes liés à un immeuble immatriculé | Numéro de lot | Depuis immatriculation |
| Index des noms | Inscriptions avant 1860 + inscriptions ne pouvant être dans l'Index des immeubles | Nom de la personne | Avant 1860 |

---

## 3. Numéro de lot — Clé universelle du système

Le **numéro de lot** est la clé d'accès commune qui relie l'ensemble des registres et bases de données :

- **Plan cadastral** : forme, mesures, superficie du lot
- **Registre foncier** : droits, transactions, historique de propriété
- **Rôle d'évaluation municipale** : valeur foncière, catégorie d'immeuble, superficie
- **Compte de taxes municipal** : obligations fiscales

### Seuil de distinction

- Lots ≥ 1 000 000 = lots rénovés (rénovation cadastrale depuis 1994) → recherche directe par numéro
- Lots < 1 000 000 = anciens cadastres → nécessitent le nom du cadastre (paroisse, canton) et la circonscription foncière

---

## 4. Types de droits réels

### 4.1 Droits principaux

| Droit | Définition | Impact sur la valeur |
|-------|-----------|---------------------|
| **Propriété** | Droit d'user, jouir et disposer d'un immeuble | Base de l'évaluation |
| **Hypothèque** | Sûreté grevant un immeuble pour garantir une obligation | Charge financière, peut indiquer difficultés |
| **Servitude** | Charge imposée sur un fonds servant en faveur d'un fonds dominant | Diminution potentielle de valeur |
| **Droit de passage** | Variété de servitude permettant l'accès | Affecte l'usage et la valeur |
| **Copropriété** | Division d'un immeuble en fractions | Évaluation par fraction |
| **Résidence familiale** | Protection du lieu de résidence familiale | Restriction à la disposition |
| **Usufruit** | Droit d'user et jouir temporairement d'un immeuble appartenant à un tiers | Démembrement affectant la valeur |

### 4.2 Actes inscrits au registre

- Transferts de propriété (vente, cession, donation, déclaration de transmission)
- Hypothèques conventionnelles, légales et de construction
- Servitudes et droits de passage
- Déclarations de copropriété
- Déclarations de résidence familiale
- Radiations (mainlevées d'hypothèques, etc.)
- Baux de plus de 3 ans (publicité obligatoire)

---

## 5. Indice de difficultés financières

Les données du Registre foncier permettent de calculer un indice de difficultés financières basé sur les types d'actes suivants :

| Type d'acte | Signification |
|-------------|--------------|
| Avis de vente pour impôt foncier | Défaut de paiement des taxes municipales |
| Faillite | Déclaration de faillite du propriétaire |
| Hypothèque de construction | Problème potentiel de financement de construction |
| Préavis d'exercice | Défaut de paiement — institution financière entame des recours |
| Saisie | Saisie judiciaire de l'immeuble |

**Attention** : les hypothèques de construction font partie de l'indice mais ne signifient pas nécessairement un défaut — elles peuvent être normales dans le cycle de construction.

---

## 6. Statistiques officielles du marché immobilier

Produites mensuellement par le Registre foncier du Québec, disponibles en données ouvertes.

### 6.1 Quatre indicateurs

1. **Nombre de ventes** par plage de prix (< 250 000 $, 250 000 $ à 500 000 $, > 500 000 $)
2. **Nombre de transferts de propriété** (tous types confondus)
3. **Nombre d'hypothèques** inscrites
4. **Indice de difficultés financières** (avis de vente, faillites, préavis, saisies)

### 6.2 Règle de comptabilisation

Seul le premier droit apparaissant à l'acte est comptabilisé. Cette règle sous-estime le volume réel quand un acte contient plusieurs droits de même nature.

### 6.3 Découpage régional

- 17 régions administratives du Québec
- **Région 10 (Nord-du-Québec)** : n'apparaît pas dans les statistiques régionales car ses données sont redistribuées dans les régions 02 (Saguenay–Lac-Saint-Jean), 08 (Abitibi-Témiscamingue) et 09 (Côte-Nord)
- Les circonscriptions foncières chevauchant plusieurs régions sont associées à celle comptant le plus de lots

### 6.4 Données ouvertes

Totalité des statistiques disponibles sur Données Québec (donneesquebec.ca) sous licence Creative Commons 4.0.

---

## 7. Sources de données pour l'évaluation immobilière

| Source | Données disponibles | Accès | Utilité pour l'évaluateur |
|--------|-------------------|-------|--------------------------|
| **Infolot (cadastre)** | Forme, position, mesures, superficie des lots | Gratuit (basique) / Payant (complet) | Identification du terrain, superficie |
| **Registre foncier en ligne** | Transactions, droits, historique, hypothèques | Payant (compte client) | Chaîne de titres, ventes antérieures |
| **Rôles d'évaluation municipaux** | Valeur foncière, catégorie, superficie, CUBF | Variable selon municipalité | Valeur inscrite, comparaison |
| **Données Québec** | Statistiques marché, rôles évaluation, données ouvertes | Gratuit (CC 4.0) | Tendances, analyses de marché |
| **Statistiques du Registre foncier** | Ventes, transferts, hypothèques, difficultés | Gratuit (mensuel) | Indicateurs de marché |
| **Greffe de l'arpenteur général** | Documents d'arpentage officiels | Consultation publique | Vérification des limites |
| **Registre du domaine de l'État** | Terres publiques, carte interactive | Gratuit | Identification du domaine public |

---

## 8. Rôles d'évaluation foncière municipale

Les rôles d'évaluation foncière sont des registres publics tenus par les municipalités contenant la valeur foncière de chaque propriété pour fins de taxation.

### 8.1 Contenu du rôle

- Numéro matricule de l'unité d'évaluation
- Description et localisation de l'immeuble
- Valeur inscrite au rôle (terrain + bâtiment)
- Catégorie d'immeuble (résidentiel, commercial, industriel, agricole, etc.)
- Code d'utilisation des biens-fonds (CUBF)
- Superficie du terrain et du bâtiment
- Année de construction
- Propriétaire inscrit

### 8.2 Accès aux données

Les rôles d'évaluation sont accessibles de diverses manières selon les municipalités :
- Consultation en ligne sur le site municipal
- Données ouvertes via Données Québec
- Demande directe à la municipalité ou à l'évaluateur municipal

---

## 9. Standards IAAO — Évaluation massive et données

Les standards de l'International Association of Assessing Officers (IAAO) sont **consultatifs et volontaires**. En cas de conflit avec les lois provinciales ou les normes CUSPAP/NPP, ces dernières prévalent.

### 9.1 Standards applicables

| Standard | Objet | Application en évaluation |
|----------|-------|--------------------------|
| **Mass Appraisal of Real Property** | Processus d'évaluation massive | Évaluation municipale, rôle foncier |
| **Automated Valuation Models (AVMs)** | Modèles d'évaluation automatisée | Outils de préfiltrage, validation |
| **Ratio Studies** | Études de ratios évaluation/valeur marchande | COD, PRD, proportion médiane |
| **Data Quality** | Collecte, vérification, validation, précision des données | Assurance qualité des données |
| **Verification and Adjustment of Sales** | Fiabilité et ajustement des données de ventes | Sélection des comparables |
| **Digital Cadastral Maps** | Cartes cadastrales numériques | SIG, cartographie |
| **Property Tax Policy** | Politique fiscale immobilière | Contexte fiscal |
| **Assessment Appeal** | Processus d'appel en évaluation | Recours, contestation |
| **Communications and Outreach** | Communication avec le public | Relations contribuables |
| **Contracting for Assessment Services** | Mandats d'évaluation | Gestion de mandats |

### 9.2 International Property Measurement Standards (IPMS)

Standard global développé par une coalition de 88 organisations immobilières (incluant l'IAAO). Standard ouvert conçu pour créer une approche uniforme de mesure des bâtiments. Applicable à tous les types de bâtiments.

### 9.3 Indicateurs statistiques IAAO

| Indicateur | Signification | Seuil acceptable |
|-----------|--------------|-----------------|
| **COD** (Coefficient of Dispersion) | Mesure de l'uniformité de l'évaluation | ≤ 15 % résidentiel, ≤ 20 % commercial |
| **PRD** (Price-Related Differential) | Mesure de la progressivité/régressivité | 0,98 à 1,03 |
| **Proportion médiane** | Ratio médian évaluation/prix de vente | 0,95 à 1,05 |

---

## 10. Processus de recherche foncière pour l'évaluateur

### 10.1 Identification du bien

1. Obtenir le numéro de lot via Infolot (recherche par adresse, code postal ou numéro)
2. Vérifier si le lot est rénové (≥ 1 000 000) ou non
3. Si lot non rénové : identifier le cadastre (paroisse, canton) et la circonscription foncière
4. Extraire les données cadastrales : forme, mesures, superficie, position

### 10.2 Extraction des droits

1. Consulter l'Index des immeubles du Registre foncier avec le numéro de lot
2. Identifier tous les droits inscrits : propriété, hypothèques, servitudes, copropriété
3. Retracer l'historique des transferts et les prix de vente antérieurs
4. Vérifier les déclarations de résidence familiale et avis de difficultés financières
5. Pour les immeubles anciens : consulter l'Index des noms (avant 1860)

### 10.3 Collecte des données de marché

1. Extraire les statistiques du Registre foncier pour la région administrative visée
2. Identifier les tendances (variation des ventes, hypothèques, difficultés financières)
3. Consulter les données ouvertes sur Données Québec pour les rôles et comparables
4. Croiser avec le rôle d'évaluation municipale

### 10.4 Validation et croisement

1. Vérifier la cohérence entre superficie cadastrale et superficie au rôle d'évaluation
2. Comparer les prix de vente inscrits au registre foncier avec les valeurs au rôle
3. Identifier les droits (servitudes, hypothèques) pouvant affecter la valeur
4. Contextualiser avec les statistiques régionales du marché

---

## 11. Pièges et limites

### 11.1 Confusion fréquentes

- Le **cadastre** ≠ **bornage** : le cadastre ne détermine pas les limites de propriété sur le terrain
- L'**inscription** au registre foncier ≠ **création de droits** : la publicité rend opposable mais ne crée rien
- La **valeur inscrite au rôle** ≠ **valeur marchande** : appliquer le facteur comparatif du rôle

### 11.2 Limites des données

- Lots non rénovés : données en ligne limitées, recherche plus complexe
- Comptabilisation statistique : sous-estimation du volume réel (règle du premier droit à l'acte)
- Région 10 : invisible dans les statistiques régionales (redistribuée)
- Copropriétés : un lot peut contenir plusieurs fractions avec fiches distinctes
- Standards IAAO : consultatifs uniquement, les lois provinciales et CUSPAP/NPP prévalent toujours
- Les données du registre foncier antérieures à 1841 sont incomplètes ou inexistantes
