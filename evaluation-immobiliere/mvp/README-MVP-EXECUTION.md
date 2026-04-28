# MVP execution — point de départ concret

## Ce qui est prêt maintenant
- Contrats d'agents v0: `AGENT-CONTRACTS-V0.yaml`
- Checklist conformité v0: `CHECKLIST-CONFORMITE-V0.md`
- Outil de priorisation automatique: `../outils/prioriser_mvp.py`
- Runner dry-run: `../outils/dry_run_pipeline_v0.py`

## Commandes utiles

```bash
python evaluation-immobiliere/outils/prioriser_mvp.py
python evaluation-immobiliere/outils/valider_fixtures_v0.py
python evaluation-immobiliere/outils/dry_run_pipeline_v0.py
python evaluation-immobiliere/outils/resumer_dry_run_v0.py
```

## Prochaine étape opérationnelle
1. Remplir `atelier/MATRICE-PRIORISATION-MVP.csv` avec des valeurs.
2. Lancer le script de scoring.
3. Exécuter le dry-run sur fixtures.
4. Réviser les rapports dans `tests/reports/`.
