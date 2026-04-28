# "Connecter au vrai engine Aston" — ce que ça veut dire concrètement

## En bref
Aujourd'hui, nos scripts (`dry_run_pipeline_v0.py`, etc.) sont un simulateur local.
"Connecter au vrai engine Aston" veut dire brancher ce pipeline à la boucle d'exécution réelle d'Aston (`agent_loop`) et à ses services (outils, stockage, streaming, persistance).

## Différence entre maintenant et après intégration

### Maintenant (simulateur)
- Les agents sont décrits sur papier (YAML/MD).
- Les règles sont appliquées par des scripts locaux.
- Les données viennent de fixtures JSON.
- Pas de session utilisateur live, pas de streaming front.

### Après intégration Aston (réel)
- Chaque agent devient un `AgentConfig` Aston exécutable.
- Les tool-calls passent par les outils d'Aston (lecture fichiers, recherche, écriture artefacts).
- Les sessions tournent dans l'`agent_loop` avec budgets/tokens/recovery.
- Les résultats sont persistés et streamés (SSE/API) vers l'interface.

## Les 4 branches de travail pour y arriver

1. **Brancher les configs agents**
   - créer les configs `facts/data`, `comps`, `valuation_draft`, `compliance_qa`, `redaction` dans la structure Aston.

2. **Brancher les outils réels**
   - remplacer les mocks/fixtures par vrais connecteurs de données (documents, comparables, registres).

3. **Brancher la persistance et artefacts**
   - sauver les outputs dans le case directory/knowledge base Aston.

4. **Brancher l'API + streaming**
   - exposer endpoints de session/start/stream pour l'agent d'évaluation immobilière.

## Définition de terminé (Done)
On pourra dire "connecté au vrai engine Aston" quand:
- un dossier réel passe de l'entrée à la sortie via `agent_loop`,
- les artefacts sont écrits/persistés,
- la progression est visible en streaming,
- l'évaluateur peut réviser dans l'interface.
