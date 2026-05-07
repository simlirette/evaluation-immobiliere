# evaluation-immobiliere

Ce dossier regroupe les artefacts de demarrage et le runtime v0 du projet **evaluation-immobiliere**.

## Ce qui est disponible

- Cadrage metier et atelier evaluateurs dans `atelier/`
- Contrats MVP, schemas, regles et checklist dans `mvp/`
- Configs d'agents et pipeline dans `integration/`
- Skills agents projet dans `skills/`
- Moteur local dans `engine/`
- Outils CLI dans `outils/`
- Fixtures synthetiques et rapports de verification dans `tests/`
- API locale et cockpit produit dans `api.py`
- Collecte et compilation des reponses evaluateurs dans `atelier/`

## Commandes utiles

```bash
python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py
python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py
python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py
python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py
python evaluation-immobiliere/outils/prioriser_mvp.py
python evaluation-immobiliere/outils/generer_registre_skills.py
python evaluation-immobiliere/outils/verifier_readiness_skills_v0.py
python evaluation-immobiliere/outils/verifier_contrat_redaction_skills_v0.py
python evaluation-immobiliere/outils/verifier_contrats_skills_agents_v0.py
python evaluation-immobiliere/outils/verifier_contrats_artefacts_agents_v0.py
python evaluation-immobiliere/outils/verifier_homologation_metier_v0.py
python evaluation-immobiliere/outils/verifier_preuve_runtime_skills_v0.py
python -m unittest evaluation-immobiliere/tests/test_tools_v0.py evaluation-immobiliere/tests/test_runtime_v0.py
```

## Skills agents

Les skills actifs du projet sont dans `skills/`. Le registre Aston-like est
genere dans `skills/SKILLS-REGISTRY.json` et la matrice agent/skills dans
`integration/AGENT-SKILLS-MATRIX.md`.

Les D-REEL ne sont plus une source active versionnee dans le projet. Les
patterns metier issus des D-REEL sont integres dans les skills, avec la
provenance documentee dans `skills/SKILLS-PROVENANCE.md`. Les regressions CI
s'appuient sur des fixtures synthetiques; tout dossier D-REEL ou client reste
hors repo dans un repertoire ignore.

Les skills de redaction ont un contrat de couverture dans
`skills/REDACTION-SKILLS-CONTRACT.json`; le gate
`outils/verifier_contrat_redaction_skills_v0.py` verifie que les ancrages
metier essentiels restent presents dans les instructions actives.

Les skills critiques par agent ont aussi un contrat dans
`skills/AGENT-SKILLS-CONTRACTS.json`; le gate
`outils/verifier_contrats_skills_agents_v0.py` couvre les ancrages
data-facts, comps-market, valuation-draft et compliance-qa.

Le runtime produit une preuve de propagation des skills dans
`tests/runtime/skills_runtime_evidence.json` et
`tests/runtime/SKILLS-RUNTIME-EVIDENCE-V0.md`. Le gate
`outils/verifier_preuve_runtime_skills_v0.py` compare les audit logs, les
artefacts et `skills_by_agent` aux `AgentConfig`.

Les artefacts metier produits par agent sont couverts par
`integration/AGENT-ARTIFACT-CONTRACTS-V0.json`; le gate
`outils/verifier_contrats_artefacts_agents_v0.py` verifie les sorties runtime
executees et genere `tests/runtime/agent_artifact_contracts_evidence.json`.

L'homologation metier synthetique est cadree par
`atelier/HOMOLOGATION-METIER-GRILLE-V1.json`; le gate
`outils/verifier_homologation_metier_v0.py` produit
`tests/runtime/homologation_metier_report.json` et maintient
`atelier/PV-HOMOLOGATION-V1.md`. La decision production demeure bloquee tant
que les revues terrain d'evaluateurs ne sont pas fournies hors repo.

Chaque `AGENTCONFIG-*` declare ses `skills_allowed`; le runtime les propage dans
les evenements et artefacts pour garder la trace du contexte specialise charge
par agent.

## Cockpit produit et API runtime v0

L'API locale expose un cockpit produit, le runtime, les operations et les artefacts:

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py
```

Interfaces locales:

```text
http://127.0.0.1:8787/product
http://127.0.0.1:8787/ui
http://127.0.0.1:8787/ops/ui
http://127.0.0.1:8787/review/ui
```

Endpoints:

- `GET /product/summary`
- `POST /product/demo`
- `GET /auth/status`
- `GET /ops/snapshot`
- `GET /ui`
- `GET /fixtures`
- `POST /session`
- `POST /start`
- `GET /session/summary?session_id=<id>`
- `GET /review/dossier?session_id=<id>`
- `GET|POST /review/package?session_id=<id>`
- `GET /knowledge/immobilier?session_id=<id>`
- `GET /assistant/workbench?session_id=<id>`
- `POST /assistant/message`
- `GET /stream?session_id=<id>`
- `GET /artifact?session_id=<id>&event_id=<event_id>`
- `GET /health`

`GET /knowledge/immobilier` expose le snapshot metier structure de la session:
mandat, bien sujet, sources, preuves marche, valeurs, reconciliation,
conformite, redaction, revue humaine et audit.
`GET /assistant/workbench` expose le plan multi-agents Aston de la session:
etat des agents, artefacts produits/manquants, transcript et prochaines actions.
`POST /assistant/message` permet de questionner le dossier actif depuis le
cockpit produit. Les reponses sont sourcees par les artefacts runtime et incluent
des limites explicites: aucune certification automatique et aucune reponse
d'evaluateur agree inventee.

Demo depuis un autre terminal:

```bash
python evaluation-immobiliere/outils/demo_api_v0.py --fixture case_nominal.json
```

## Prochaine etape logique

Continuer la finalisation produit backend/frontend: lecture detaillee des
artefacts, workflow de revue dossier, reprise session, securite minimale,
observabilite et gates CI. La revue par un evaluateur immobilier reste une
etape finale de validation, pas le centre de la construction produit.
