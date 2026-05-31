# Phase 5 — Multi-bureau, sécurité avancée & échelle

**Dépend de :** Phases 0 et 3
**Débloque :** le modèle d'affaires B2B (vente au bureau), la croissance.
**Effort :** L–XL
**Objectif :** introduire la notion de bureau (tenant), réécrire l'isolation, le tableau de bord directeur, la facturation, et préparer l'échelle. Couvre **A7 (tenant/RLS)** et la roadmap bureau.

## Périmètre
**Inclus :** modèle tenant, RLS par bureau, rôles bureau, attribution de dossiers, crédits/facturation, observabilité usage, préparation migration cloud.
**Exclus :** logique métier (P4), rapport (P3).

---

## Tâches

### T5.1 — Modèle de données tenant (bureau) — *fondation manquante*
La RLS actuelle isole par **utilisateur** (`created_by = auth.uid()`), aucune notion de bureau.
- Ajouter `bureaux` (id, nom, plan) + `bureau_membres` (user_id, bureau_id, role) ; colonne `bureau_id` sur `dossiers`/`sessions`.
- Migration `006_bureaux_tenant.sql`.
- **DoD :** chaque dossier appartient à un bureau ; chaque user appartient à un bureau.

### T5.2 — Réécriture des policies RLS par bureau
- Remplacer/compléter les policies `created_by = auth.uid()` par une logique tenant : un membre voit les dossiers de **son bureau** selon son rôle ; un `bureau_admin` voit tout le bureau ; un `evaluateur` voit ses dossiers (+ partagés selon politique).
- Mettre à jour storage RLS, documents, pins, rapport_versions, sessions.
- **Fichiers :** `supabase/migrations/007_rls_tenant.sql`, `api.py` (`session_access_allowed` tenant-aware).
- **DoD :** tests : un user d'un autre bureau n'accède à rien ; un bureau_admin voit les dossiers de ses évaluateurs.

### T5.3 — Tableau de bord directeur
- Vue bureau : dossiers par évaluateur, statuts, charge, historique centralisé, attribution/réassignation de dossiers.
- **Fichiers :** `src/app/bureau/**` (nouveau), API agrégation.
- **DoD :** un `bureau_admin` voit et attribue les dossiers du bureau.

### T5.4 — Crédits & facturation (constat business)
- Compteur d'usage par dossier/bureau ; modèle base + crédits (décision 20 mai) ; suivi coût LLM par dossier (cible marge ≥ 30 %).
- **Fichiers :** `api.py` (metering), table `usage_credits`, intégration paiement (différé si besoin).
- **DoD :** usage mesuré par bureau ; facture/relevé générable.

### T5.5 — Observabilité & audit étendu
- Métriques par bureau (dossiers/mois, temps gagné, coût LLM) ; audit d'accès déjà partiel (`append_access_audit`) → tableau de bord.
- **DoD :** métriques d'usage et d'accès consultables.

### T5.6 — Préparation migration cloud (différé ~200 évaluateurs)
- Document d'architecture cible (résidence des données Loi 25, stockage, scaling Railway→cloud).
- **Fichiers :** `docs/SCALE-MIGRATION.md`.
- **DoD :** plan de migration écrit, déclenché au seuil défini (pas avant).

---

## Critère de done de la phase
Notion de bureau en place ; isolation tenant testée ; tableau de bord directeur fonctionnel ; usage mesuré et facturable ; plan de scale documenté.
