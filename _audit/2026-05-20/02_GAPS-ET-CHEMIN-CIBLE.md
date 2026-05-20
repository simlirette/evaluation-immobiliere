# Audit eval-immo — 02 GAPS ET CHEMIN CIBLE
**Date :** 2026-05-20

---

## Catégorie A — Bloquants critiques (le système ne peut pas produire un rapport certifiable)

### A1 — Approches coût et revenu sont des proxies sur les mêmes comparables
**Dépendance :** `engine/valuation.py`, `mvp/MOTEUR-CALCUL-VALEUR-V0.yaml`  
**Problème :** `approche_cout` = `mean(prix_vente_comparables)`. `approche_revenu` = `median(prix_vente_comparables)`. Ce sont des variantes de l'approche comparative avec la même base de données. Un OEAQ ne peut pas signer un rapport où "approche par le coût" signifie la moyenne des ventes récentes.  
**Variables d'environnement requises :** Aucune (problème algorithmique)  
**Effort :** XL — tables de coûts de construction (Marshall & Swift ou Altus) + modèle de dépréciation physique/fonctionnelle/économique + valorisation terrain séparée. Pour revenu : TGA extrait du marché, RNE.  
**Aston-réutilisable :** Build complet  
**Impact si laissé :** Rapport non certifiable par É.A. — deux des trois approches sont des fictions labellisées.

### A2 — Compliance-qa est un LLM, pas un moteur de règles
**Dépendance :** `integration/AGENTCONFIG-COMPLIANCE-QA-V0.yaml`, `engine/runtime.py`  
**Problème :** Les règles B001-B007 (bloquantes) et W001-W005 (avertissements) sont dans un `system_prompt`. Sans OPENAI_API_KEY, le step produit un artefact vide ou générique. Avec API key, le LLM peut ignorer ou halluciner. La règle B002 (comparable sans source_id) est vérifiable en code pur — elle ne l'est pas.  
**Variables d'environnement requises :** `OPENAI_API_KEY` pour fonctionnement actuel  
**Effort :** M — encoder B001-B007 comme fonctions Python pures appelées avant ou après le LLM. Le LLM reste pour les nuances non-encodables (B006 : "conclusion non soutenue").  
**Aston-réutilisable :** Partiel — logique de gate/blocage existe dans Aston  
**Impact si laissé :** Un dossier peut passer compliance sans que B002/B003/B004/B005 soient vérifiés en l'absence d'API key. En production avec API key, non-reproductible.

### A3 — Connecteurs de données externes absents (Centris, JLR, registre foncier live)
**Dépendance :** `engine/tools.py::search_comparables()`, `engine/data_enrichment.py`  
**Problème :** `search_comparables()` opère sur `case["comparables"]` — l'évaluateur doit saisir manuellement les comparables dans le JSON. Aucun connecteur Centris, JLR, Matrix, GESTIM, ou registre foncier live. `data_enrichment.py` couvre StatCan + rôle municipal CSV/XML uniquement.  
**Variables d'environnement requises :** Credentials Centris API, JLR API — ni documentées ni présentes dans `.env.example`  
**Effort :** XL — chaque connecteur est un projet d'intégration distinct avec authentification, parsing, cache, normalisation des adresses.  
**Aston-réutilisable :** Build complet  
**Impact si laissé :** L'évaluateur saisit les comparables à la main. L'outil d'assistance devient un outil de mise en forme, pas d'analyse.

### A4 — Tests T01-T05 inexistants
**Dépendance :** `backend/tests/runtime/`, `TEST-PLAN-V0.md`  
**Problème :** Le dossier `tests/runtime/` est absent. `TEST-PLAN-V0.md` est introuvable. Les 5 cas de test cités dans les spécifications ne peuvent pas être exécutés.  
**Effort :** S — créer le TEST-PLAN-V0.md et les 5 fixtures YAML correspondantes avec assertions.  
**Aston-réutilisable :** Partiel  
**Impact si laissé :** La régression n'est pas détectable sur les cas pilotes nommés.

---

## Catégorie B — Bloquants conformité OEAQ

### B1 — Validation humaine sans gate d'interface
**Dépendance :** `engine/valuation.py` ligne 11, `api.py`  
**Problème :** `validation_humaine: true` est vérifié dans le calcul, mais un dossier sans ajustements (liste vide) passe sans blocage. Aucun endpoint n'exige que l'évaluateur ait validé chaque ajustement ≥ 25 000 $ avant de déclencher `compliance-qa`. La règle B005 OEAQ est donc contournable.  
**Effort :** S — ajouter un check avant l'étape valuation-draft : si ajustement ≥ 25 000 $ et `validation_humaine != true`, émettre un blocage.  
**Aston-réutilisable :** Partiel  
**Impact si laissé :** Non-conformité B005 silencieuse.

### B2 — Conformité OEAQ OEAQ003 (unités m²) non vérifiée en code
**Dépendance :** `engine/tools.py::_score_penalties()`, `engine/runtime.py`  
**Problème :** `_score_penalties()` pénalise les `unit_mismatch` entre sujet et comparable, mais OEAQ003 exige les m² (pas les pi²). Le fixture pilote utilise `pi2`. Aucun check en code pour forcer la conversion ou bloquer si `unit != "m2"`.  
**Effort :** S — ajouter une validation déterministe dans data-facts ou compliance-qa.  
**Aston-réutilisable :** Build  
**Impact si laissé :** Non-conformité OEAQ003 systématique sur tous les dossiers en pi².

### B3 — Numéro de membre OEAQ (règle B007) non vérifié
**Dépendance :** `integration/AGENTCONFIG-COMPLIANCE-QA-V0.yaml`  
**Problème :** B007 est dans le prompt LLM. Le `case` dict n'a pas de champ `numero_membre_oeaq`. Le runtime ne peut pas vérifier B007 sans API key — et même avec, c'est le LLM qui décide.  
**Effort :** S — ajouter `numero_membre_oeaq` au schéma du case, vérifier sa présence dans compliance-qa déterministe.  
**Aston-réutilisable :** Build  
**Impact si laissé :** Rapport signable par qui que ce soit.

### B4 — Fichiers UI absents (endpoints HTTP 404)
**Dépendance :** `api.py` lignes 33-37, `backend/ui/`  
**Problème :** `api.py` définit des routes HTTP vers `ui/pilote_api.html`, `ui/product_cockpit.html`, `ui/ops_cockpit.html`, `ui/evaluateur_review.html`, `ui/auth_client.js` — tous absents. Ces routes retournent 500 ou 404.  
**Effort :** S — soit créer les fichiers HTML, soit supprimer les routes mortes.  
**Aston-réutilisable :** N/A  
**Impact si laissé :** API partiellement cassée — les cockpits ops et évaluateur ne fonctionnent pas.

---

## Catégorie C — Bloquants industrialisation

### C1 — Tests DataEnrichment font des appels réseau réels
**Dépendance :** `tests/test_pure.py::TestDataEnrichment_*`  
**Problème :** Les tests `TestDataEnrichment_EnrichCase::test_enrich_case_never_raises` etc. appellent StatCan WDS API et Nominatim sans mock. En CI sans réseau (ou réseau lent), ils bloquent indéfiniment.  
**Variables d'environnement requises :** Accès réseau à `www150.statcan.gc.ca` et Nominatim  
**Effort :** S — mocker les appels HTTP dans les tests avec `responses` ou `httpx-mock`.  
**Aston-réutilisable :** Build  
**Impact si laissé :** CI instable ou timeout en environnement réseau limité.

### C2 — Un test FAIL dans test_pure.py
**Dépendance :** `tests/test_pure.py::TestExportRapport_InvalidFormat::test_format_pdf_raises_value_error`  
**Problème :** Le test attend `ValueError` sur format "pdf" mais `api.py:972` lève `FileNotFoundError` quand `brouillon_rapport.md` est absent. L'exception levée est incorrecte — le message d'erreur devrait indiquer que "pdf" n'est pas un format invalide, mais que le rapport est absent.  
**Effort :** XS — corriger le message ou l'exception dans `api.py`.  
**Aston-réutilisable :** N/A  
**Impact si laissé :** CI échoue sur ce test.

### C3 — `backend/schemas/` et `backend/mvp/PIPELINE-IO-SCHEMAS/` vides
**Dépendance :** `api.py` ligne 40 `KNOWLEDGE_API_SCHEMA_PATH`  
**Problème :** Les schémas JSON formels ne sont pas générés. La validation de session contre un schéma est impossible.  
**Effort :** M — générer les schémas JSON à partir de `CONTRATS-DONNEES-V0.yaml`.  
**Aston-réutilisable :** Build  
**Impact si laissé :** Validation de payload non typée — erreurs de structure silencieuses.

### C4 — `data_enrichment.py` : rôle municipal CSV 72 MB absent
**Dépendance :** `engine/data_enrichment.py` commentaire ligne 6  
**Problème :** Le CSV MAMH (`data_cache/role_mtl.csv`) n'est pas présent. Le code le gère gracieusement (fallback), mais la fonctionnalité n'est pas accessible sans un script de téléchargement documenté.  
**Effort :** S — ajouter un script de téléchargement ou documenter la procédure dans README.  
**Aston-réutilisable :** Build  
**Impact si laissé :** Enrichissement rôle municipal non fonctionnel par défaut.

### C5 — Fichier orphelin avec chemin Windows
**Dépendance :** `C:Userssimoneval-immosession-log.md` à la racine  
**Problème :** Un fichier avec un chemin Windows transformé en nom de fichier existe à la racine du projet. Artefact de bug de création de fichier. Confusant et indicateur d'un incident passé.  
**Effort :** XS — supprimer le fichier.  
**Impact si laissé :** Confusion et indicateur de problème non résolu.

---

## Catégorie D — Améliorations différables

### D1 — Approches géospatiales : distance calculée manuellement par l'évaluateur
Le champ `distance_km` dans les comparables est saisi manuellement. Un calcul Haversine depuis les adresses améliorerait la précision mais n'est pas bloquant.

### D2 — `valuation.py::approche_fta` non implémentée
L'approche FTA (flux de trésorerie actualisés) est listée dans le skill `analyse-approche-fta` et dans les méthodes optionnelles, mais aucune fonction FTA n'existe dans `valuation.py`. Différable car applicable uniquement aux mandats complexes.

### D3 — Supabase queries absentes
`src/lib/supabase/queries/` est vide selon l'inventaire. La couche de requêtes DB frontend n'est pas implémentée. Différable si le mock est suffisant pour les démos.

### D4 — Convergence inter-approches non vérifiée (CONF007)
`CONTRACT_CHECKS_BY_ARTIFACT` référence `CONF007` (divergence inter-approches > 35%) mais avec des proxies coût/revenu sur les mêmes données, CONF007 ne peut jamais se déclencher correctement.

---

## Schéma textuel du chemin critique

```
[État actuel]
Pipeline déterministe 7 étapes fonctionnel
OCR PDF + Vision opérationnel
Orchestrateur + scoring comparables opérationnel
76+ tests backend PASS

     │
     ▼
[Étape 1 — Urgence conformité] (S/M)
- Encoder B001-B007 en code Python pur (compliance-qa déterministe)
- Ajouter gate validation humaine ajustements ≥ 25 000 $
- Ajouter champ numero_membre_oeaq au schéma

     │
     ▼
[Étape 2 — Approche coût réelle] (XL)
- Tables de coûts de construction (Marshall & Swift ou proxy MAMH)
- Modèle de dépréciation physique basique (âge effectif / durée vie)
- Valorisation terrain séparée (rôle municipal comme proxy)

     │
     ▼
[Étape 3 — Données réelles] (XL)
- Connecteur Centris (scraping ou API)
- Connecteur registre foncier (BDIMMO ou accès direct)
- search_comparables() branché sur source externe

     │
     ▼
[Production certifiable]
```

---

## 3 prochaines actions concrètes

### Action 1 — Encoder les règles OEAQ bloquantes en code Python (S, 2-3 jours)

**Justification :** C'est le seul gap dont le résultat est directement observable dans un rapport : sans B002/B003/B004 en code, un dossier avec un comparable sans source passe en production. C'est vérifiable, démontrable, et ne dépend d'aucune donnée externe.

**Fichier cible :** Créer `engine/compliance_rules.py` avec fonctions pures :
- `check_b001(case)` : dossier_id, date_reference, adresse présents
- `check_b002(case)` : tous comparables et ajustements ont source_id
- `check_b003(case)` : date_vente ≤ date_reference pour tous comparables
- `check_b004(case)` : unités cohérentes entre sujet et comparables
- `check_b005(case)` : ajustements ≥ 25 000 $ ont validation_humaine: true

Appeler ces fonctions dans `runtime.py` avant de lancer `compliance-qa`.

### Action 2 — Mocker les appels réseau dans TestDataEnrichment (XS, < 1 jour)

**Justification :** C'est la cause du blocage CI. Sans ce fix, `pytest tests/` ne termine jamais en environnement hors ligne. Priorité opérationnelle.

**Fichier cible :** `backend/tests/test_pure.py` — patcher `httpx.get` et `urllib.request.urlopen` avec `unittest.mock.patch` dans les tests DataEnrichment.

### Action 3 — Corriger le test FAIL + supprimer les fichiers morts (XS, < 2h)

**Justification :** Un test FAIL dans la suite principale est un signal de bruit — il masque les vraies régressions. Les routes HTTP mortes (`ui/*.html`) retournent 500 et donnent une fausse impression de fonctionnement.

**Fichiers cibles :**
- `tests/test_pure.py` ligne 1389 : le test doit tester `FileNotFoundError` ou `api.py` doit lever `ValueError` avec un message correct sur l'absence de rapport.
- `C:Userssimoneval-immosession-log.md` : supprimer.
- `api.py` lignes 33-37 : retirer ou stub les routes UI si `ui/` n'existe pas.
