# State — eval-immo

_Updated: 2026-06-12 | HEAD: 692948e (master, poussé) | PROD front: eval-immo.vercel.app = 9b89cd9 | PROD back: blissful-reverence (Railway)_

## Current Goal

**Refonte frontend P1-P6 TERMINÉE et DÉPLOYÉE.** Suite P6 : opérationnalisation prod backend.

## Session 2026-06-12 (en cours)

- Vérifs prod : BFF Vercel 401 propre ; backend Railway = service **blissful-reverence** (URL blissful-reverence-production-ef1d.up.railway.app, volume /data) — image du 06-10 incluait déjà le fix Infolot ✓, fail-closed ✓.
- **Découverte** : service Railway `evaluation-immobiliere` = frontend Next REDONDANT (Vercel fait ce travail) avec « Deploy failed » sur chaque push — à supprimer/désactiver (décision user).
- Readiness prod : 2 warnings — **MAMH_CACHE vide** et **SIRF creds absents**.
- **Nouveau (692948e, poussé)** : endpoint `POST/GET /ops/mamh/provision` (runtime_write/read, thread background, idempotent, statut détaillé) + 4 tests ; suite 1041 ✅. Railway redéploie ; monitor armé → ensuite POST provisioning, suivre jusqu'à ok, re-checker readiness.
- DEPLOYMENT.md mis à jour (provisioning à distance) — commit local, push différé pour ne pas retrigger le build en cours.
- Provisioning exécuté en prod : **partial** — gatineau OK ; laval/longueuil/quebec/sherbrooke = « No space left on device » (**volume Railway 500 MB trop petit**, besoin ~2-5 GB) ; Montréal CSV = 429 rate-limit portail (retry après).
- **Actions user** : (1) Dashboard Railway → volume blissful-reverence → **Grow** (5 GB) ; ensuite re-POST /ops/mamh/provision (je peux le faire). (2) Creds SIRF en prod. (3) Supprimer le service Railway doublon `evaluation-immobiliere` (deploy failed à chaque push).

## Refonte (12 commits, 2026-06-10)

P1 shell+primitives (8df1602) · P2 6 écrans simples (57fead6, 2af03f3) · P3 Mes-dossiers (db74fc7) · P4 wizard (169c242) · P5a coquille workspace (49e7a8d) · P5b panels+capsule (d9fdbd6) · P5c onglet Dossier+Activité (09cb799) · P6 QA+fixes (9b89cd9).

QA P6 : backend local 8796 + dossier pilote — tous les écrans vérifiés avec données réelles, zéro erreur console. Déploiement : `npx vercel deploy --prod` → READY, alias eval-immo.vercel.app, target production.

## À surveiller / suites

- **Backend Railway** : master poussé (inclut fix Infolot ArcGIS) — vérifier que Railway a redéployé (sinon redéploiement manuel) ; sans quoi les comparables publics prod restent cassés.
- origin/main très en retard (mi-mai) — la prod vit sur master + CLI deploy ; envisager d'aligner main ou de changer la branche par défaut.
- Améliorations différées : endpoint recherche registre (wizard), liste dossiers enrichie (année/superficie/valeur/client), endpoints bibliothèque/modèles/archives réels, rendu markdown dans le tiroir capsule, SSO Microsoft réel, sign-up OEAQ réel.
- Lint : 1 erreur pré-existante `src/hooks/useFetch.ts:27` (react-hooks/use-memo).

## Open (hors refonte)

- MAMH cache prod à confirmer · smoke SIRF (payant) · corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs-rajustement) + réindex RAG · T3.6 vrai dossier É.A. · avis Loi 25 · OEAQ §6.5 · Stripe.
