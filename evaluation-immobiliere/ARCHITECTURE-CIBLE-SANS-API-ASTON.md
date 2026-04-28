# Architecture cible — adaptation directe d'Aston (sans dépendre de son API)

## Décision
On fait une **adaptation directe d'Aston** (base principale), pas une simple inspiration.
Le principe: reprendre l'infrastructure Aston quasi telle quelle, puis appliquer des changements ciblés pour le métier d'évaluation immobilière.

## Positionnement technique
- **Base de départ**: architecture Aston existante (engine, patterns d'agents, handoff, contrôles).
- **Objectif**: fork/adaptation métier immobilière.
- **Contrainte**: ne pas dépendre de l'API du projet Aston partenaire.

## Ce qu'on garde d'Aston (quasi intact)
1. Boucle agent unifiée (orchestration, retries, budgets, compaction).
2. Modèle de config agent (approche `AgentConfig` et quality gates).
3. Logique de handoff d'artefacts.
4. Streaming d'événements et observabilité.

## Ce qu'on adapte (changement minimal ciblé)
1. Prompts/outils/schémas orientés évaluation immobilière.
2. Règles conformité (NPP/OEAQ) et validation humaine évaluateur.
3. Artefacts de sortie (comparables, approches, brouillon rapport).
4. Connecteurs de données immobilières.

## Stratégie d'adaptation (minimiser les écarts)
- Étape 1: copier structure Aston (engine/api/tools) comme base interne.
- Étape 2: brancher les `AGENTCONFIG-*` immobiliers.
- Étape 3: remplacer seulement les modules métier (tools + prompts + règles).
- Étape 4: exécuter dry-run + dossiers pilotes pour mesurer l'écart vs cible.

## Définition de done
Adaptation réussie quand:
- le runtime garde la structure Aston,
- les agents juridiques sont remplacés par les agents immobiliers,
- les sorties respectent la conformité immobilière,
- et le flux complet fonctionne sans dépendre de l'API Aston partenaire.
