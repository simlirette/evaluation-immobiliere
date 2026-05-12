# Synthese exhaustive - Extraction des faits immobiliers

---

## 1. Architecture des donnees immobilieres

Le processus d'evaluation fonciere municipale au Quebec repose sur quatre fichiers permanents complementaires :

### 1.1 Fichier des mutations immobilieres (2A)

Instrument fondamental de prise de decision pour l'evaluation fonciere. Constitue la banque de donnees du marche. Contient tous les actes translatifs de propriete (ventes, donations, partages, successions, retrocessions). Les renseignements relatifs aux ventes doivent etre conserves minimalement quatre ans (RREF, art. 3). Toutes les transactions immobilieres y sont codifiees selon le prefixe FM, avec 14 groupes de renseignements prescrits.

Les cinq categories de mutation :

| Code | Nom | Description |
|------|-----|-------------|
| 1 | Vente d'une unite complete existante | Totalite d'une unite d'evaluation |
| 2 | Vente d'une unite d'evaluation a creer | Nouvelle subdivision a l'origine de la transaction |
| 3 | Vente de plusieurs unites d'evaluation | Transaction visant plus d'une unite |
| 4 | Vente d'une partie d'une unite d'evaluation | Agrandissement ou diminution d'une unite |
| 5 | Non-vente | Cessions, jugements, partages, corrections |

### 1.2 Systeme d'information geographique (2B)

Reference spatiale de toutes les unites d'evaluation. Contient les donnees cartographiques et georeferenciees necessaires a la localisation precise des immeubles sur le territoire.

### 1.3 Dossiers de propriete (2C)

Ensemble structure de renseignements propres a chaque unite d'evaluation. Caractere permanent, transcende la duree triennale des roles. Constitue par trois types de renseignements, organises en blocs numerotes de *00 a *99. Fonction : contenir les renseignements pertinents pour etablir la valeur, demontrer une connaissance objective des immeubles, et assurer la perennite des donnees.

### 1.4 Fichier des unites de voisinage (2D)

Regroupement geographique des unites d'evaluation presentant des caracteristiques similaires du point de vue du marche immobilier. Chaque unite d'evaluation est rattachee a une unite de voisinage identifiee par un numero distinctif.

---

## 2. Types d'immeubles

Six types d'immeubles distincts, determines par un cheminement decisionnel prescrit :

### 2.1 Terrains

- **Terrain general** : Tout terrain qui n'est pas agricole ou boise. Majoritairement en zone urbaine, semi-urbaine ou de villegiature. Superficie generalement inferieure a 20 000 m2. Sert d'assiette aux batiments.
- **Terrain agricole ou boise** : Compris dans une exploitation agricole enregistree (EAE) OU d'une superficie excedant 20 000 m2, principalement boisee ou a usage agricole.

### 2.2 Batiments

- **Batiment residentiel** : Principalement destine a l'habitation, au plus 5 logements/chambres locatives/locaux non residentiels, au plus 3 etages dans sa partie la plus elevee.
- **Batiment multiresidentiel** : Principalement destine a l'habitation, au moins 6 logements/chambres locatives/locaux non residentiels, destine a generer des revenus de location immobiliere.
- **Batiment agricole** : Principalement destine a l'agriculture, avec ses dependances.
- **Batiment non residentiel** : Ne correspond pas aux trois types precedents. Principalement commercial, industriel ou institutionnel. Peut inclure batiments residentiels ou agricoles aux caracteristiques exceptionnelles.

### 2.3 Cheminement decisionnel

Pour les terrains : EAE? -> Si non, superficie > 20 000 m2? -> Si oui, principalement agricole ou boise? -> Terrain agricole ou boise / Terrain general.

Pour les batiments : Principalement residentiel? -> Si oui, au plus 5 logements? -> Si oui, au plus 3 etages? -> Batiment residentiel. Si non a l'une des conditions et genere des revenus de location -> Batiment multiresidentiel. Si principalement agricole -> Batiment agricole. Sinon -> Batiment non residentiel.

---

## 3. Structure du dossier de propriete

### 3.1 Trois types de renseignements

**Renseignements administratifs (blocs *00 a *03)** : Identification, classification et traitement du dossier a des fins administratives ou fiscales. Concernent la totalite de l'unite d'evaluation. Aucun lien avec les methodes d'evaluation, mais essentiels dans la procedure fiscale.

- Bloc *00 : Identification (designation cadastrale, coordonnees diverses, adresse)
- Bloc *01 : Renseignements generaux
- Bloc *02 : Identification du proprietaire
- Bloc *03 : Historique

**Renseignements descriptifs (blocs *04 a *89)** : Caracteristiques de tout immeuble compris dans l'unite. Visent distinctement le terrain et chaque batiment principal avec ses dependances. Different selon les types d'immeubles. Requis aux fins de l'application des methodes d'evaluation.

**Resultats d'evaluation (blocs *90 a *99)** : Conclusions de l'application du processus d'evaluation. Concernent la totalite de l'unite. Decoulent de l'application des methodes et actes professionnels.

### 3.2 Codification universelle par bloc

Systeme de codification a deux chiffres (*00 a *99), 100 blocs possibles. Chaque bloc regroupe des elements de nature ou fonction similaire. Numerotation ordonnancee logiquement. Inspire du systeme UNIFORMAT II.

### 3.3 Les 11 familles de blocs de renseignements descriptifs

| Plage | Famille | Composantes visees |
|-------|---------|-------------------|
| *04 | Terrains | Bloc *04 General ou *04 Agricole (un seul a la fois) |
| *05 a *09 | Renseignements globaux sur le batiment | Photo, croquis, dimensions de base, renseignements generaux |
| *11 a *19 | Infrastructure | Murs de fondations, assises, composantes construites dans le sol |
| *21 a *29 | Structure et enveloppe | Charpente, murs exterieurs, toit |
| *31 a *39 | Finitions interieur | Cloisons, plafonds, finis de planchers, cuisines |
| *41 a *49 | Services au batiment | Ascenseurs, plomberie, chauffage, climatisation, electricite, systemes de protection |
| *51 a *59 | Equipements lies aux activites | Equipements integres (aspirateur central, foyer, etageres d'entreposage) |
| *61 a *69 | Constructions accessoires ou speciales | Issues (balcons, perrons, galeries, escaliers), dependances, constructions speciales |
| *71 a *78 | Amenagement du site | Stationnements, murs de soutenement, piscines, services mecaniques/electriques externes |
| *79 | Attestation de verification | Verification d'exactitude des renseignements descriptifs du batiment |
| *81 a *89 | Description economique | Espaces locatifs, conditions de location, depenses d'exploitation |

---

## 4. Identifiants et codification

### 4.1 Code geographique et matricule

L'identifiant universel de toute unite d'evaluation au Quebec est constitue du **code geographique** (identifiant la municipalite, determine par l'ISQ) et du **numero matricule** (coordonnees rectangulaires). Le matricule comprend : division (1000 m x 1000 m), section (100 m x 100 m), emplacement (centroide visuel), chiffre autoverificateur (facultatif), numero de batiment et numero de local (au besoin).

### 4.2 CUBF (Code d'utilisation des biens-fonds)

Code numerique a 4 chiffres hierarchiques decrivant l'usage preponderant de l'unite d'evaluation. Repertorie a l'annexe 2C.1. Peut correspondre a l'usage des batiments, sauf si le terrain est inutilise ou exploite distinctement.

### 4.3 Prefixes de codification

| Prefixe | Fichier/Type |
|---------|-------------|
| FM | Fichier des mutations immobilieres |
| AD | Renseignements administratifs (dossier propriete) |
| TG | Terrain general |
| TA | Terrain agricole ou boise |
| R_ | Batiment residentiel |
| M_ | Batiment multiresidentiel |
| N_ | Batiment non residentiel |
| A_ | Batiment agricole |
| RE | Resultats d'evaluation |
| VERSION | Version du repertoire |

### 4.4 Unite de voisinage

Numero distinctif attribue par l'evaluateur (AD0002A). Chaque unite d'evaluation inscrite au role est rattachee a une unite de voisinage.

---

## 5. Fichier des mutations immobilieres - Codification complete

### 5.1 Les 14 groupes de renseignements prescrits

1. **Identification de l'acte** : Numero d'inscription (FM0101A), date de transaction (FM0102A), code geographique (FM0103A), categorie (FM0104A)
2. **Designation cadastrale** : Numero de lot cadastre Quebec (FM0201Ax), suffixe (FM0201Bx), nom cadastre non renove (FM0201Cx), designation secondaire (FM0201Dx), numero de lot (FM0201Ex), indicateur partie non subdivisee (FM0201Fx)
3. **Identification des parties** : Nom/prenom cedant (FM0301A/B), nom/prenom acquereur (FM0302A/B)
4. **Copropriete indivise** : Quote-part (FM0401A)
5. **Copropriete divise** : Quote-part (FM0501A)
6. **Restrictions** : Code 1 a 7 (FM0601Ax) - isolation miuf, restriction construction, zone inondable, bien culturel, utilite publique, droit de passage, autre. Description (FM0602A)
7. **Biens non immobiliers** : Description (FM0701Ax), valeur a l'acte (FM0701Bx)
8. **Valeur au role** : Terrain (FM0801A), batiment (FM0802A), immeuble (FM0803A)
9. **Prix de vente** : Prix declare (FM0901A, incluant TPS/TVQ si applicable), valeur biens non immobiliers (FM0902A), rajustements (FM0903A), prix rajuste (FM0904A). Formule : Prix rajuste = Prix declare - Biens non immobiliers +/- Rajustements
10. **Hypotheque** : Solde (FM1001A), taux d'interet (FM1002A), conversion (FM1002B : A/S/T/M/H), terme (FM1003A), remboursement montant/frequence (FM1004A/B), amortissement (FM1005A), 1er versement (FM1006A), nom creancier (FM1007A)
11. **Renseignements generaux** : Logements (FM1101A), chambres locatives (FM1102A), locaux NR (FM1103A), etages (FM1104A), aire d'etages (FM1105A), lien physique (FM1106A), annee originelle (FM1107A), utilisation/CUBF (FM1108A), matricule (FM1109A)
12. **Adresse** : Numero inferieur/superieur (FM1201A-D), generique (FM1201E), lien (FM1201F), voie publique (FM1201G), point cardinal (FM1201H), numero appartement/local (FM1201I/J)
13. **Terrain** : Renseignements communs (utilisation FM1301A, unite de voisinage FM1302A). Terrain general (forme FM1303A, localisation FM1304Ax, front FM1305A, profondeur FM1306A, superficie FM1307A, topographie FM1308Ax, autre topo FM1309A, services FM1310Ax, zone agricole FM1311A, droit acquis FM1312A). Terrain agricole/boise (front FM1313A, superficie totale FM1314A, % superficie zonee FM1315A, forme FM1316Ax, services FM1317Ax, superficie droit acquis FM1318A, superficies detaillees FM1319A a FM1326A)
14. **Resultats d'analyse des ventes** : Memo (FM1401A), ratio (FM1402A), decision (FM1403A : 1=admise, 0=exclue), motif d'exclusion (FM1404A), nom/prenom analyste (FM1405A/B), date analyse (FM1406A)

### 5.2 Motifs d'exclusion des ventes

**Motifs generaux** (fichier des mutations) :

| Code | Motif |
|------|-------|
| C | Considerations sentimentales ou liens de parente |
| G | Liquidation de biens, vente pour defaut de paiement de taxes |
| H | Vente entre filiales d'une meme entreprise |
| J | Prix anormalement eleve pour immeuble adjacent deja possede |
| K | Biens meubles d'une valeur significative inclus |
| M | Vente de droits indivis |
| S | Restriction importante (servitude, usufruit) |
| X | Expropriation impliquant un corps public |
| Y | Conditions de financement inhabituelles |
| Z | Autres circonstances (necessite explication dans memo) |

**Motifs exclusifs a la proportion mediane** (non concordance immeubles vendus vs role) :

| Code | Motif |
|------|-------|
| B | Non concordance batiment |
| D | Non concordance dossier |
| E | Non concordance evaluation |
| L | Non concordance lot |
| P | Non concordance propriete |

Ces motifs B/D/E/L/P ne justifient pas, a eux seuls, l'exclusion d'une vente aux fins d'autres analyses que la proportion mediane.

---

## 6. Donnees descriptives du terrain

### 6.1 Bloc *04 - Terrain general

**Caracteristiques** :
- Utilisation/CUBF (TG0401A)
- Forme (TG0402A) : 1-Carree, 2-Rectangulaire, 3-Trapezoidale, 4-Triangulaire, 5-Autre
- Localisation (TG0403Ax) : 1-Coin, 2-Interieure, 3-Exterieure, 4-Transversale, 5-Ilot, 6-Enclavee, 7-Riveraine, 8-Cul-de-sac. Plusieurs codes simultanes possibles.
- Front (TG0404A) en metres, sur voie publique de l'adresse principale. 0 = terrain enclave.
- Profondeur (TG0405A) en metres. 0 si aucune mesure representative.
- Superficie (TG0406A) en metres carres. Superficie utile ou occupee (LFM, art. 58). 0 si unite au nom du superficiaire.
- Topographie (TG0407Ax) : 1-Bas, 2-Contrebas, 3-Declivite, 4-Denivellation, 5-Plat, 6-Surplomb, 7-Autre. Plusieurs codes simultanes possibles.
- Autre topographie (TG0408A) en texte libre
- Superficie terre agricole exploitable non exploitee (TG0417A, art. 57.3 LFM)

**Services disponibles** (TG0409Ax) : 01-Eclairage, 02-Rue pavee, 03-Trottoir/chaine, 04-Deneigement, 05-Egout sanitaire, 06-Egout pluvial, 07-Aqueduc, 08-Tous les services 01-07, 09-Aucun des services 01-07, 10-Fosse septique, 11-Puits artesien. Nombre de raccordements (TG0409Bx) pour codes 05/06/07/10/11.

**Zonage agricole** : Zone agricole (TG0410A : 0/1/2), droit acquis (TG0411A : 0/1/2).

**Exploitation agricole enregistree** (terrain general dans EAE) : Superficie totale (TG0414A), superficie en zone agricole (TG0415A), superficie visee imposition maximale (TG0416A).

**Attraits ou nuisances significatifs** : Type (TG0412Ax : 1-Intrinseque, 2-Contigue, 3-Proximite, 4-Vue, 9-Aucun), description (TG0412Bx). Caractere multiple.

**Attestation de verification terrain** : Motif (TG0413Ax), type (TG0413Bx), date (TG0413Cx), employe (TG0413Dx/Ex), personne contactee (TG0413Fx/Gx).

### 6.2 Bloc *04 - Terrain agricole ou boise

Ventilation detaillee des superficies : superficie totale, pourcentage en zone agricole, forme (restrictions au potentiel agricole/forestier), services, superficie avec droit acquis, superficies cultivable, paturage, boisee, erabliere, arbres fruitiers, produits forestiers non ligneux, friche et inutilisable.

---

## 7. Donnees descriptives des batiments

### 7.1 Renseignements globaux communs

**Bloc *05 - Photo** : Photo numerique en format reconnu, montrant facade et un cote du batiment principal. Actualisee en meme temps que les autres renseignements descriptifs. Associee au matricule.

**Bloc *06 - Croquis** : Plan a l'echelle du pourtour du batiment et de ses dependances significatives. Dimensions brutes en metres/centimetres a la face externe des murs. Nombre d'etages encercle au centre. Codes : PAF (porte-a-faux), MM (mur mitoyen), P (perron), G (galerie), T (terrasse), B (balcon), TT (terrasse de toit), E (escalier), ESS (entree de sous-sol).

**Bloc *07 - Dimensions** : Aire brute des etages, nombre d'etages, hauteur, selon le type de batiment. Quatre degres de precision : nombre/mesure exact, pourcentage (appreciation attentive), strate d'envergure (appreciation sommaire), presence/absence (observation simple binaire).

### 7.2 Blocs specifiques selon le type

- **Batiment residentiel** : Blocs R_ (chapitres 4 de la partie 2C)
- **Batiment multiresidentiel** : Blocs M_ (chapitre 5)
- **Batiment agricole** : Blocs A_ (chapitre 6)
- **Batiment non residentiel** : Blocs N_ (chapitre 7)

Les blocs couvrent sequentiellement : infrastructure (*11-*19), structure et enveloppe (*21-*29), finitions interieur (*31-*39), services au batiment (*41-*49), equipements (*51-*59), constructions accessoires (*61-*69), amenagement du site (*71-*78).

### 7.3 Renovations

Sont considerees comme renovation : tout ajout ou remplacement significatif, posterieur a la construction originelle, d'elements toujours existants. Comprend les agrandissements et les remplacements substantiels de composantes (couverture de toit, parement de murs, portes et fenetres). Ne comprend pas l'entretien courant ni les reparations mineures. Pour chaque renovation : annee de renovation et pourcentage de la composante concernee.

### 7.4 Deterioration

Chaque deterioration est decrite par : le pourcentage approximatif de la portion de la composante a remplacer a court terme, et le code du type de materiau (pour distinguer les remplacements selon la duree de vie).

### 7.5 Qualite et complexite (codes A a E)

Appreciation du degre de qualite et de complexite de certains elements du batiment. Cinq codes : A (superieur), B (au-dessus de la moyenne), C (moyen), D (au-dessous de la moyenne), E (inferieur). Le MEFQ fournit des reperes concrets pour chaque element, mais l'evaluateur peut apprecier autrement si les reperes sont insuffisants.

Pour les batiments residentiels, 8 elements sont apprecies individuellement. La classe globale est une ponderation de ces 8 elements.

---

## 8. Donnees economiques

### 8.1 Blocs *81 a *89 - Description economique

**Espaces locatifs** : Inventaire de tous les espaces generant ou pouvant generer des revenus de location. Identification de chaque espace, superficie, type d'occupation.

**Conditions de location** : Loyers contractuels, duree des baux, conditions particulieres (echelons, options de renouvellement, clauses d'indexation).

**Depenses d'exploitation** : Frais annuels de possession et d'exploitation de l'immeuble, incluant taxes, assurances, entretien, reparations, administration, services publics, provisions pour remplacement.

### 8.2 Normalisation des revenus et depenses

Les donnees economiques servent de base a l'application de la methode du revenu (bloc *92). La normalisation vise a refleter les conditions typiques du marche plutot que la situation contractuelle particuliere du proprietaire.

---

## 9. Resultats d'evaluation

### 9.1 Bloc *91 - Methode de comparaison

Requis au dossier de toute unite a laquelle cette methode a ete appliquee (sauf si plusieurs batiments principaux ou resultats non retenus en conciliation).

Renseignements prescrits :
- Indicateur de marche (RE9101A) : montant en dollars (ex: prix au m2)
- Nom de l'indicateur (RE9101B)
- Multiplicateur applique (RE9102A) : quantite caracterisant l'immeuble (ex: aire habitable en m2)
- Nom du multiplicateur (RE9102B)
- Resultat avant rajustement (RE9103A) = indicateur x multiplicateur
- Rajustements aux caracteristiques du sujet (RE9104A) : valeur contributive de caracteristiques differentes de celles comprises dans l'indicateur (abri d'auto, remise, sous-sol amenage). Peut etre negatif.
- Valeur indiquee par la methode de comparaison (RE9105A) = resultat avant rajustement + rajustements

### 9.2 Bloc *92 - Methode du revenu

Requis si methode appliquee et resultats retenus en conciliation. Deux techniques :

**Technique TGA** (taux global d'actualisation) :
- Revenu annuel (RE9201A) et type (RE9201B : potentiel brut, potentiel net, contractuel brut, etc.)
- Provision inoccupation et mauvaises creances (RE9202A)
- Revenu effectif (RE9203A) = revenu annuel - provision
- Depenses d'exploitation normalisees (RE9204A)
- Revenu net annuel normalise (RE9205A) = revenu effectif - depenses
- Indicateur de marche (RE9206A) : TGA comme diviseur
- Resultat avant rajustements (RE9207A) = revenu net / TGA
- Rajustements (RE9208A)
- Valeur indiquee (RE9209A) = resultat + rajustements

**Technique MRB** (multiplicateur de revenu brut) :
- Revenu annuel potentiel brut
- Indicateur de marche : MRB comme multiplicateur
- Resultat avant rajustements = revenu x MRB

### 9.3 Bloc *93 - Methode du cout

Renseignements prescrits :
- Cout neuf de l'ensemble des constructions (RE9301A) : batiment principal, dependances et ameliorations d'emplacement
- Depreciation (RE9302A) : diminution globale de valeur (deterioration et desuetude)
- Cout deprecie des constructions (RE9303A) = cout neuf - depreciation
- Valeur du terrain (RE9304A) : evalue comme s'il etait vague, selon l'usage le meilleur et le plus profitable
- Valeur indiquee par la methode du cout (RE9305A) = cout deprecie + valeur terrain

Formule : V = Terrain + (Cout neuf - Depreciation)

### 9.4 Bloc *94 - Valeur retenue

Requis au dossier de toute unite d'evaluation, sans exception. Conclusions de la conciliation.
- Date des conditions du marche (RE9401A) : date de reference (1er juillet de la 2e annee precedant le 1er exercice)
- Terrain (RE9402A) : arrondi a la centaine
- Batiment (RE9403A) : arrondi a la centaine
- Immeuble (RE9404A) = terrain + batiment, arrondi a la centaine

Sous reserve d'equilibration par facteur (*95), ces valeurs sont transposees au role.

### 9.5 Bloc *95 - Equilibration par facteurs

Requis si la valeur au role est issue d'une equilibration par facteurs.
- Date des conditions du marche (RE9501A)
- Valeur terrain au role anterieur (RE9502A), facteur d'equilibration terrain (RE9502B), valeur terrain au role en vigueur (RE9502C)
- Valeur batiment au role anterieur (RE9503A), facteur d'equilibration batiment (RE9503B), valeur batiment au role en vigueur (RE9503C)
- Valeur immeuble au role en vigueur (RE9504A) = terrain + batiment au role en vigueur

Lors du depot d'un role subsequent : supprimes si reevaluation, remplaces si nouvelle equilibration par facteurs, maintenus si pas d'equilibration.

### 9.6 Bloc *98 - Repartition fiscale

Pour les unites partiellement ou totalement exemptees de taxes. Identifie pour terrain, batiment et immeuble : source legislative (loi, article, alinea/paragraphe), montant concerne, partie d'immeuble (T/B/I), code d'imposabilite (1=imposable, 2=non imposable, 3=exempt de toute taxe EAE).

---

## 10. Attestation de verification (Bloc *79)

Bloc par lequel une personne habilitee atteste des circonstances d'une verification d'exactitude des renseignements descriptifs physiques d'un batiment. Sert au suivi du delai maximal de 9 ans (LFM, art. 36.1).

### 10.1 Renseignements requis

- **Motif** : 1-Permis (travaux de construction/renovation), 2-Vente (connaissance de l'objet de la vente), 3-Actualisation de l'inventaire, 4-Revision/Recours (revision administrative ou recours devant le TAQ)
- **Type** : C-Complete (tous les renseignements descriptifs verifies), P-Incomplete (partie seulement verifiee), R-Refus (proprietaire refuse l'acces)
- **Date** : AAAA MM JJ
- **Employe** : Nom et prenom de la personne ayant procede a la verification
- **Personne contactee** : Nom et prenom de la personne ayant autorise ou refuse la verification

Nouvelle sequence ajoutee a chaque verification. L'historique est conserve au dossier.

### 10.2 Delai de 9 ans

L'article 36.1 de la LFM fixe un delai maximal de 9 ans pour la verification de l'exactitude de l'inventaire des immeubles. Tout depassement doit etre signale. Le calendrier de reinspection gagne a etre adapte a l'activite du marche immobilier local.

---

## 11. Analyse et validation des ventes immobilieres

### 11.1 Nature de l'analyse

L'analyse des ventes n'est pas une analyse de comportement du marche. Elle consiste a s'interroger sur les conditions de la transaction pour determiner si la vente repond aux prescriptions de l'article 43 de la LFM (valeur reelle = valeur d'echange sur un marche libre et ouvert a la concurrence).

Seules les ventes (categories 1 a 4) sont analysees. Les non-ventes (categorie 5) ne servent qu'a la tenue a jour du role.

### 11.2 Demarche d'analyse en trois etapes

**Etape 1 - Validation des donnees sur la vente** : Verification des informations a l'acte. Source privilegiee : l'acheteur (obligation art. 18 LFM). Moyens : entrevue personnelle (preferee, peut etre couplee a une inspection), entrevue telephonique, enquete postale. Peuvent etre sollicites : vendeur, courtier, notaire, autorites municipales, institutions financieres.

**Etape 2 - Verification de l'exactitude des donnees sur l'immeuble vendu** : S'assurer que l'objet de la vente correspond aux donnees du fichier des mutations. Verifier les changements non couverts par les permis : ameliorations aux terrains, deteriorations, croissance/abattage boise, travaux sans permis. Les proprietes vendues constituent l'echantillonnage a partir duquel les parametres sont etablis.

**Etape 3 - Decision sur la representativite** : Sur la base d'une perception globale, decider si la vente est representative de la valeur reelle. Questions pertinentes de l'article 43 LFM :
- Les donnees permettent-elles de bien connaitre l'immeuble vendu et les droits s'y rapportant?
- Le financement comporte-t-il des conditions inhabituelles? Quantifiables?
- Existe-t-il des servitudes, restrictions, charges, conventions, impositions speciales?
- La presence de biens meubles ou elements incorporels a-t-elle eu un effet sur le prix?
- L'acheteur et le vendeur ont-ils agi prudemment, raisonnablement informes?
- Ont-ils agi sans contrainte et dans leur meilleur interet respectif?
- Le marche est-il ouvert et concurrentiel?
- Un effort de marketing adequat et un temps suffisant d'exposition ont-ils ete effectues?

### 11.3 Rajustements au prix de vente

Les rajustements les plus frequents :
- Taxes (TPS et TVQ)
- Valeur contributive des elements non immobiliers ou non portables au role
- Impact de conditions de paiement ou de financement inhabituelles

Tout rajustement doit etre objectif, adequatement motive, et ne pas representer une variation trop importante du prix declare.

### 11.4 Principe directeur

Un rajustement objectif et motive est preferable au simple rejet d'une vente. Le rejet statistique est preferable au rejet arbitraire. Il faut resister a la tentation d'ecarter une transaction dont le prix apparait irrationnel mais qui presente toutes les caracteristiques d'une vente repondant aux criteres de l'article 43.

---

## 12. Proportion mediane

### 12.1 Definition et raison d'etre

Indicateur statistique constitue par la donnee mediane d'une distribution de proportions individuelles (valeur au role / prix de vente). Mesure annuelle du niveau du role par rapport a la valeur reelle. Trois formes d'equite justifient son utilisation :

- **Equite intramunicipale** : Toutes les evaluations doivent tendre a representer une meme proportion de la valeur reelle
- **Equite intermunicipale** : Juste repartition des sommes entre municipalites (quotes-parts, perequation, taxation SQ)
- **Equite de l'imposition scolaire** : Uniformisation des evaluations pour les centres de services scolaires

### 12.2 Etablissement de la liste de base

Conditions des ventes a considerer :
- Prix de vente >= 5 000 $ (RPMREF, art. 2)
- Taxes applicables incluses dans le prix
- Conclue au cours du 2e, 3e ou 4e exercice precedant celui pour lequel on etablit la proportion mediane
- Immeuble situe sur le territoire de la municipalite visee

**Nombre requis de ventes** = Max(30, N / (15,500 + 0,001N)) ou N = nombre d'unites d'evaluation au sommaire du role.

Regles d'arrondissement : 0,001N a 3 decimales, 15,500 + 0,001N a 3 decimales, resultat final a l'unite (0 decimale).

### 12.3 Terminologie des ventes

- **Ventes requises** : Nombre devant etre inscrit a la liste de base (RPMREF, art. 5-7)
- **Ventes inscrites** : Nombre effectivement contenu dans la liste de base
- **Ventes admises** : Ventes inscrites moins les terrains excedentaires (motif U) et les ventes non representatives
- **Ventes utilisees** : Ventes admises moins les ventes retranchees par epuration statistique (RPMREF, art. 17)

### 12.4 Ecart type relatif a la mediane

Revele l'ampleur de la dispersion des valeurs autour de la proportion mediane. Exprime en pourcentage relatif. Comparable d'un role a l'autre. Seuil maximal prescrit : 24 % (indicateur #5).

---

## 13. Indicateurs de performance

### 13.1 Vue d'ensemble

10 indicateurs en 3 groupes, appliques aux roles comptant au moins 500 unites d'evaluation. Resultats exprimes par une note pour chaque indicateur, traduits en note globale en pourcentage.

### 13.2 Groupe 1 - Fiabilite de l'inventaire

**Indicateur #1 : Verification de l'inventaire** - Le nombre de verifications (3 derniers exercices) doit etre >= nombre de ventes (3 ans). Ne s'applique pas si ventes sur 3 ans > 33% des unites. Note : 10/10 si >= 1,0; 5/10 si 0,5-0,99; 0/10 si < 0,5.

### 13.3 Groupe 2 - Fiabilite des mesures statistiques

**Indicateur #2 : Proportion mediane** - Doit etre entre 90% et 110%. Note : 10/10 si dans l'intervalle; 5/10 si 80-89% ou 111-120%; 0/10 sinon.

**Indicateur #3 : Conservation des ventes** - Au moins 60% des ventes analysees doivent etre conservees (admises avant epuration statistique). Ne s'applique pas si < 10 ventes analysees. Note : 10/10 si >= 60%; 5/10 si 40-59,9%; 0/10 si < 40%.

**Indicateur #4 : Variation de la valeur des proprietes vendues** - Difference entre variation des valeurs des proprietes vendues et variation des valeurs de l'ensemble des proprietes de meme categorie doit etre < 10 points de pourcentage.

**Indicateur #8 : Conservation des ventes par categorie** - Au moins 40% des ventes conservees dans chacune des categories.

### 13.4 Groupe 3 - Equite horizontale

**Indicateur #5 : Ecart type relatif a la mediane** - Ne doit pas exceder 24%. Note : 10/10 si <= 24%; 5/10 si 24,1-34%; 0/10 si > 34%.

**Indicateur #6 : Effet de l'equilibration** - L'equilibration doit avoir un effet a la baisse sur l'ecart type relatif.

**Indicateur #7 : Effet de l'absence d'equilibration** - L'ecart type relatif d'un role resultant d'une equilibration anterieure ne doit pas augmenter de plus de 10 points de pourcentage.

**Indicateur #9 : Proportions medianes categorielles** - La difference entre les proportions medianes categorielles ne doit pas exceder 20 points de pourcentage.

**Indicateur #10 : Ecart type relatif categoriel** - L'ecart type relatif a toute proportion mediane categorielle ne doit pas exceder 30%.

---

## 14. Recoupement des donnees

### 14.1 Sources internes

- Dossier de propriete (renseignements descriptifs vs resultats d'evaluation)
- Fichier des mutations (ventes vs valeurs au role)
- SIG (donnees spatiales vs descriptions au dossier)
- Fichier des unites de voisinage (coherence des regroupements)

### 14.2 Sources externes

- Permis de construction et de renovation municipaux
- Cadastre officiel du Quebec (MERN)
- Registre foncier (Bureau de la publicite des droits)
- Enquetes SCHL (pour donnees de marche locatif)
- Registre des exploitations agricoles enregistrees (MAPAQ)
- Commission de protection du territoire agricole (CPTAQ)

### 14.3 Validation croisee des trois methodes

La coherence entre les resultats des trois methodes d'evaluation (comparaison, revenu, cout) constitue un element majeur de recoupement. Lors de la conciliation (partie 3F), la methode de comparaison constitue la preuve directe et est privilegiee.

### 14.4 Niveaux de confiance

| Niveau | Description | Conditions |
|--------|-------------|------------|
| A | Confiance elevee | Donnees completes, recoupees, coherentes entre elles |
| B | Confiance moyenne | Donnees partiellement verifiees ou coherence partielle |
| C | Confiance faible | Donnees non verifiees, incoherences significatives, lacunes importantes |

---

## 15. Qualite des donnees

### 15.1 Sept criteres de qualite

1. **Exactitude** : Les renseignements descriptifs correspondent a la realite physique et economique de l'immeuble.
2. **Actualite** : Les donnees sont a jour et refletent la situation actuelle. Delai maximal de 9 ans pour la verification de l'inventaire (LFM, art. 36.1).
3. **Completude** : Tous les renseignements prescrits par le RREF et le MEFQ sont presents au dossier.
4. **Coherence** : Les renseignements sont compatibles entre eux a l'interieur d'un meme dossier et entre les differents fichiers permanents.
5. **Uniformite** : Les memes standards de codification, de mesure et de description sont appliques de maniere constante sur l'ensemble du territoire.
6. **Perennite** : Les donnees sont conservees et structurees de maniere a transcender les roles successifs et les changements d'evaluateurs.
7. **Transmissibilite** : Les donnees sont structurees selon les formats prescrits (XML/XSD) et peuvent etre efficacement transmises a quiconque y ayant droit (RREF, art. 21).

### 15.2 Standards IAAO

L'International Association of Assessing Officers (IAAO) etablit des standards de pratique en evaluation de masse qui completent les prescriptions du MEFQ :
- Standard on Ratio Studies : methodologie d'etude des ratios evaluation/prix de vente
- Standard on Verification and Adjustment of Sales : processus de verification et rajustement des ventes
- Standard on Mass Appraisal of Real Property : principes d'evaluation de masse
- Standard on Automated Valuation Models (AVMs) : modeles d'evaluation automatises

Les principes IAAO s'alignent avec ceux du MEFQ en ce qui concerne l'importance de la verification des ventes, la mesure de l'equite par les ratios, et l'utilisation de seuils statistiques objectifs.

### 15.3 Standards IPMS

Les International Property Measurement Standards (IPMS) fournissent des references pour la mesure coherente des superficies immobilieres. La precision des mesures descriptives au dossier de propriete beneficie de l'adoption de standards internationaux de mesurage.

---

## 16. Depreciation

### 16.1 Trois categories

- **Depreciation physique** : Usure normale, deterioration des materiaux, effet du temps et des intemperies. Peut etre corrigible (entretien differe) ou incorrigible (usure structurelle irreversible).
- **Desuetude fonctionnelle** : Inadequation du batiment par rapport aux normes et exigences actuelles. Corrigible (mise a niveau economiquement justifiable) ou incorrigible (defaut structural non rentable a corriger).
- **Desuetude externe (economique)** : Facteurs exterieurs au batiment (changement de zonage, nuisances environnementales, declin economique du secteur). Toujours incorrigible par le proprietaire.

### 16.2 Guide de depreciation des batiments industriels

Outil complementaire au MEFQ pour l'evaluation de la depreciation des batiments industriels. Segmentation selon trois criteres : flexibilite d'utilisation, type de charpente et localisation. Fournit des tables de depreciation adaptees au contexte industriel quebecois.

---

## 17. Formats de transmission des donnees

### 17.1 Transmission electronique

Le RREF (art. 21) prescrit la forme des renseignements lors de leur transmission. Le chapitre 9 de la partie 2C expose les prescriptions techniques :
- Format (structure de donnees) a respecter
- Codification distinctive de chaque renseignement (indiquee entre parentheses a la droite de chaque renseignement dans les chapitres 1 et 3 a 8)
- Attributs devant caracteriser chaque renseignement transmis

### 17.2 Schema XML et gabarits XSD

Chaque fichier permanent utilise un numero de version de repertoire pour assurer la concordance avec le schema XML et les gabarits XSD prescrits. Le numero de version est le premier renseignement de chaque fichier (ex: FM0101A pour les mutations, VERSION pour les administratifs).

---

## 18. Processus de confection et de tenue a jour du role

### 18.1 Duree du role

Le role d'evaluation a une duree triennale (3 exercices financiers). Peut etre de 6 exercices dans certains cas (municipalites de petite taille). L'equilibration permet de maintenir les valeurs a niveau entre les reevaluations completes.

### 18.2 Date de reference

Toutes les evaluations doivent refleter les conditions du marche a la date de reference : le 1er juillet de la 2e annee qui precede le 1er des exercices financiers auxquels s'applique le role. Exemple : role 2025-2027, date de reference = 1er juillet 2023.

### 18.3 Obligation de verification

L'evaluateur doit verifier l'exactitude de l'inventaire des immeubles au moins tous les 9 ans (LFM, art. 36.1). Le calendrier de reinspection est adapte a l'activite du marche immobilier local. La verification des proprietes vendues est particulierement prioritaire car elles constituent l'echantillonnage de base.

### 18.4 Sources d'information

- Avis de mutation immobiliere (Bureau de la publicite des droits)
- Permis de construction et de renovation
- Inspections sur le terrain
- Enquetes aupres des acquereurs (obligation art. 18 LFM)
- Systemes d'information geographique
- Donnees cadastrales
- Sommaire du role d'evaluation fonciere
