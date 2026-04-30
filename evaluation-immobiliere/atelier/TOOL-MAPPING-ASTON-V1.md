# TOOL MAPPING ASTON V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Versionner le mapping Phase C entre les `tools_allowed` des `AGENTCONFIG-*` immobiliers et les capacités réellement disponibles dans le runtime local. Ce document sert de contrat de branchement avant passage à une boucle Aston native.

## Synthèse exécution
| Outil | Agents consommateurs | Implémentation repo actuelle | Statut Phase C | Écart Aston réel |
|---|---|---|---|---|
| `read_file` | data-facts, comps-market, valuation-draft, compliance-qa, redaction | Lecture fixtures JSON et artefacts runtime via `Path.read_text` dans `RuntimeEngine` et scripts `outils/` | Branché v0 local | Remplacer par lecture workspace/session Aston avec contrôle d'accès |
| `list_files` | data-facts | Découverte `case_pilote_reel_*.json` par `discover_real_pilot_cases()` | Branché v0 local | Lister pièces d'une session Aston et métadonnées documentaires |
| `extract_text` | data-facts | Contexte `runtime_pilotes_reels/ingestion_v0` et `source_text` conservé hors git | Partiel | Brancher OCR/document parser réel avec preuve page/source |
| `write_file` | tous | `write_artifact_payload()` écrit JSON/Markdown par étape | Branché v0 local | Écriture dans artifact store Aston avec version, checksum, ACL |
| `append_audit_log` | tous | `engine.audit.append_audit_log()` écrit JSONL append-only par cas | Branché v0 local | Journal central immuable et corrélé session/run/user |
| `search_comparables` | comps-market | `engine.tools.search_comparables()` filtre et score le pool fourni par fixture | Partiel | Connecteur comparables réel, provenance fournisseur, coûts et retries |
| `run_calculation` | valuation-draft | `engine.tools.run_calculation()` + `engine.valuation.calculate_valuation_trace()` | Branché v0 local | Tables métier calibrées et moteur de calcul homologué |
| `validate_schema` | compliance-qa | `engine.tools.validate_schema()` + `validate_contract_rules()` | Branché v0 local | Validation schema/contrat intégrée au runtime Aston |
| `format_document` | redaction | `render_markdown_payload()` produit les brouillons Markdown | Partiel | Génération rapport final template client avec revue et export |

## Mapping par agent
| AgentConfig | Outils requis | Couverture actuelle | Point bloquant |
|---|---|---|---|
| `AGENTCONFIG-DATA-FACTS-V0.yaml` | `read_file`, `list_files`, `extract_text`, `write_file`, `append_audit_log` | Lecture/écriture/audit prêts; extraction texte partielle via artefacts d'ingestion existants | OCR et chaînage document réel non branchés nativement |
| `AGENTCONFIG-COMPS-MARKET-V0.yaml` | `search_comparables`, `read_file`, `write_file`, `append_audit_log` | Scoring déterministe sur pool fourni; audit prêt | Source de marché réelle non connectée |
| `AGENTCONFIG-VALUATION-DRAFT-V0.yaml` | `read_file`, `run_calculation`, `write_file`, `append_audit_log` | Calculs comparatif/coût/revenu tracés | Calibrage métier et tables coût/revenu à homologuer |
| `AGENTCONFIG-COMPLIANCE-QA-V0.yaml` | `read_file`, `validate_schema`, `write_file`, `append_audit_log` | Contrats et schema checks exécutables | Harmoniser erreurs runtime et décisions humaines finales |
| `AGENTCONFIG-REDACTION-V0.yaml` | `read_file`, `write_file`, `format_document`, `append_audit_log` | Brouillons Markdown générés si compliance non bloquante | Template rapport final client et export restent à brancher |

## Contrats minimaux des outils
| Outil | Entrées minimales | Sorties minimales | Erreurs Phase C |
|---|---|---|---|
| `read_file` | `path`, `session_id`, `run_id` | contenu + métadonnées source | `E-SOURCE-MISSING`, `E-PERSISTENCE-FAILED` |
| `list_files` | `dossier_id`, `session_id` | liste chemins + types + checksums | `E-SOURCE-MISSING` |
| `extract_text` | document source + type MIME | texte, pages, flags d'anonymisation, trace champs | `E-SOURCE-MISSING`, `E-CALCULATION-FAILED` |
| `write_file` | artefact, payload, step, checksum | chemin artefact + checksum + event `artifact_written` | `E-PERSISTENCE-FAILED` |
| `append_audit_log` | event runtime, timestamp, session/run | ligne JSONL ou event central | `E-EVENT-STREAM-GAP`, `E-PERSISTENCE-FAILED` |
| `search_comparables` | fiche bien, zone, date, sources marché | comparables scorés + justifications | `E-SOURCE-MISSING`, `E-UNIT-INCOHERENCE` |
| `run_calculation` | comparables, ajustements, méthode | valeurs par approche + trace calcul | `E-CALCULATION-FAILED`, `E-UNIT-INCOHERENCE` |
| `validate_schema` | artefact, schema/contrat | pass/fail + violations | `E-COMPLIANCE-BLOCKING` |
| `format_document` | artefacts validés, template | brouillon rapport + annexe sources | `E-REDACTION-INCOMPLETE` |

## Décisions prises
- La Phase C démarre sur le runtime local déterministe existant, en gardant le vocabulaire Aston (`session`, `run`, `artifact`, `event`) pour préparer le remplacement par la boucle native.
- Les connecteurs externes non branchés sont explicitement classés "Partiel" afin d'éviter un faux Go.
- Le dossier `runtime_pilotes_reels/` reste une preuve locale ignorée par git; les synthèses versionnées vivent dans `atelier/`.

## Questions ouvertes
- Quel service Aston doit porter l'artifact store central: workspace fichiers, stockage objet, base runtime dédiée, ou combinaison ?
- Quel fournisseur de comparables réel est retenu pour remplacer le pool fixture ?
- Quel outil OCR/document parser est homologué pour les dossiers client anonymisés ?
