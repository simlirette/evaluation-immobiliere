# eval-immo — Présentation bureau É.A.

**Pour :** Directeur(trice) de bureau d'évaluateurs agréés  
**Version :** Mai 2026 — Confidentiel

---

## Ce qu'eval-immo fait aujourd'hui

eval-immo est un assistant de travail pour évaluateurs agréés. Il prend en charge les tâches répétitives du dossier d'évaluation résidentielle, de la réception du mandat jusqu'à l'export du rapport.

### Flux de travail actuel (4 étapes confirmées par l'É.A.)

**Étape 1 — Faits du dossier**  
L'É.A. téléverse les documents du dossier (PDF contrat, photos, acte). eval-immo extrait automatiquement les informations clés : adresse, type de bien, superficie, année de construction, commanditaire. L'É.A. valide et corrige si besoin.

**Étape 2 — Comparables JLR**  
L'É.A. importe son export CSV JLR. eval-immo score chaque transaction (superficie, distance, date, type de bien) et propose les 8 meilleurs candidats. L'É.A. sélectionne ceux qu'il retient — minimum 3 requis.

**Étape 3 — Réconciliation**  
eval-immo calcule l'approche comparative avec les ajustements retenus, vérifie automatiquement 7 règles de conformité OEAQ (champs obligatoires, dates, distances, plausibilité de la valeur). Les blocages sont signalés avec explication en français.

**Étape 4 — Rapport**  
Un brouillon de rapport est généré par intelligence artificielle selon le format OEAQ applicable (abrégé ou complet 15 sections). L'É.A. l'édite directement dans l'outil, puis exporte en PDF ou Word.

### Résultats mesurés — Dossier démo Chomedey (Laval)

| Phase | Sans eval-immo | Avec eval-immo | Gain |
|---|---:|---:|---:|
| Lecture mandat + saisie | 15 min | 3 min | −80 % |
| Extraction faits dossier | 25 min | 4 min | −84 % |
| Recherche comparables JLR | 40 min | 8 min | −80 % |
| Calcul ajustements | 30 min | 5 min | −83 % |
| Rédaction brouillon rapport | 60 min | 10 min | −83 % |
| Révision É.A. (maintenue) | 30 min | 20 min | −33 % |
| Mise en page + export PDF | 20 min | 2 min | −90 % |
| **Total temps É.A.** | **220 min** | **52 min** | **−76 %** |

> Sur 10 dossiers résidentiels par mois, c'est **28 heures récupérées** — soit l'équivalent de 3 à 4 mandats additionnels sans embauche.

---

## Ce qui arrive dans les 6 prochains mois

### Connecteur JLR — été 2026
Accès direct à la base JLR depuis eval-immo, sans export CSV manuel. L'É.A. lance la recherche de comparables depuis l'outil, avec filtres géographiques et critères de bien. Requiert une entente avec JLR (démarche en cours).

### Tables Altus/Marshall Swift — automne 2026
Intégration des coûts de construction Altus pour l'approche par le coût. Aujourd'hui, cette approche est signalée comme proxy non certifiable — elle deviendra pleinement certifiable avec les tables réelles.

### Multi-bureau — automne 2026
Gestion de plusieurs É.A. dans le même bureau : tableau de bord directeur, attribution des dossiers, historique centralisé, facturation consolidée.

---

## Modèle de tarification

| Formule | Coût mensuel | Inclus |
|---|---:|---|
| **Bureau — base** | 299 $/mois | Jusqu'à 3 É.A., accès complet, support |
| **Bureau — standard** | 499 $/mois | Jusqu'à 8 É.A., multi-bureau, export illimité |
| **Crédit dossier** | 25 $/dossier | Rapport PDF certifiable exporté |

**Exemple — bureau 3 É.A., 10 dossiers/mois :**  
299 $ (base) + 250 $ (10 × 25 $) = **549 $/mois**

**Valeur générée :** 28 h × 80 $/h (taux É.A. moyen) = **2 240 $/mois**  
**Ratio valeur/coût : 4,1×**

---

## Conformité et responsabilité professionnelle

- Chaque décision de l'É.A. est horodatée et enregistrée (4 points de contrôle obligatoires)
- Le rapport exporté porte la mention **BROUILLON NON CERTIFIÉ** jusqu'à validation et signature de l'É.A.
- eval-immo n'émet pas d'opinion de valeur — il produit un brouillon soumis au jugement professionnel de l'É.A.
- Conforme au principe human-in-the-loop de la Norme 6 OEAQ

---

## Prochaines étapes

1. **Démo live** — passage complet d'un dossier résidentiel devant votre équipe (1 h)
2. **Pilote** — un É.A. de votre bureau teste eval-immo sur 3 vrais dossiers (2 semaines, gratuit)
3. **Entente** — signature + configuration du bureau + formation É.A. (1/2 journée)

**Contact :** Simon-Olivier Paré — [à compléter avant la démo]

---

*Document confidentiel — usage interne bureau.*
