# MATRICE ERREURS / RETRY V1

## Portée
Matrice exécutable des erreurs runtime Aston, politiques de retry, et impacts sur scoring/homologation.

| Code erreur | Étape runtime | Détection | Retry | Limite | Escalade | Impact scoring | Impact homologation |
|---|---|---|---|---|---|---|---|
| E-SOURCE-MISSING | data-facts / comps-market | source_index incomplet | Oui | 2 | Lead Runtime | -0.20 qualité sources | Bloquant |
| E-UNIT-INCOHERENCE | valuation-draft | incohérence unités | Non | 0 | Lead Métier | -0.25 cohérence méthodes | Bloquant |
| E-CALCULATION-FAILED | valuation-draft | calcul JSON invalide | Oui | 1 | Lead Runtime | -0.30 confiance globale | Bloquant |
| E-COMPLIANCE-BLOCKING | compliance-qa | statut_sortie=A_REVOIR | Non | 0 | QA/Compliance | -0.15 confiance globale | Bloquant |
| E-REDACTION-INCOMPLETE | redaction | brouillon_rapport absent | Oui | 1 | Ops | -0.10 confiance globale | Conditionnel |
| E-EVENT-STREAM-GAP | runtime events | trou event_id/timestamp | Oui | 1 | Lead Plateforme | -0.15 cohérence méthodes | Bloquant |
| E-PERSISTENCE-FAILED | persistance session | artefact non écrit | Oui | 2 | Lead Plateforme | -0.20 confiance globale | Bloquant |

## Politique de retry Aston runtime
1. Retry uniquement pour erreurs techniques transitoires (I/O, persistance, indisponibilité source).
2. Aucun retry automatique pour erreurs métier/compliance (incohérence unités, A_REVOIR).
3. Après limite dépassée, stop runtime et ouverture ticket d'incident avec run_id.
4. Toute reprise doit conserver la traçabilité event→artefact et checksum.

## Tests de compatibilité attendus
- `python evaluation-immobiliere/outils/valider_contrats_runtime_v0.py`
- `python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py`
- `python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py`

## Décisions prises
- Le retry est borné et interdit pour les erreurs de conformité/homologation.
- Une erreur bloquante force le stop runtime et la revue humaine.
- L'impact scoring est explicite pour éviter un Go implicite.

## Questions ouvertes
- Faut-il introduire un mode dégradé Aston (sans redaction) pour certains clients internes ?
- Le seuil d'escalade doit-il être par dossier ou global session ?
