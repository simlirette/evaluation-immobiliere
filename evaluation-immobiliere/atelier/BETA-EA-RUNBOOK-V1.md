# Runbook beta E.A. v1

Objectif: permettre a un evaluateur agree invite d'utiliser eval-immo sur un lien beta ferme avec des dossiers anonymises, sans certification automatique et sans conservation de documents bruts avant contrat.

## Definition de pret

Le lien beta peut etre transmis seulement si `GET /beta/readiness` retourne `status=PRET_LIEN_EA`.

Controles bloquants:

- `hosted_url_configured`: `EVAL_IMMO_BETA_HOSTED_URL` pointe vers l'URL HTTPS partagee.
- `token_auth_enabled`: `EVAL_RUNTIME_API_TOKEN` est defini et transmis hors canal a l'invite.
- `release_candidate_gate`: le gate release candidate retourne `PRET_GO_LIVE_CONTROLE`.
- `product_review_package_workflow`: le produit reste bloque production mais utilisable en beta controlee.
- `anonymization_gate`: l'audit anonymisation ne contient aucun finding bloquant.
- `live_ai_provider_policy`: le runtime live Anthropic reste desactive par defaut avant contrat.

## Variables d'environnement beta

```text
EVAL_RUNTIME_API_TOKEN=<token fort transmis hors canal>
EVAL_IMMO_BETA_HOSTED_URL=https://<domaine-beta>
EVAL_IMMO_BETA_RETENTION_DAYS=14
```

Ne pas definir ces variables pour une beta sans contrat:

```text
EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME
EVAL_IMMO_RUN_LIVE_SMOKE
```

## Parcours invite

1. Ouvrir `/product`.
2. Saisir le role `evaluator` ou `supervisor` et le token fourni.
3. Lire les limites beta dans le bloc `Beta E.A.`.
4. Cocher les deux attestations: conditions beta et anonymisation.
5. Lancer une fixture synthetique ou coller un dossier JSON anonymise.
6. Inspecter `Dossier`, `Knowledge`, `Evaluateur AI` et `Paquet V1`.
7. Saisir une revue interne si le dossier doit generer un paquet V1.

## Regles donnees

- Les dossiers beta doivent etre anonymises avant saisie dans l'outil.
- Les champs evidents `email`, `telephone`, `nom`, `client`, `proprietaire` ou des motifs d'adresse precise bloquent `/beta/intake`.
- Les documents bruts (`content`, `raw_text`, `base64`, `pdf_base64`, etc.) sont refuses par defaut avant contrat.
- Chaque session beta ecrit `runtime_sessions/<session_id>/beta_intake.json` avec l'attestation, le statut anonymisation, le delai de retention et le manifeste documentaire.

## Verification avant invitation

```bash
python evaluation-immobiliere/outils/verifier_release_candidate_v1.py --strict
python evaluation-immobiliere/outils/verifier_statut_phases_projet_v1.py
python evaluation-immobiliere/outils/auditer_anonymisation_v0.py
python evaluation-immobiliere/outils/verifier_beta_ea_readiness_v1.py --strict-link
python -m unittest discover -s evaluation-immobiliere/tests -p "test_*.py" -v
```

Puis demarrer l'API:

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py --host 127.0.0.1 --port 8787
```

Verifier:

```text
GET /beta/readiness
GET /product/summary
GET /auth/status
```

Smoke HTTP complet:

```bash
python evaluation-immobiliere/outils/smoke_beta_ea_link_v1.py --base-url https://<domaine-beta> --token <token> --role supervisor --require-external-ready
```

Le smoke verifie `/health`, `/auth/status`, `/product`, `/beta/readiness`,
`/beta/intake` et la presence de `beta_intake` dans `/session/summary`.

## Deploiement minimal

Le repo fournit un `Procfile` compatible avec les plateformes qui exposent
`PORT`:

```text
web: python outils/lancer_api_v0.py --host 0.0.0.0
```

Le serveur lit aussi `EVAL_IMMO_API_HOST`, `EVAL_IMMO_API_PORT` ou `PORT` si
les arguments CLI ne sont pas fournis. Le proxy HTTPS/IAM reste a porter par la
plateforme de deploiement.

## Decision

- `PRET_LIEN_EA`: le lien beta ferme peut etre partage.
- `BETA_LIEN_BLOQUE`: ne pas partager; fermer les controles listes dans `blocking_checks`.
- `ready_for_local_anonymized_beta=true`: utilisable localement pour un dry-run anonymise, mais pas encore pret comme lien externe si l'URL ou l'auth manque.
