# Tool mapping Aston -> Évaluation immobilière (v0)

## But
Relier les besoins outils de l'agent `data-facts` aux capacités Aston existantes.

## Mapping initial

| Besoin métier | Outil Aston cible | Statut |
|---|---|---|
| Lire les documents d'un dossier | `read_file` | prêt |
| Lister les pièces disponibles | `list_files` | prêt |
| Extraire texte de PDF/scans | `extract_text` | à brancher selon infra OCR |
| Écrire les artefacts produits | `write_file` | prêt |
| Écrire la traçabilité (audit) | `append_audit_log` | à implémenter |

## Décisions de design
1. Aucun outil externe sans journalisation de source.
2. Toute écriture d'artefact doit inclure `source_index`.
3. Les erreurs d'extraction ne bloquent pas l'agent si elles sont explicitement journalisées.

## Critère prêt-intégration
- Le mapping est complet pour tous les `tools_allowed` du config agent.
- Chaque outil a un contrat input/output documenté.
- Les erreurs sont mappées à `blocking` ou `warning`.
