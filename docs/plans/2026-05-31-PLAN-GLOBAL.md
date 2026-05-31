# Plan global — eval-immo vers la version finale É.A.

**Date :** 2026-05-31
**Fondé sur :** `docs/ANALYSE-ECARTS-PRODUIT-FINAL-2026-05-31.md` (audit code, 3 passes)
**Cible :** assistant exécutant toutes les tâches d'un É.A., livrable identique à un expert, l'É.A. dirige et confirme ; toutes les sources liées ; toute la connaissance dans le projet.

Ce document est la **vue d'ensemble**. Chaque phase a son propre plan détaillé dans `docs/plans/2026-05-31-phase-N-*.md`. Les 7 phases couvrent **l'intégralité** des constats de l'audit (matrice de couverture en §4).

---

## 1. Principes directeurs (invariants de toutes les phases)

1. **Human-in-the-loop non négociable** : l'É.A. confirme les 4 checkpoints ; aucune certification automatique. Rien ne contourne les gates.
2. **Déterministe > LLM pour tout ce qui engage la conformité** : valeurs, conformité, conflit d'intérêts, présence des éléments obligatoires = Python pur. Le LLM rédige la prose et raisonne sur données structurées, il ne décide pas.
3. **Aucune donnée inventée** : tout chiffre/affirmation est rattaché à une source (donnée ou normative) ou marqué « à compléter par l'É.A. ». Pas de placeholder silencieux, pas d'invention d'ajustements.
4. **Sources liées de bout en bout** : données (source_id, diagnostics) ET normatif (citation page/section vers la base de connaissances).
5. **Fail-closed en production** : pas de token → pas d'accès ; mode dégradé (LLM down) explicite et signalé, jamais un faux livrable.
6. **Le savoir vit dans le dépôt** et atteint réellement les agents (pas seulement en métadonnées).
7. **Pas de régression de portée** : le résidentiel standard reste fonctionnel à chaque phase.

---

## 2. Les 7 phases

| Phase | Titre | Objectif central | Dépend de | Effort | Débloque |
|---|---|---|---|---|---|
| **0** | Assainissement, conformité & sécurité immédiate | Retirer le contenu non conforme, fail-closed, conflit déterministe, lettre unique, Loi 25, migrations prod | — | S–M | Usage réel sûr |
| **1** | Connaissance active (savoir + sources) | `analysis.md` atteint les agents ; RAG + citations normatives ; corpus dans le dépôt | 0 | L | Qualité & traçabilité |
| **2** | Cœur analytique (valeur comme un É.A.) | Grille d'ajustements moteur, AMU réelle, TGA/coûts marché, source de calcul unique | 1 | L–XL | Rapport crédible |
| **3** | Rapport d'expert | 16 éléments garantis, grille au rapport, inspection, repli complet, export certifiable | 2 | M–L | Livrable = É.A. |
| **4** | Couverture métier | Mandats spéciaux (succession, LFM, expropriation, liquidation) + types de biens | 2, 3 | XL | « toutes les tâches » |
| **5** | Multi-bureau & échelle | Tenant bureau, RBAC bureau, tableau directeur, crédits/facturation, scale | 0, 3 | L–XL | B2B / revenus |
| **6** | Qualité & dette | Découpe `api.py`, CI mocks + E2E, unification TS/Python, dead code, observabilité | transverse | M | Maintenabilité |

> Phase 6 est **transverse** : ses tâches s'exécutent en continu, mais sont regroupées pour ne rien oublier.

---

## 3. Chemin critique et séquencement

```
P0 (assainir/sécuriser) ─► P1 (savoir actif + RAG) ─► P2 (cœur analytique) ─► P3 (rapport expert)
                                                                                   │
                                          P5 (multi-bureau) ◄── dépend de P0+P3 ───┤
                                          P4 (mandats/types) ◄── dépend de P2+P3 ──┘
P6 (qualité/dette) : en parallèle continu, jalons à la fin de P2 et P3.
```

- **Ordre recommandé** : P0 → P1 → P2 → P3, puis P4 et P5 en parallèle, P6 en continu.
- **Démo bureau É.A.** (objectif 3 mois, résidentiel) atteignable dès **fin P3** (P4/P5 = post-démo).
- **Premier client payant** exige P0 complet (Loi 25 + sécurité) + P3 (livrable) + le socle P5 d'isolation s'il y a plus d'un É.A.

---

## 4. Matrice de couverture — chaque constat de l'audit → une phase

| Réf. audit | Constat | Phase |
|---|---|---|
| A1 | `analysis.md` inerte (pipeline + assistant) | **1** |
| C | Sources normatives non liées, corpus hors dépôt, pas de RAG | **1** |
| A2 | Grille d'ajustements absente du moteur | **2** |
| A3 | AMU = tampon (zonage non utilisé) | **2** |
| A5 | Coût/revenu non certifiables (tables, TGA marché) | **2** |
| A12 (calculs) | Logique de valeur dupliquée TS/Python | **2** (unification) / **6** |
| A9 | 16 éléments non garantis, grille non alimentée, repli stub | **3** |
| A8 | Capture d'inspection absente (élément 14) | **3** |
| A9 (export) | Export certifiable (signature, n° permis, sceau) | **3** |
| A4 | Mandats spéciaux non codés | **4** |
| A4 (biens) | Types de biens spécialisés | **4** |
| A6 | Comparables : visibilité diagnostics, robustesse SIRF | **2** (visibilité) / **4** (sources étendues) |
| A7 (Loi 25) | Conformité Loi 25 | **0** |
| A7 (migrations) | Migrations Supabase non appliquées prod | **0** |
| A7 (fail-closed) | Runtime ouvert si token absent | **0** |
| A7 (CORS) | CORS prod | **0** (vérif/durcissement) |
| A7 (tenant/RLS) | RLS mono-utilisateur, pas de bureau | **5** |
| conflit | Détection conflit LLM-only | **0** |
| lettre | Double chemin lettre de mandat | **0** |
| A11 | Sur-ingénierie `data_enrichment`, scores hors OEAQ dans AMU/rapport | **0** (sortir du rapport) / **6** (élaguer le module) |
| A12 (api.py) | `api.py` monolithe 256 Ko | **6** |
| A12 (dead code) | ThemeToggle, TabBar | **6** |
| A13 | CI mocks réseau, E2E | **6** |
| Assistant | Outils limités (`fetch_artifact` seul), pas d'action/ré-exécution | **1** (search_knowledge) / **4** (tool calling étendu) |

**Aucun constat de l'audit n'est hors couverture.**

---

## 5. Définition de « version finale » (critères de sortie globaux)

- [ ] Un dossier résidentiel réel anonymisé traverse les 4 checkpoints et produit un rapport conforme aux 16 éléments, avec grille d'ajustements réelle et sources (données + normatives) liées.
- [ ] Le savoir É.A. (MEFQ, NPP, CUSPAP, AMU, approches) est dans le dépôt et cité dans le rapport.
- [ ] Au moins les mandats résidentiels + succession + financement + contestation LFM sont exécutés correctement par le moteur.
- [ ] Conformité Loi 25 documentée ; isolation multi-bureau active ; runtime fail-closed.
- [ ] Mode dégradé (LLM down) ne produit jamais un faux livrable.
- [ ] CI verte (backend + frontend + E2E), `api.py` modularisé, source de calcul unique.

---

## 6. Risques transverses

- **Dépendances externes non techniques** (avocat Loi 25/§6.5, accès Altus/JLR, contact É.A. pour modèles réels) — démarrer en parallèle dès P0.
- **Fragilité du scraping SIRF** (changement DOM) — surveiller, prévoir repli.
- **Coût/latence LLM** avec injection de connaissance + RAG — mesurer par dossier (cible < 0,10 $).
- **Régression** à chaque phase — la suite de tests (P6) doit précéder les gros refactors.

---

*Plans détaillés : `phase-0` à `phase-6` dans le même répertoire.*
