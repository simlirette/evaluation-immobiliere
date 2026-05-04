# Skills Provenance

_As-of date: 2026-05-04_

## Source active

La source active de connaissance metier pour les agents est le repertoire
`evaluation-immobiliere/skills/`.

Les artefacts de controle actifs sont:

- `skills/SKILLS-REGISTRY.json`
- `skills/REDACTION-SKILLS-CONTRACT.json`
- `skills/AGENT-SKILLS-CONTRACTS.json`
- `integration/AGENT-ARTIFACT-CONTRACTS-V0.json`
- `integration/AGENT-SKILLS-MATRIX.md`
- `integration/AGENTCONFIG-*-V0.yaml`
- `outils/verifier_readiness_skills_v0.py`
- `outils/verifier_contrat_redaction_skills_v0.py`
- `outils/verifier_contrats_skills_agents_v0.py`
- `outils/verifier_contrats_artefacts_agents_v0.py`
- `outils/verifier_preuve_runtime_skills_v0.py`
- `tests/runtime/skills_runtime_evidence.json`
- `tests/runtime/agent_artifact_contracts_evidence.json`

## Statut D-REEL

Les D-REEL ont servi de calibration et d'observation pour certains skills de
redaction et de raisonnement metier. Ils ne sont plus requis comme fixtures
versionnees ni comme source active dans le repo.

Regles de retention:

- Aucun PDF, texte extrait ou JSON D-REEL n'est versionne.
- Les dossiers D-REEL ou clients restent dans un repertoire local ignore par
  Git, par exemple `evaluation-immobiliere/tests/fixtures_external/`.
- Les tests CI utilisent des fixtures synthetiques et representatives.
- Les skills peuvent mentionner une provenance D-REEL dans leurs analyses, mais
  les comportements attendus doivent etre exprimes dans les instructions de
  skill et verifies par les gates.

## Mode de preuve

Le projet ne depend pas des D-REEL pour passer les checks de readiness. La
preuve courante combine:

- coherence registry/matrice/AgentConfig;
- contrat de couverture des skills de redaction;
- contrats de couverture des skills critiques par agent;
- contrats metier des artefacts produits par agent;
- propagation runtime de `skills_allowed`;
- preuve runtime par audit log, artefacts et `skills_by_agent`;
- fixtures synthetiques sous `tests/fixtures/`;
- artefacts runtime synthetiques sous `tests/runtime/`;
- revue humaine ulterieure sur dossiers externes non versionnes.
