# Quand on passe à la vraie boucle Aston: est-ce adapté à l'immobilier?

## Réponse courte
Oui.
La boucle Aston (engine `agent_loop`) reste la même, mais le **métier** change via la configuration:
- prompts système,
- outils disponibles,
- règles de conformité,
- artefacts produits,
- garde-fous de validation humaine.

## Comment l'adaptation se fait techniquement

### 1) Ce qui ne change pas
- La mécanique de la boucle (itérations, appels outils, recovery, compaction, streaming).
- La structure d'exécution multi-agent.

### 2) Ce qui change pour passer de "avocat" à "évaluation immobilière"
- Les `AgentConfig` (agents immobiliers au lieu juridiques).
- Les tools branchés (sources immobilières au lieu jurisprudentielles).
- Les schémas d'output (fiche bien, comparables, ajustements, brouillon rapport).
- Les règles QA (NPP/OEAQ et validation évaluateur).

## Image mentale simple
- **Engine Aston** = le moteur de voiture.
- **Configs/Outils/Prompts** = la carrosserie + usage métier.

On garde le moteur, on change l'équipement pour en faire un véhicule d'évaluation immobilière.

## Critère de validation
On peut confirmer "oui c'est adapté" si, dans la vraie boucle:
1. les agents immobiliers tournent sans agents juridiques,
2. les outils retournent des données immobilières,
3. les sorties respectent les contrôles conformité immobiliers,
4. l'évaluateur peut valider/réviser la sortie finale.
