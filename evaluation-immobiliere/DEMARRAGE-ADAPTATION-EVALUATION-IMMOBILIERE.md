# Démarrage — adaptation de l'infrastructure Aston vers l'évaluation immobilière

## Contexte analysé

À partir de `INFRASTRUCTURE-AGENTS-2026-04-28.md`, l'infrastructure Aston est déjà un **orchestrateur multi-agents robuste** (boucle unifiée, outils, RAG, contrôle qualité, handoff via knowledge base). Elle est donc réutilisable comme fondation technique.

À partir de `IA pour l'évaluation immobilière au Québec.docx`, le domaine cible impose :

- un **cadre réglementaire strict** (OEAQ, NPP, traçabilité),
- une forte charge de **collecte/synthèse de données hétérogènes**,
- des étapes très automatisables en amont,
- et une étape de **réconciliation/jugement final** qui doit rester humaine.

## Objectif produit reformulé

Construire un copilote d'évaluation immobilière qui exécute le travail de bureau (collecte, structuration, comparables, calculs préparatoires, conformité documentaire, rédaction de brouillons), pendant que l'évaluateur :

1. valide les hypothèses,
2. arbitre les ajustements sensibles,
3. signe la conclusion professionnelle.

## Par où commencer (ordre recommandé)

### 1) Atelier de cadrage (immédiat, 2-3 h)

Objectif : verrouiller les frontières « automatisable vs jugement réservé ».

Livrables :

- liste des mandats cibles v1 (ex. résidentiel 1-4 logements),
- niveau de risque acceptable,
- liste des décisions obligatoirement humaines.

### 2) Période de questions structurée (avant tout dev)

Questions critiques à trancher :

- Quels types de rapports sont prioritaires en v1 (narratif, abrégé, formulaire)?
- Quelles sources de données sont accessibles légalement dès maintenant?
- Quel niveau d'explicabilité est exigé pour chaque chiffre généré?
- Quels contrôles qualité doivent être bloquants avant export du rapport?
- Quelle tolérance aux erreurs (faible, très faible, zéro sur certains champs)?

### 3) Plan fonctionnel en 3 couches

- **Couche A — Acquisition** : ingestion dossiers, registres, zonage, ventes, baux, photos.
- **Couche B — Analyse assistée** : sélection comparables, propositions d'ajustements, approche coût/revenu, cohérence mathématique.
- **Couche C — Conformité & rapport** : checklist NPP/OEAQ, traces de justification, génération de brouillon, piste d'audit.

### 4) Prototype vertical (2-4 semaines)

Faire **un seul cas d'usage de bout en bout** :

- mandat résidentiel standard,
- 1 type de rapport,
- données limitées mais fiables,
- revue finale par évaluateur.

Succès si : gain de temps mesurable + qualité perçue acceptable + traçabilité complète.

## Proposition d'adaptation des agents Aston

- **Agent Intake** (nouveau) : transforme la demande client en plan de collecte.
- **Agent Data/Facts** (adaptation de Facts) : lit les pièces, extrait attributs immobiliers, chronologie des faits, contraintes réglementaires.
- **Agent Comps & Market** (nouveau) : recherche et score des comparables avec justifications.
- **Agent Valuation Draft** (nouveau) : prépare calculs (approche comparative/coût/revenu) + hypothèses explicites.
- **Agent Compliance QA** (nouveau) : contrôle NPP/OEAQ, cohérence des unités, champs manquants, alertes risques.
- **Agent Redaction** (adaptation) : produit le brouillon de rapport prêt à révision.

## Garde-fous indispensables dès v1

- Journal complet des sources, hypothèses et transformations.
- Séparation explicite entre « proposition IA » et « décision évaluateur ».
- Blocage de sortie si checklist conformité incomplète.
- Versionnage des calculs et justification de chaque ajustement.

## Prochaine action concrète (recommandée)

Lancer un mini-workshop de 60-90 minutes avec 1-2 évaluateurs pour remplir une matrice :

- Tâche actuelle,
- Temps moyen,
- Douleur,
- Risque de conformité,
- Potentiel d'automatisation,
- Validation humaine requise.

Cette matrice deviendra le backlog priorisé du MVP.
