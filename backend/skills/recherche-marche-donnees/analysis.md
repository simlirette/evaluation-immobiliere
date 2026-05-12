# Analyse — Données de marché, facteurs de rajustement et standards internationaux

> Synthèse exhaustive des sources de données de marché immobilier, des facteurs de rajustement au coût de base (MEFQ), des standards IAAO de vérification et ajustement des ventes, et des standards internationaux de mesure immobilière (IPMS).

---

## 1. Sources de données de marché au Québec

### 1.1 Sources publiques

| Source | Contenu | Accès | Fréquence |
|--------|---------|-------|-----------|
| Registre foncier du Québec | Transactions, prix de vente, hypothèques, transferts | Payant (compte client) | Continu |
| Statistiques du Registre foncier | Ventes par plage de prix, transferts, hypothèques, indice difficultés | Gratuit (Données Québec) | Mensuel |
| Rôles d'évaluation municipaux | Valeur foncière, CUBF, superficie, année construction | Variable selon municipalité | Triennal (cycle de rôle) |
| Données Québec (donneesquebec.ca) | Rôles d'évaluation, statistiques marché, données ouvertes | Gratuit (CC 4.0) | Variable |
| Infolot (cadastre MRNF) | Forme, position, mesures, superficie des lots | Gratuit (basique) / Payant (complet) | Continu |

### 1.2 Sources privées et professionnelles

| Source | Contenu | Accès |
|--------|---------|-------|
| JLR (Registre foncier enrichi) | Données transactionnelles enrichies, analyses de marché | Abonnement |
| Centris / APCIQ | Ventes résidentielles via courtiers, statistiques MLS | Abonnement / Partenariat |
| Firmes d'évaluation (données internes) | Comparables, rapports antérieurs, bases de données propriétaires | Interne |
| Services d'enrichissement OCR | Numérisation et extraction de données de documents | Variable |

### 1.3 Priorités de documentation des fournisseurs

Pour chaque fournisseur de données, documenter :
- Conditions d'utilisation et licences
- Restrictions de redistribution
- Dictionnaires de champs (définitions des variables)
- Fréquence de mise à jour
- Provenance des données
- Limites connues
- SLA ou taux d'erreur documenté
- Politiques de conservation

---

## 2. Facteurs de rajustement au coût de base — Système MEFQ

Les bulletins annuels des facteurs de rajustement font partie intégrante du système de rajustements au coût de base prévu par le MEFQ, aux fins de l'application de la méthode du coût. Ils sont publiés par le MAMH (Direction générale de la fiscalité et de la transition climatique).

### 2.1 Règle fondamentale

**Aucun facteur ne peut être utilisé individuellement, ni être appliqué à un coût de base autre que ceux obtenus à l'aide des barèmes de coûts unitaires figurant au MEFQ.** Tous les facteurs s'appliquent conjointement à la date de référence indiquée, avec les autres facteurs que doit établir l'évaluateur.

### 2.2 Cinq catégories de facteurs

#### 2.2.1 Facteur de temps

Rajustement temporel du coût de base pour refléter l'évolution des coûts de construction.

| Usage | Facteur 2025 | Facteur 2006 (référence) |
|-------|-------------|------------------------|
| Résidentiel | 3,00 | 1,32 |
| Multirésidentiel typique | 2,80 | — |
| Multirésidentiel atypique | 3,00 | — |
| Agricole | 3,06 | 1,50 |
| Commercial | 2,76 | 1,37 |
| Industriel | 2,52 | 1,37 |
| Institutionnel | 3,06 | 1,31 |

#### 2.2.2 Facteur de taxes de vente

Rajustement pour la composante taxes de vente (TPS/TVQ) applicable selon le type de bâtiment.

**Édition modernisée (2025)** :
- Tout bâtiment : 1,00
- 1 ou 2 logements (selon valeur de la contrepartie) : échelle de 1,08 à 1,15
  - Moins de 204 000 $ : 1,10
  - 204 000 $ à 219 000 $ : 1,11
  - 219 000 $ à 236 000 $ : 1,08
  - 236 000 $ à 256 000 $ : 1,12
  - 256 000 $ à 280 000 $ : 1,09
  - 280 000 $ à 364 000 $ : 1,15
  - 364 000 $ à 418 000 $ : 1,13
  - 418 000 $ et plus : 1,14
- Résidence secondaire : 1,15
- 3 logements ou plus : 1,10
- 4 logements et plus (éligible crédit TPS fédéral) : 1,06

**Édition 2006** :
- Catégories commerciale, industrielle : 1,00
- Catégories institutionnelles : 1,00 à 1,12 selon sous-catégorie
- Habitation : 1,11 à 1,14 selon plage de valeur

#### 2.2.3 Facteur d'envergure

Rajustement selon la taille du bâtiment (superficie ou coût neuf).

**Édition modernisée (2025)** — Non résidentiel, par superficie :
| Superficie | Facteur |
|-----------|---------|
| Moins de 615 m² | 1,35 |
| 615 à 1 799,9 m² | 1,30 |
| 1 800 à 2 399,9 m² | 1,20 |
| 2 400 à 3 299,9 m² | 1,15 |
| 3 300 à 7 999,9 m² | 1,10 |
| 8 000 m² et plus | 1,05 |

**Édition 2006** — Par coût neuf :
| Coût neuf | Facteur |
|-----------|---------|
| Moins de 500 000 $ | — |
| 500 000 $ à 1,5 M $ | — |
| 1,5 M $ à 2,5 M $ | — |
| 2,5 M $ à 12 M $ | — |
| 12 M $ à 30 M $ | — |
| 30 M $ à 50 M $ | — |
| 50 M $ et plus | — |
| ou : Analyse individuelle | Réf. |

Note : Les facteurs spécifiques varient selon l'année et doivent être établis par l'évaluateur pour les éditions 2006.

#### 2.2.4 Facteur de classe

Rajustement selon la classe de qualité de construction (1 à 9).

| Classe | Résidentiel 2025 | Multirés. typique 2025 | Commercial 2025 | Industriel 2025 | Institutionnel 2025 |
|--------|-----------------|----------------------|----------------|----------------|-------------------|
| 1 | 1,30 | 1,45 | 1,35 | 1,35 | 1,35 |
| 2 | 1,15 | 1,35 | 1,20 | 1,20 | 1,20 |
| 3 | 1,10 | 1,10 | 1,10 | 1,10 | 1,10 |
| 4 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| 5 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| 6 | 0,85 | 0,95 | 0,90 | 0,90 | 0,90 |
| 7 | 0,75 | 0,85 | 0,75 | 0,75 | 0,75 |
| 8 | 0,65 | 0,75 | 0,70 | 0,70 | 0,70 |
| 9 | 0,60 | 0,65 | 0,60 | 0,60 | 0,60 |

#### 2.2.5 Facteur économique

Rajustement pour les conditions économiques locales. **À établir par l'évaluateur** selon les conditions du marché local. Les bulletins identifient les catégories nécessitant un facteur économique mais le facteur lui-même relève de l'analyse de l'évaluateur.

**Édition 2006** — Facteurs économiques industriels établis pour constructions dont le coût neuf est compris entre 1,5 M $ et 32 M $ :
- Coût neuf 1,5 à 12 M $ : 1,00
- Coût neuf 12 à 32 M $ : 1,05

### 2.3 Évolution des bulletins

- **Édition 2006** : Bulletins annuels de 2006 à 2016. Structure par volumes (Vol. 4 résidentiel, Vol. 5 non résidentiel). Codes distinctifs A à F par usage.
- **Édition modernisée** : Bulletins annuels de 2013 à 2025. Structure simplifiée, catégories mises à jour. Usage du terme « multirésidentiel typique/atypique ».

### 2.4 Usage institutionnel — Sous-catégories

| # | Sous-catégorie | Facteur temps 2025 | Facteur classe |
|---|---------------|-------------------|---------------|
| 1 | Commercial | 2,76 | Variable |
| 2 | Industriel | 2,52 | Variable |
| 3 | Enseignement primaire ou secondaire | — | 1,00 |
| 4 | Enseignement post-secondaire | — | 1,07 |
| 5 | Soins de santé et services sociaux | — | 1,00 |
| 6 | Gouvernemental | — | 1,07 |
| 7 | Municipal ou supramunicipal | — | 1,00 |
| 8 | Autre usage institutionnel | — | 1,07 |

---

## 3. Standard IAAO — Vérification et ajustement des ventes

Standard révisé approuvé en avril 2020 par l'IAAO. Consultatif et volontaire — en cas de conflit avec les lois provinciales, ces dernières prévalent.

### 3.1 Principes fondamentaux

1. Système d'enregistrement numérique pour stocker les données de transferts, questionnaires de vérification et entrevues de suivi
2. Collecte administrée de manière cohérente et opportune, aussi complète et exacte que possible
3. Vérification effectuée de manière opportune, uniforme et transparente
4. Ajustements effectués pour représenter uniquement la valeur du bien immobilier transféré, de manière cohérente, transparente et documentée
5. Résultats documentés rapidement, de manière exhaustive, stockés préférablement en format électronique

### 3.2 Sources de données de ventes

#### 3.2.1 Documents de transfert immobilier

Types principaux :
- **Acte de garantie générale** (general warranty deed) : plus haute protection pour l'acheteur
- **Acte de garantie spéciale** (special warranty deed) : garantie limitée à la période de propriété du vendeur
- **Acte de vente à prix débattu** (bargain and sale deed) : propriété affirmée mais sans garantie de titre
- **Acte de renonciation** (quitclaim deed) : moins protecteur, transfère seulement les droits existants
- **Acte de vente pour taxes** (tax deed) : transfert suite à vente pour taxes impayées
- **Acte du shérif** (sheriff deed) : transfert suite à saisie judiciaire
- **Acte de fiducie** (trust deed) : transfert à un fiduciaire, 3 parties (emprunteur, fiduciaire, prêteur)
- **Contrat de vente à tempérament** (land contract) : titre retenu par vendeur jusqu'à paiement complet

#### 3.2.2 Questionnaires de vérification des ventes

Déclarations affirmées ou assermentées concernant la vente. Un questionnaire plus complet limite le besoin de vérification de suivi.

#### 3.2.3 Parties à la vente et sources tierces

Sources tierces importantes :
- Services inter-agences (MLS)
- Sociétés de titres
- Institutions financières
- Agences de location
- Gestionnaires immobiliers
- Courtiers et agences immobilières
- Évaluateurs gouvernementaux et privés
- Avocats
- Organisations d'évaluation

### 3.3 Collecte de données — Informations utiles

#### 3.3.1 Informations de vente et d'acte

Éléments essentiels :
- **Considération complète** : montant total payé (acompte + montants financés)
- **Date de transfert** : date de clôture (pas la date d'enregistrement)
- **Description légale, adresse, identifiant parcellaire** : lien avec les dossiers de l'évaluateur
- **Noms des acheteurs et vendeurs** : identification des parties
- **Type de transfert** : indicateur de validité de la vente
- **Numéro d'instrument** : localisation dans les registres
- **Numéro de vente unique** : prévient la duplication

#### 3.3.2 Conditions de transaction

- **Intérêt transféré** : pleine propriété (fee simple) vs intérêt partiel
- **Type et modalités de financement** : acompte, type de prêt, taux d'intérêt, amortissement
- **Relation entre acheteur et vendeur** : parties liées = transaction potentiellement non représentative
- **Méthode de mise en marché** : courtier, enchère, FSBO, internet, journal, appel d'offres, bouche-à-oreille
- **Durée d'exposition au marché** : trop longue ou trop courte = non représentatif

#### 3.3.3 Caractéristiques du bien

- **Usage du bien** : résidentiel vs commercial, type d'occupation
- **Plus haute et meilleure utilisation** : ne pas présumer que le prix reflète l'usage actuel
- **Biens meubles** : type et valeur des biens meubles inclus dans le prix
- **Localisation GIS** : géocodage pour analyse spatiale

### 3.4 Vérification des ventes

**Principe directeur** : toutes les ventes sont candidates comme ventes valides sauf si des informations suffisantes démontrent le contraire.

**Délai recommandé** : vérification dans les 3 mois suivant la vente.

#### 3.4.1 Méthodes de vérification

1. **Questionnaires par courrier** : moins coûteux mais réponse différée
2. **Entrevues téléphoniques** : réponse rapide, clarification immédiate
3. **Entrevues en personne** : plus coûteuses mais plus fiables, moins de refus
4. **Méthodes analytiques** : ratios atypiques identifiés par seuils (< 50 %, > 150 %) ou techniques géostatistiques

#### 3.4.2 Ventes généralement considérées invalides

| Type | Raison |
|------|--------|
| Ventes impliquant des agences gouvernementales | Élément de compulsion possible |
| Ventes impliquant des organismes caritatifs/religieux/éducatifs | Élément de philanthropie |
| Ventes impliquant une institution financière comme acheteur | Souvent en lieu de forclusion |
| Ventes impliquant une institution financière comme vendeur | Prix typiquement bas (motivé à vendre) |
| Ventes entre personnes liées | Transaction non ouverte au marché |
| Ventes pour succession | Prix non représentatif si pressé |
| Ventes forcées par ordonnance judiciaire | **Jamais valides** pour calibration ou études de ratios |
| Ventes de titre douteux | Incertitude juridique |

**Exception institution financière comme vendeur** : potentiellement valide si ces ventes représentent > 20 % du marché dans une juridiction.

#### 3.4.3 Conditions spéciales

- Ventes à conditions spéciales (enchères absolues vs avec réserve)
- Acquisitions/cessions par grands propriétaires
- Échanges IRC Section 1031
- Propriétaires contigus
- Cession-bail (leaseback)
- Ventes à découvert (short sales)

#### 3.4.4 Vérification des baux commerciaux

- Questionnaires de vérification de bail accompagnant les questionnaires de vente
- Comparer le loyer contractuel au loyer du marché (brut)
- Convertir les loyers nets en loyers bruts pour comparaison
- Terme résiduel < 3 ans : le prix peut refléter le loyer du marché
- Seuils : si écart significatif entre loyer contractuel et loyer du marché → ajustement requis

### 3.5 Ajustements au prix de vente

**Ordre des ajustements** :
1. Ajustements transactionnels (convertir le prix en valeur marchande à la date de vente)
2. Ajustements pour isoler le bien immobilier imposable (soustraire biens meubles, etc.)
3. Ajustements temporels (différence entre date de vente et date d'analyse)

#### 3.5.1 Ajustements transactionnels

| Type | Ajustement |
|------|-----------|
| Frais de clôture de l'acheteur (payés par le vendeur) | Soustraire du prix de vente |
| Taxes impayées (payées par l'acheteur) | Ajouter au prix de vente |
| Financement (taux hors marché) | Calculer la valeur actualisée de la différence de paiements |
| Commission immobilière | **Pas d'ajustement** sauf si payée par l'acheteur (alors ajouter) |

**Financement — Sous-types** :
- Hypothèques assumées (taux hors marché) : calculer la VA de la différence de paiements mensuels
- Programmes de subvention : soustraire le montant du don du prix de vente
- Points payés par le vendeur : soustraire la valeur des points
- Financement par le vendeur : si taux < marché → soustraire VA différence ; si taux > marché → ajouter VA différence

#### 3.5.2 Ajustements pour conditions du bien

| Type | Ajustement |
|------|-----------|
| Baux à long terme (loyers hors marché) | VA de la différence entre flux de loyers contractuels et du marché |
| Biens meubles | Soustraire la valeur contributive des biens meubles |
| Allocation de réparations | Soustraire si bien non réparé à la date d'évaluation |
| Cotisations spéciales | Variable |

**Seuils pour biens meubles** :
- Résidentiel : si > 10 % du prix → exclure la vente
- Commercial/industriel : si > 25 % du prix → exclure la vente

**Baux à long terme** :
- Seuil minimum : bail de 3 ans ou plus
- Si loyer contractuel > loyer du marché : soustraire la VA de la différence du prix
- Si loyer contractuel < loyer du marché : ajouter la VA de la différence au prix
- Utiliser le taux d'actualisation approprié par usage et durée résiduelle

#### 3.5.3 Ajustements temporels

- Programme de suivi des variations de niveaux de prix dans le temps
- Ajustements basés sur l'analyse de marché, non arbitraires
- Appliquer après les ajustements transactionnels et de condition

### 3.6 Ventes multiples parcelles

- Vérifier si les parcelles sont contiguës
- Déterminer s'il s'agit d'une ou plusieurs unités économiques
- Unités économiques multiples → généralement exclure
- Comparer la somme des valeurs évaluées au prix de vente total

---

## 4. Standard IPMS — Mesure immobilière internationale

International Property Measurement Standards: All Buildings (janvier 2023), publié par la coalition IPMSC (88 organisations dont l'IAAO).

### 4.1 Objectif

Créer une approche uniforme et internationale de mesure des bâtiments. Applicable à tous les types de bâtiments indépendamment de leur usage ou occupation.

### 4.2 Applications

- Analyse et benchmarking
- Financement immobilier
- Ratios de coûts de construction
- Gestion immobilière
- Conversion entre standards de mesure
- Recherche
- Allocation de coûts
- Estimation sommaire de coûts
- Assurance
- Durabilité et efficacité énergétique
- Planification et architecture
- Évaluation / transactions (location et vente)
- Développement immobilier

### 4.3 Structure des standards IPMS

Trois groupements fondamentaux :

| Standard | Type | Description |
|----------|------|-------------|
| IPMS 1 | Externe, bâtiment entier ou partiel | Mesure externe du bâtiment |
| IPMS 2 | Interne, bâtiment entier ou partiel | Mesure interne du bâtiment |
| IPMS 3.1 | Externe, occupation exclusive | Mesure externe pour occupation exclusive |
| IPMS 3.2 | Interne, occupation exclusive | Mesure interne pour occupation exclusive |
| IPMS 4.1 | Interne, zones sélectionnées incluant murs intérieurs et colonnes | Mesure interne incluant murs/colonnes |
| IPMS 4.2 | Interne, zones sélectionnées excluant murs extérieurs et colonnes | Mesure interne excluant murs/colonnes extérieurs |

### 4.4 Concepts clés

- **Face dominante interne** (Internal Dominant Face) : point de référence pour la mesure interne
- **Zones à usage limité** (Limited Use Areas) : zones avec restrictions de hauteur ou d'usage
- **Hauteur** : critère de classification des zones mesurables
- **Fenêtres en baie** (Bay Windows) : règles spécifiques de mesure
- **Surface de plancher externe** (External Floor Area) : mesure depuis l'extérieur des murs
- **Limite notionnelle** (Notional Boundary) : limite fictive pour mesure
- **Zone abritée** (Sheltered Area) : zones couvertes mais non fermées
- **Mur mitoyen** (Demising Wall) : mur séparant des espaces d'occupation différente

### 4.5 Zones composantes (Component Areas)

L'utilisation des zones composantes est optionnelle mais facilite l'analyse du bâtiment et la conversion entre standards IPMS et autres standards de mesure.

---

## 5. Indicateurs statistiques de marché

### 5.1 Indicateurs IAAO pour études de ratios

| Indicateur | Signification | Seuil acceptable |
|-----------|--------------|-----------------|
| COD (Coefficient of Dispersion) | Uniformité de l'évaluation | ≤ 15 % résidentiel, ≤ 20 % commercial |
| PRD (Price-Related Differential) | Progressivité/régressivité | 0,98 à 1,03 |
| Proportion médiane | Ratio médian évaluation/prix de vente | 0,95 à 1,05 |

### 5.2 Statistiques du Registre foncier du Québec

Quatre indicateurs publiés mensuellement :
1. Nombre de ventes par plage de prix (< 250 000 $, 250 000 $ à 500 000 $, > 500 000 $)
2. Nombre de transferts de propriété (tous types)
3. Nombre d'hypothèques inscrites
4. Indice de difficultés financières (avis de vente, faillites, préavis d'exercice, saisies)

**Règle de comptabilisation** : seul le premier droit apparaissant à l'acte est comptabilisé → sous-estimation du volume réel.

**Découpage** : 17 régions administratives. Région 10 (Nord-du-Québec) redistribuée dans régions 02, 08, 09.

---

## 6. Processus de collecte et validation des données de marché

### 6.1 Collecte

1. Identifier les sources disponibles (publiques et privées) pour le marché visé
2. Extraire les transactions pertinentes (période, localisation, type de bien)
3. Documenter la provenance, les conditions d'accès et les limites de chaque source
4. Constituer un fichier de ventes avec toutes les informations requises

### 6.2 Vérification

1. Vérifier chaque vente selon les critères IAAO (conditions de transaction, intérêt transféré, financement)
2. Identifier et exclure les ventes non représentatives (parties liées, forcées, gouvernementales)
3. Attribuer des codes de raison pour les ventes valides et invalides
4. Documenter le processus de vérification

### 6.3 Ajustement

1. Appliquer les ajustements dans l'ordre prescrit (transactionnels → condition → temporels)
2. Appliquer les facteurs de rajustement MEFQ pour la méthode du coût
3. Documenter chaque ajustement et sa justification
4. Utiliser les tables d'intérêts composés pour les ajustements de financement

### 6.4 Validation croisée

1. Comparer les données de ventes avec les valeurs au rôle d'évaluation
2. Vérifier la cohérence entre sources (registre foncier vs données privées)
3. Identifier les ratios atypiques (< 50 %, > 150 %) pour investigation
4. Contextualiser avec les statistiques régionales du marché

---

## 7. Pièges et limites

### 7.1 Données de marché

- Les données du registre foncier ne contiennent pas toujours le prix réel (considération nominale)
- La règle du premier droit à l'acte sous-estime le volume réel des transactions
- Les données MLS/Centris ne couvrent pas toutes les transactions (ventes privées exclues)
- Les rôles d'évaluation reflètent une date de référence passée (cycle triennal)

### 7.2 Facteurs de rajustement

- Les facteurs du bulletin MEFQ ne peuvent être utilisés isolément
- Les facteurs de classe et d'envergure varient significativement — une erreur de classification a un impact majeur
- Le facteur économique doit être établi par l'évaluateur selon les conditions locales
- Les éditions 2006 et modernisée utilisent des structures différentes — ne pas mélanger

### 7.3 Standards IAAO

- Consultatifs et volontaires — les lois provinciales et CUSPAP/NPP prévalent
- Les seuils de ratios (COD, PRD) sont des guides, non des normes contraignantes
- La méthodologie de vérification est conçue pour l'évaluation massive, pas nécessairement pour l'évaluation unitaire
- Les exemples d'ajustement utilisent des taux et tables américains — adapter au contexte québécois

### 7.4 Mesure IPMS

- Standard international qui peut différer des pratiques locales de mesure
- La conversion entre IPMS et standards locaux nécessite les zones composantes
- Ne remplace pas les exigences de mesure spécifiques du MEFQ ou des normes professionnelles locales
