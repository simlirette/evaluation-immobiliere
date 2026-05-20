# Brainstorming eval-immo — Notes de session
**Date :** 2026-05-20
**Format :** questions posées une par une, réponses de Simon-Olivier, points bloquants identifiés.

---

## Q1 — L'outil est-il un assistant ou un générateur de rapport ?

### Réponse de Simon-Olivier
Les deux. L'évaluateur est le **décideur et réviseur**, pas le commis de saisie.

Flux cible :
1. Évaluateur joint les documents de départ
2. Agents analysent et exécutent le workflow métier
3. L'évaluateur confirme les points clés (pas chaque étape)
4. Agents rédigent le rapport demandé
5. Évaluateur révise, exporte, signe

Saisies manuelles acceptables : joindre les documents initiaux, confirmer la première analyse, indiquer les actions/méthodes à prendre, joindre des documents supplémentaires si demandé, réviser le rapport final.

### Architecture cible identifiée
Pipeline stoppable et relançable par étape (pas one-shot), avec 4 checkpoints humains :

```
[Documents déposés]
    ↓
Pipeline intake + data-facts
    ↓
[CHECKPOINT 1] Évaluateur confirme les faits du bien sujet
    ↓
Pipeline comps-market
    ↓
[CHECKPOINT 2] Évaluateur confirme les comparables retenus
    ↓
Pipeline valuation-draft
    ↓
[CHECKPOINT 3] Évaluateur confirme la réconciliation des approches
    ↓
Pipeline compliance-qa + redaction
    ↓
[CHECKPOINT 4] Révision rapport → export → signature
```

### Ce qui existe déjà (bien)
- Pipeline 7 étapes one-shot fonctionnel
- Couche conversationnelle SSE (`/app/message/stream`) — Q&A sur artefacts existants
- Gate de validation unique avant package V1
- Upload PDF → extraction texte (PyMuPDF) → source_index
- `ingest_uploaded_documents()` : PDF → GPT-4o Vision → champs structurés → injectés dans le case avant pipeline

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 1.1 | Pipeline one-shot non stoppable — doit devenir relançable par étape avec état persisté entre checkpoints | Bloquant critique | L |
| 1.2 | `_STRUCTURED_FIELDS_SCHEMA` extrait 10 champs sur ~30+ nécessaires — `type_bien`, `adresse`, `destination`, `zonage`, `nb_pieces`, `garage`, etc. manquants | Bloquant opérationnel | S |
| 1.3 | Pas de feedback UI post-upload — l'évaluateur ne voit pas ce que les agents ont compris de ses documents (CHECKPOINT 1 sans interface) | Bloquant UX | M |
| 1.4 | PDF scanné non extrait sans `OPENAI_API_KEY` — échec silencieux (`try/except: pass`) — pipeline continue avec fixture par défaut sans avertir | Bloquant prod | S |
| 1.5 | "Évaluateur ordonne les prochaines étapes" ≠ Q&A — le code actuel répond aux questions sur artefacts existants, il ne peut pas ré-exécuter une étape spécifique avec une nouvelle instruction | Gap architectural | L |

---

## Q2 — Comment justifies-tu à l'OEAQ que l'IA "propose" les comparables ?

### Réponse de Simon-Olivier
eval-immo trouve et propose les comparables via JLR (connecteur à implémenter). L'évaluateur est celui qui confirme. L'IA fait la recherche, pas le choix.

### Ligne OEAQ
"IA propose / évaluateur confirme" = acte professionnel (sélection) reste humain. Défendable sous §6.5 du Code, à condition que le CHECKPOINT 2 soit un vrai gate (pas contournable).

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 2.1 | Zéro connecteur JLR — `search_comparables()` filtre un pool fourni manuellement — chemin critique bloqué | Bloquant critique | L |
| 2.2 | Accès JLR = partenariat ou abonnement professionnel — dépendance externe non technique | Bloquant business | - |
| 2.3 | CHECKPOINT 2 (confirmation comparables) non implémenté comme gate réel — actuellement déclaratif dans contrats YAML | Bloquant conformité | M |
| 2.4 | Sans JLR, version intermédiaire possible : évaluateur exporte un CSV/Excel depuis JLR/Centris, eval-immo l'ingère et propose le ranking | Contournement temporaire | S |

---

## Q3 — `human_validation_required: true` est-il une protection ou une illusion ?

### Réponse de Simon-Olivier
Chaque checkpoint enregistre : date, heure, nom de l'évaluateur. Pipeline physiquement bloqué si checkpoint non confirmé — on ne peut pas passer à l'étape suivante sans avoir validé la précédente. Les confirmations n'apparaissent pas dans le rapport exporté (rapport propre), mais existent dans le dossier interne.

### Ce que ça implique techniquement
```
checkpoint_log.jsonl (interne, jamais exporté) :
  { "checkpoint": 1, "label": "faits_bien_sujet", "confirmed_by": "Jean Tremblay É.A.",
    "confirmed_at": "2026-05-20T14:32:11Z", "snapshot_hash": "..." }
```
- Le `snapshot_hash` = hash des artefacts confirmés à ce moment → preuve que l'évaluateur a validé *cette version* des données, pas une version modifiée après coup.
- Gate backend : `run_pipeline_from(checkpoint=2)` vérifie que `checkpoint_1.confirmed = true` avant d'exécuter. Sinon : erreur bloquante.
- Rapport exporté : aucune mention des confirmations — contenu professionnel uniquement.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 3.1 | `checkpoint_log.jsonl` n'existe pas — aucune trace horodatée des confirmations dans le code actuel | Bloquant conformité | M |
| 3.2 | Pipeline non stoppable par checkpoint — `app_validate_review` est le seul gate, en fin de pipeline | Bloquant critique | L |
| 3.3 | Nom de l'évaluateur non structuré dans la session — `reviewer` est une string libre, pas liée à un compte authentifié | Bloquant conformité | M |
| 3.4 | Snapshot hash absent — sans lui, impossible de prouver que l'évaluateur a validé la version exacte des données | Bloquant audit | S |

---

## Q4 — Un rapport produit sans LLM est-il certifiable ?

### Réponse de Simon-Olivier
Option A : LLM rédige la prose du rapport. Des modèles de rapport par type sont fournis à l'agent redaction comme référence de style/structure. Si OpenAI est down : eval-immo fait ce qu'il peut, l'évaluateur complète à la main. OpenAI est une dépendance forte en mode normal, mais pas un bloquant dur.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 4.1 | Aucun modèle de rapport par type (résidentiel, commercial, industriel, agricole) fourni à l'agent redaction — `AGENTCONFIG-REDACTION-V0.yaml` n'a pas de section "modèles" | Bloquant qualité | M |
| 4.2 | Pas de gestion explicite du mode dégradé (OpenAI down) — aujourd'hui `try/except` silencieux, évaluateur ne sait pas que le brouillon est vide | Bloquant UX | S |
| 4.3 | Éditeur de rapport en ligne absent — si LLM down, l'évaluateur n'a nulle part pour rédiger à la main dans l'outil | Bloquant UX | M |

---

## Q5 — Pourquoi `compliance-qa` est-il un LLM et non un moteur de règles ?

### Réponse de Simon-Olivier
Aucun rapport non-conforme ne doit être livré. Les violations et informations manquantes doivent être signalées à l'évaluateur avec une explication claire pour qu'il puisse corriger. C'est un bloquant dur.

### Architecture cible
Deux couches distinctes :

1. **Moteur de règles déterministe (Python pur)** — B001 à B007 codées en `if/else`. Si une règle est violée : pipeline bloqué physiquement, message d'erreur structuré avec explication actionnable.
2. **LLM optionnel en surcouche** — pour les avertissements (W001-W005) et la rédaction du message d'explication à l'évaluateur (ton humain, pas technique).

```
compliance_check(case) → [
  { "rule": "B002", "status": "VIOLATED",
    "explanation": "Le comparable C-3 n'a pas de source_id. Ajoutez le numéro
                    de fiche JLR ou la référence Centris avant de continuer." },
  ...
]
→ si len(violations) > 0 : pipeline bloqué, retour à l'évaluateur
→ si len(violations) == 0 : pipeline continue
```

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 5.1 | B001-B007 dans un `system_prompt` LLM — non-déterministe, peut rater des violations — à réécrire en Python pur | Bloquant critique | M |
| 5.2 | Messages d'erreur actuels : techniques et non-actionnables pour un É.A. — besoin d'explications en français clair | Bloquant UX | S |
| 5.3 | Pas de mécanisme de retour au checkpoint précédent après violation — l'évaluateur est bloqué sans savoir comment reprendre le dossier | Bloquant UX | M |
| 5.4 | Règles W001-W005 (avertissements) : LLM acceptable ici car non-bloquant, mais doit être clairement séparé des règles bloquantes | Note architecture | S |

---

## Q6 — `data_enrichment.py` : module central ou périphérique ?

### Réponse de Simon-Olivier
Se fier au workflow OEAQ exact — pas d'interprétation libre.

### Ce que le workflow dit (lu dans `workflow-evaluateur-agree.md`)

| Donnée | Usage OEAQ réel | Rôle dans pipeline | Priorité |
|---|---|---|---|
| Zonage municipal | AMU critère 1 (légalement permis) — décision binaire qui guide choix des approches | Central — calcul | Bloquant |
| Loyers SCHL / taux vacance | Approche revenu uniquement, immeubles locatifs | Conditionnel (si type_bien = locatif) | Moyen |
| Rôle municipal (MAMH) | Cross-check cohérence valeur finale vs évaluation municipale | Contextuel — validation | Bas |
| StatCan WDS | Non mentionné dans le workflow OEAQ — sources citées : Altus, Marshall Swift, SCHL, CBRE | Hors scope métier | Retirer |
| Nominatim / GeoJSON | Géocodage adresse → coordonnées → zonage | Infrastructure (sert le zonage) | Bloquant |

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 6.1 | Zonage extrait mais non utilisé dans la logique AMU — `valuation.py` ignore le zonage pour déterminer les approches applicables | Bloquant métier | M |
| 6.2 | StatCan WDS (5 142 LOC partiellement) — source non utilisée par les É.A. québécois — investissement non aligné avec le workflow OEAQ | Dette technique | M |
| 6.3 | Tests `DataEnrichment` font des appels HTTP réels — bloquent indéfiniment hors ligne — aucun mock prévu | Bloquant tests | S |
| 6.4 | Loyers SCHL injectés dans tous les dossiers même résidentiels — logique conditionnelle manquante (if type_bien == locatif) | Bug silencieux | S |

---

## Q7 — 16 sessions pour le même dossier. Quelle session est la "vraie" ?

### Réponse de Simon-Olivier
Ce n'est pas l'idéal. 1 dossier = 1 session active. L'évaluateur sélectionne un dossier et travaille dessus — pas de choix de session à faire. La session active est toujours la bonne et à jour.

### Architecture cible
```
Dossier (entité persistante, ex: D-2026-001)
└── Session active (1 seule à la fois, UUID interne)
    ├── Checkpoints confirmés
    ├── Artefacts courants
    └── Historique des runs (audit trail interne, non visible à l'évaluateur)
```
Si l'évaluateur repart d'une étape (après correction d'une violation B002), le pipeline reprend depuis le checkpoint précédent sur la même session — il ne crée pas une nouvelle session.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 7.1 | `create_session()` crée un UUID à chaque run — pas de concept de "session active par dossier" | Bloquant UX | M |
| 7.2 | 16 sessions pour D-PILOTE-RES-001 en dev — sans nettoyage automatique, accumulation illimitée en prod | Bloquant prod | S |
| 7.3 | Dossier et session sont le même concept aujourd'hui — à séparer : dossier = entité métier persistante, session = run technique interne | Gap architectural | M |

---

## Q8 — Comment les comparables entrent-ils dans le système en production réelle ?

### Réponse de Simon-Olivier
Pas de contrat API JLR actuellement. Version intermédiaire acceptable pour les premiers utilisateurs : évaluateur exporte CSV depuis JLR.ca, eval-immo ingère et propose le ranking. API JLR = objectif futur, à clarifier avec JLR (politique partenariat startup inconnue).

### Roadmap connecteur comparables

| Phase | Mécanisme | Dépendance | Effort |
|---|---|---|---|
| V1 (maintenant) | Import CSV/Excel depuis JLR.ca ou Centris — eval-immo parse, score, propose | Aucune externe | S |
| V2 | API JLR si partenariat obtenu — fetch automatique par adresse + critères | Contrat JLR | L |
| V3 | Multi-source (JLR + Centris + registre foncier public) | Plusieurs contrats | XL |

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 8.1 | Aucun parseur CSV/Excel JLR — `search_comparables()` attend un dict Python, pas un fichier | Bloquant V1 | S |
| 8.2 | Format d'export JLR.ca non documenté dans le code — colonnes, encodage, format date à valider sur un vrai export | Bloquant V1 | S |
| 8.3 | Politique partenariat API JLR avec startups inconnue — risque business à valider avant d'investir dans le connecteur V2 | Risque business | - |

---

## Q9 — Approche coût sans tables de coûts — quel est le plan ?

### Réponse de Simon-Olivier
1. Afficher seulement les approches pertinentes selon le type de bien (comme un É.A. le ferait). Pas les trois approches systématiquement.
2. Investiguer partenariat/export Altus et Marshall Swift. Même approche CSV que JLR si API non disponible.

### Ce qu'on sait sur les sources de coûts

| Source | Accès É.A. | API | Export CSV | Partenariat startup |
|---|---|---|---|---|
| Altus Data Studio | Licence firme (pas individuel) | Enterprise seulement | Oui (Excel/CSV) | Non documenté |
| Marshall Swift (CoreLogic) | Licence firme | API orientée USA | Oui (PDF/Excel) | Non documenté |
| MAMH (public) | Gratuit, public | Non — téléchargement fichier | Oui | N/A |

### Questions à valider avec les É.A. cibles
- Travaillent-ils en firme (accès Altus via employeur) ou en solo (pas d'accès) ?
- Si firme : la firme accepterait-elle d'exporter leurs tables Altus vers eval-immo ?
- Si solo : ils n'ont pas accès à Altus/Marshall Swift — l'approche coût est alors impossible sans alternative.

### Décision intermédiaire actée
- Afficher proxy actuel (`mean(prix_vente)`) avec avertissement explicite dans l'artefact : "VALEUR PROXY — non certifiable OEAQ, remplacer par calcul Altus/Marshall Swift"
- Approche revenu : ne pas afficher pour résidentiel unifamilial (non applicable)
- Approche coût : afficher seulement si données de coûts disponibles (Altus importé ou saisie manuelle É.A.)

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 9.1 | Proxy `mean(prix_vente)` présenté comme "approche coût" sans watermark visible — non certifiable et trompeur | Bloquant conformité | S |
| 9.2 | Approche revenu calculée sur tous les dossiers même résidentiels — logique conditionnelle par type_bien manquante | Bloquant métier | S |
| 9.3 | Aucun parseur pour tables Altus/Marshall Swift — à construire si export CSV validé | Bloquant V2 | M |
| 9.4 | Accès solo vs firme non clarifié — change radicalement la faisabilité de l'approche coût | Risque business | - |

---

## Q10 — L'OEAQ est-il au courant ? Quel est le plan de divulgation ?

### Réponse de Simon-Olivier
Pas de contact OEAQ à ce jour. Peut contacter son avocat. Croit que les checkpoints + human-in-the-loop démontrent la conformité.

### Analyse du risque
La thèse est défendable : les 4 checkpoints + log horodaté + gate bloquant = l'évaluateur prend des décisions réelles à chaque étape critique. C'est structurellement proche d'un logiciel comme GESTIM Plus (que l'OEAQ accepte déjà).

Le vide réglementaire sur l'IA au Québec joue en faveur d'eval-immo aujourd'hui — mais c'est un risque évolutif.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 10.1 | Aucune validation juridique avant premier client payant — risque disciplinaire pour l'évaluateur si l'OEAQ interprète différemment | Risque business | - |
| 10.2 | Les checkpoints (Q3) doivent être implémentés avant tout usage réel — sans eux, la thèse "human-in-the-loop" n'est pas démontrée dans le code | Bloquant conformité | L |
| 10.3 | Action recommandée : consulter l'avocat avec un document montrant les 4 checkpoints + log horodaté + gates bloquants — avant le premier É.A. payant | Action business | - |

---

## Q11 — La lettre de mandat générée automatiquement est-elle légalement valide ?

### Contexte
La lettre de mandat = contrat entre l'évaluateur et son client. 10 éléments obligatoires §6.3 : nom du client, adresse de la propriété, objet de l'évaluation, honoraires, date limite, signatures. Premier document produit, avant inspection.

### Réponse de Simon-Olivier
Objectif = réduire le temps de l'évaluateur. Quelle option est la plus optimale ?

### Décision actée : formulaire pré-rempli, pas LLM
L'évaluateur saisit 5-6 champs à l'ouverture du dossier → eval-immo génère la lettre depuis un template fixe → évaluateur relit, corrige si besoin, envoie.

Le LLM est le mauvais outil ici : le contenu est structuré (noms, dates, montants), pas narratif. Un template `{{ nom_client }}`, `{{ adresse }}`, `{{ honoraires }}` est 100% fiable et sans placeholders.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 11.1 | `AGENTCONFIG-MANDAT-INTAKE-V0.yaml` utilise LLM + `temperature: 0.1` pour générer la lettre — produit des placeholders `[À CONFIRMER]` si données manquantes | Bloquant conformité | S |
| 11.2 | Aucun template fixe de lettre de mandat par type de mandat (résidentiel, commercial, expropriation) | Bloquant V1 | S |
| 11.3 | Les 5-6 champs d'entrée (client, adresse, objet, honoraires, délai) doivent être le premier écran du workflow — avant tout lancement de pipeline | Gap UX | M |

---

## Q12 — Quel est le coût LLM par dossier et comment le justifier dans le pricing ?

### Réponse de Simon-Olivier
Modèle : frais de base par bureau (selon nb users) + coût par "token" d'usage. Base = couvre dépenses fixes. Variable = croît avec l'usage intensif. Objectif marge minimale 30%. Valeur vendue = temps gagné par évaluateur (pas features). Optimiser les modèles LLM pour réduire les coûts tout en maintenant la qualité professionnelle.

### Clarification importante sur "token"
Le "token" facturé à l'évaluateur ≠ token OpenAI. C'est une unité d'usage eval-immo à définir. Options :
- **Crédit par dossier** (1 dossier = X crédits) — plus simple à comprendre pour l'évaluateur
- **Crédit par étape pipeline** (intake = 1, rapport = 3) — plus granulaire
- **Crédit par rapport exporté** — facture uniquement ce qui a de la valeur livrée

### Optimisation modèles LLM par tâche

| Tâche | Modèle optimal | Justification |
|---|---|---|
| Extraction PDF → champs structurés | GPT-4o (Vision) | Nécessite compréhension visuelle |
| Extraction texte → JSON | GPT-4o-mini | Tâche structurée, pas besoin de puissance |
| Compliance B001-B007 | Aucun LLM (Python pur) | Déterministe obligatoire |
| Avertissements W001-W005 | GPT-4o-mini | Signalement, pas décision |
| Scoring comparables | Aucun LLM (algorithme) | Calcul déterministe |
| AMU — analyse zonage | GPT-4o-mini | Raisonnement simple sur données structurées |
| Rédaction rapport | GPT-4o | Prose professionnelle = qualité visible |
| Q&A agent conversationnel | GPT-4o-mini | Réponses rapides sur artefacts existants |

Économie estimée vs tout GPT-4o : ~75% de réduction du coût LLM par dossier.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 12.1 | Tous les agents utilisent le même modèle (`gpt-4o-mini` par défaut) — pas de routing par tâche | Coût optimisable | S |
| 12.2 | Aucun compteur de crédits/usage par dossier ou par bureau — infrastructure billing absente | Bloquant business | M |
| 12.3 | Calcul du temps gagné par dossier non mesuré — argument de vente principal sans donnée | Bloquant commercial | S |

---

## Q13 — Stack infra à 50 évaluateurs : coût et longévité ?

### Réponse de Simon-Olivier
Stack actuelle acceptable pour maintenant. Migration cloud (AWS/Azure/GCP) nécessaire pour la sécurité des données à plus grande échelle. Analyse de migration = session dédiée quand le moment est venu. Pas une priorité immédiate.

### Estimation coûts actuels

| Service | Dev | 50 évaluateurs | 500 évaluateurs |
|---|---|---|---|
| Vercel (frontend) | Gratuit | ~$20/mois | ~$150/mois |
| Railway (backend) | ~$5/mois | ~$50-100/mois | Migration requise |
| Supabase (DB) | Gratuit | ~$25/mois | ~$100/mois |
| OpenAI | Variable | ~$50-500/mois | ~$500-5000/mois |
| **Total** | ~$5/mois | ~$145-645/mois | Migration cloud |

### Note sécurité données
Les dossiers d'évaluation contiennent des données personnelles (adresses, propriétaires, valeurs) soumises à la Loi 25 (Québec) et possiblement à des exigences de résidence des données. À documenter avant le premier client payant — pas une décision à improviser.

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 13.1 | Conformité Loi 25 (données personnelles québécoises) non analysée — exige inventaire des données collectées et politique de rétention | Risque légal | M |
| 13.2 | Politique d'archivage des sessions absente — accumulation illimitée (déjà 16 sessions pour 1 dossier pilote) | Bloquant prod | S |
| 13.3 | Migration cloud = session dédiée quand seuil ~200 évaluateurs atteint | Différé délibérément | XL |
| **13.4** | **Conformité Loi 25 obligatoire — non différable — inventaire données personnelles + politique rétention avant premier client** | **Bloquant légal** | **M** |

---

## Q14 — Quelle est la métrique de succès à 3 mois ?

### Réponse de Simon-Olivier
Contact É.A. déjà identifié. Objectif : présenter un produit concret fonctionnel + roadmap d'améliorations (JLR, Altus, etc.) pour convaincre le bureau de signer une entente pour leurs employés. C'est une démo de vente B2B, pas un MVP utilisateur.

### Ce que ça implique concrètement
La cible dans 3 mois n'est pas "un É.A. a traité un vrai dossier" — c'est "le bureau a signé". Pour ça, il faut :

1. **Un dossier résidentiel complet démo-able** — intake PDF → comparables CSV → rapport exporté — avec les données anonymisées d'un vrai dossier. Le bureau doit voir quelque chose qui ressemble à leur travail réel.
2. **Une roadmap écrite** — JLR API, Altus, checkpoints, modèles de rapport — avec des jalons et une estimation de valeur par feature.
3. **Un argument temps gagné** — même approximatif. "Ce dossier aurait pris X heures, eval-immo l'a réduit à Y heures."

### Points manquants / bloquants

| # | Problème | Sévérité | Effort |
|---|---|---|---|
| 14.1 | Aucun dossier démo avec données réelles anonymisées — D-PILOTE-RES-001 est un fixture synthétique évident | Bloquant démo | M |
| 14.2 | Pas de mesure du temps gagné — argument de vente principal sans chiffre | Bloquant commercial | S |
| 14.3 | Roadmap écrite orientée bureau É.A. (features + valeur métier) inexistante | Bloquant commercial | S |
| 14.4 | Onboarding bureau : comptes utilisateurs, auth, gestion des É.A. par bureau — absent du code | Bloquant technique | M |

---

---

## Synthèse — Bloquants avant la démo bureau É.A.

Ce qui doit être fait avant de présenter au bureau, classé par ordre de dépendance :

```
[1] Auth + comptes utilisateurs (bureau → É.A.)
        ↓ dépend de
[2] Dossier = entité persistante séparée de la session technique
        ↓ dépend de
[3] Pipeline stoppable par checkpoint (4 gates avec log horodaté)
        ↓ dépend de
[4] Compliance B001-B007 en Python pur (moteur déterministe)
        ↓ en parallèle
[5] Import CSV JLR → scoring comparables → CHECKPOINT 2
[6] Template lettre de mandat (formulaire 5 champs, pas LLM)
[7] Extraction PDF élargie (30 champs, pas 10)
[8] Dossier démo anonymisé + chrono temps gagné
[9] Conformité Loi 25 (avocat)
```

---

## Décisions actées

| Décision | Date |
|---|---|
| Vision : évaluateur = décideur/réviseur, agents = exécutants des tâches répétitives | 2026-05-20 |
| 4 checkpoints humains (faits, comparables, réconciliation, rapport final) — pas chaque étape | 2026-05-20 |
| Flux entrée : PDF → extraction → JSON structuré → agents (plomberie existante, incomplète) | 2026-05-20 |
| Comparables : IA propose via JLR, évaluateur confirme — JLR sur chemin critique | 2026-05-20 |
| Checkpoints : confirmation horodatée (date + heure + nom É.A.), gate bloquant, jamais exportée dans le rapport | 2026-05-20 |
| OpenAI obligatoire pour la prose du rapport — dégradé gracieux si down, évaluateur complète à la main | 2026-05-20 |
| compliance-qa = moteur de règles déterministe (B001-B007 en Python pur), LLM pour avertissements seulement | 2026-05-20 |
| Modèles de rapport par type à fournir à l'agent redaction (résidentiel, commercial, etc.) | 2026-05-20 |
| data_enrichment : zonage → AMU (central), SCHL conditionnel (locatif seulement), StatCan à retirer | 2026-05-20 |
| 1 dossier = 1 session active — pas de choix de session pour l'évaluateur | 2026-05-20 |
| Import CSV JLR en V1, API JLR en V2 (partenariat à négocier) | 2026-05-20 |
| Approches par type de bien : afficher seulement les approches pertinentes — pas les 3 systématiquement | 2026-05-20 |
| Proxy approche coût : watermark obligatoire "VALEUR PROXY — non certifiable OEAQ" | 2026-05-20 |
| Lettre de mandat : formulaire 5 champs + template fixe, pas LLM | 2026-05-20 |
| Pricing : base par bureau (nb users) + crédit par usage — marge cible 30% minimum | 2026-05-20 |
| Routing LLM par tâche : GPT-4o pour rapport, GPT-4o-mini pour le reste, Python pur pour compliance | 2026-05-20 |
| Conformité Loi 25 : obligatoire avant premier client — consulter avocat (même appel que OEAQ/§6.5) | 2026-05-20 |
| Stack Vercel + Railway + Supabase : acceptable jusqu'à ~200 évaluateurs, migration cloud = session dédiée | 2026-05-20 |
| Objectif 3 mois : démo bureau É.A. avec dossier réel anonymisé + roadmap JLR/Altus pour entente ferme | 2026-05-20 |
