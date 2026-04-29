# Resume simple - ou on en est

## Ce qui est fait

- La base projet est en place: regles, pipeline, contrats d'agents, schemas et fixtures.
- Le mini moteur runtime lit le pipeline, execute les etapes et ecrit des artefacts par dossier.
- Les controles QA detectent les sources manquantes, ajustements sensibles, incoherences d'unites, ventes futures et warnings de confiance.
- Le journal d'audit est alimente a chaque etape et a chaque ecriture d'artefact.
- Une API locale minimale existe maintenant pour lancer un dossier sans UI complete.

## Ce que ca permet

Tu peux faire une demo interne en trois temps:

1. Verifier la coherence du pipeline et des AgentConfig.
2. Lancer la simulation sur les fixtures.
3. Lancer l'API locale et demarrer une execution via `POST /start`.

## Commandes utiles

```bash
python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py
python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py
python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py
python evaluation-immobiliere/outils/lancer_api_v0.py
```

## Etat des tests runtime

Derniere simulation locale:

- 5 cas
- 1 `PRET_REVISION_FINALE`
- 1 `BROUILLON`
- 3 `A_REVOIR`
- 122 evenements runtime/audit

## Prochaine etape logique

Preparer 2-3 dossiers anonymises reels et les envoyer dans l'API v0 pour comparer les sorties avec une revue evaluateur.
