eval-immo

L'objectif global et la vision de ce projet est de batir une plateforme AI qui assiste rigoureusement le travail quotidien de l'évaluateur immobilier agréé. Dans un monde idéal, eval-immo "est" un É.A., il fait tout le travail d'un dossier de A à Z et l'É.A. fait seulement vérifier et approuver. Les connections aux sources de données officielles utilisées par les É.A. doivent être faites pour que les informations soient toujours officielles et à jour. Les agents et les skills doivent être batit par les connaissances théoriques sources de l'É.A.
Avec une infrastructure agentic, toutes les taches de l'évaluateur sont complétées par des agents précis et leurs skills. Voici comment je vois les étapes de déroulement de l'utilisation de la part de l'É.A. Le document workflow-evaluateur-agree.md est une source primordiale pour le projet, il décrit par étape comment l'É.A. procède à compléter un dossier de A à Z. Les étapes ci dessous sont un résumé dans mes mots, plus simple, mais aucun détail du workflow complet ne doit manquer. 

1. Dossier
1.1 "Récolte" de documents et d'informations. L'É.A. drag and drop les documents du nouveau dossier.
- Le mandat / contrat de service — c'est le document central. Il porte : le but de l'évaluation, le type de valeur recherché, la date de référence, l'usage prévu et les utilisateurs prévus, le type de bien, et l'identité du client (qui peut différer du mandant).
- L'adresse du bien.
- L'identification cadastrale (numéro de lot, parfois le matricule) — souvent, mais pas toujours fournie.

1.2 Avec ces trois documents, l'agent AI de cette première étape doit identifier le type de mandat, le type de propriété, le type de rapport OAEQ et les proposer au É.A. comme suggestion, l'É.A. doit confirmer ou choisir une autre option pour passer à la prochaine étape. 

*Ensuite, les agents exécutent les actions à prendre selon le workflow d'un É.A. Je m'explique: je veux que les agents fassent complètement le travail du É.A. avec le même résultat professionnel et la même méthodologie (workflow-evaluateur-agree.md). Des étapes clés de vérification par l'É.A. sont nécessaires. 

2. Marché
2.1 Inspection physique de la propriété. Photos, notes, croquis, voir phase 2 dans workflow-evaluateur-agree.md pour les types de docs de l'inspection. À cette étape, il doit aussi avoir un drag and drop pour les nouveaux documents à ajouter au dossier. 
2.2 Recherche de données par l'agent AI. Voir workflow-evaluateur-agree.md pour comprendre comment l'É.A. recherhe. 

3. Analyse du meilleur usage (AMU), fait par l'agent AI et vérifier et confirmer par l'É.A.

4. Analyse: application des approches d'évaluation, fait par l'agent AI et vérifier et confirmer par l'É.A.

5. Rapport: rédaction par l'agent AI. vérification, modification, confirmation, signature par l'É.A.

