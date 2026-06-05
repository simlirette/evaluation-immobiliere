# Runbook beta E.A. v1

Objectif: permettre a un evaluateur agree invite d'utiliser eval-immo sur un lien beta ferme avec des dossiers anonymises, sans certification automatique et sans conservation de documents bruts avant contrat.

## Definition de pret

Le lien beta peut etre transmis seulement si:

- `GET /beta/readiness` retourne `status=PRET_LIEN_EA`.
- `python scripts/check_closed_beta_launch.py <evidence.json>` retourne `READY_FOR_CLOSED_BETA`.

Controles bloquants:

- `hosted_url_configured`: `EVAL_IMMO_BETA_HOSTED_URL` pointe vers l'URL HTTPS partagee.
- `token_auth_enabled`: `EVAL_RUNTIME_API_TOKEN` est defini et transmis hors canal a l'invite.
- `allowed_origin_configured`: `EVAL_RUNTIME_ALLOWED_ORIGIN` est l'origine HTTPS exacte du frontend.
- `openai_configured`: `OPENAI_API_KEY` est configuree.
- `deploy_readiness_gate`: le gate `/readiness` ne contient aucun controle critique.
- `anonymized_acceptance_fixture`: la fixture d'acceptation anonymisee reste valide.
- `live_ai_provider_policy`: le runtime live Anthropic reste desactive par defaut avant contrat.
- `closed_beta_launch_evidence`: la preuve production/privacy/E.A./dossiers/source/launch est complete.
- `professional_workfile_gate`: aucun blocage dans le paquet du dossier pilote.

## Variables d'environnement beta

```text
APP_ENV=production
EVAL_RUNTIME_API_TOKEN=<token fort transmis hors canal>
EVAL_RUNTIME_ALLOWED_ORIGIN=https://<frontend-vercel>
EVAL_IMMO_BETA_HOSTED_URL=https://<frontend-vercel-ou-domaine-beta>
EVAL_IMMO_BETA_RETENTION_DAYS=14
OPENAI_API_KEY=<cle configuree dans Railway>
OPENAI_MODEL=<modele retenu>
SESSIONS_DIR=/data/sessions
DATA_CACHE_DIR=/data/data_cache
```

Ne pas definir ces variables pour une beta sans contrat ou sans decision operateur:

```text
EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME
EVAL_IMMO_RUN_LIVE_SMOKE
```

## Parcours invite

1. Ouvrir le lien Vercel beta.
2. Se connecter via Supabase si l'auth production est active.
3. Verifier que l'utilisateur est nomme dans la beta et que le role attendu est applique.
4. Creer ou ouvrir un dossier anonymise.
5. Lire les limites beta et accepter les conditions.
6. Inspecter les faits, sources, comparables, ajustements, checkpoints, rapport et paquet.
7. Saisir une revue interne avant toute generation de paquet V1.
8. Ne signer aucun rapport sans validation humaine E.A. hors outil.

## Regles donnees

- Les dossiers beta doivent etre anonymises avant saisie dans l'outil.
- Les champs evidents `email`, `telephone`, `nom`, `client`, `proprietaire` ou des motifs d'adresse precise bloquent `/beta/intake`.
- Les documents bruts (`content`, `raw_text`, `base64`, `pdf_base64`, etc.) sont refuses par defaut avant contrat.
- Chaque session beta ecrit `runtime_sessions/<session_id>/beta_intake.json` avec l'attestation, le statut anonymisation, le delai de retention et le manifeste documentaire.

## Verification avant invitation

Depuis `backend/`:

```bash
python scripts/check_deploy_readiness.py --production --json
python scripts/verifier_beta_ea_readiness_v1.py --strict-link
python scripts/run_ea_acceptance.py tests/fixtures/acceptance/ea_acceptance_anonymized_residential.json --json
python scripts/smoke_beta_ea_link_v1.py --base-url https://<frontend-vercel> --token <token-runtime> --role supervisor --require-external-ready
python scripts/check_closed_beta_launch.py ..\_audit\2026-06-02\closed_beta_launch_evidence.json --json
python -m pytest tests/ -q
```

Verifier aussi:

```text
GET /health
GET /readiness
GET /beta/readiness
GET /auth/status
GET /product
```

Le smoke HTTP verifie `/health`, `/auth/status`, `/product`, `/beta/readiness`, `/beta/intake` et la presence de `beta_intake` dans `/session/summary`.

## Evidence de lancement

Copier le template:

```powershell
copy _audit\2026-06-02\closed_beta_launch_evidence.template.json _audit\2026-06-02\closed_beta_launch_evidence.json
```

Remplir uniquement des informations non secretes:

- URLs HTTPS Vercel/Railway.
- Statuts de readiness/smoke.
- Approbations privacy/legal sous forme booleenne.
- Id E.A. non identifiant.
- Ids de dossiers anonymises.
- Chemins vers manifestes ou rapports d'acceptance.
- Decisions explicites sur SIRF, JLR, approche cout et donnees insuffisantes.

Pour chaque paquet E.A., verifier aussi:

```text
package_v1/professional_workfile_gate.json
package_v1/npp_compliance_matrix.json
package_v1/source_provenance.json
```

Les warnings acceptes doivent etre notes comme limites beta. Les blocages ne
peuvent pas rester ouverts avant partage du lien.

Le fichier ne doit pas contenir de token, cle API, nom client, adresse civique brute, telephone ou courriel.

## Decision

- `PRET_LIEN_EA` + `READY_FOR_CLOSED_BETA`: le lien beta ferme peut etre partage aux utilisateurs nommes.
- `BETA_LIEN_BLOQUE`: ne pas partager; fermer les controles listes dans `blocking_checks`.
- `BLOCKED`: ne pas partager; fermer les controles listes par `check_closed_beta_launch.py`.
- `ready_for_local_anonymized_beta=true`: utilisable localement pour un dry-run anonymise, mais pas encore pret comme lien externe si l'URL, l'auth ou l'evidence externe manque.

## Stop conditions

Arreter ou ne pas lancer la beta si:

- Un P0 securite, privacy, professionnel ou workflow reste ouvert.
- Les sessions ne persistent pas apres redeploiement.
- Le BFF Vercel ne peut pas joindre Railway.
- Le runtime est accessible sans token.
- Un dossier contient des identifiants directs.
- Le pilote E.A. ne valide pas l'utilite du workflow.
