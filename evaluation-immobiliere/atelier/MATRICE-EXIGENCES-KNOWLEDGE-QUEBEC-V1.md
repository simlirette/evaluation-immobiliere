# MATRICE EXIGENCES KNOWLEDGE QUEBEC V1

_As-of date: 2026-05-01 (America/Toronto)_

## Objectif

Transformer les sources knowledge Quebec/CUSPAP/OEAQ disponibles en exigences produit testables pour `evaluation-immobiliere`, sans declarer de conformite professionnelle tant qu'un evaluateur agree n'a pas valide les gates.

## Sources exploitees

| Source | Fichier local | Conversion | Portee utilisee |
|---|---|---|---|
| CUSPAP 2026 | `C:\Users\simon\knowledge\2026-CUSPAP.pdf` | `converted-docling/2026-cuspap.md` via pypdf complet; Docling partiel conserve | reporting, work-file, confidentialite, conflits, scope of work, inspection, sources, IA, certification |
| Code de deontologie OEAQ | `C:\Users\simon\knowledge\C-26, R. 123.pdf` | Docling markdown/json | devoirs client/public/profession, independance, conflits, confidentialite, dossier client |
| F-2.1, r. 10 | `C:\Users\simon\knowledge\F-2.1, R. 10.pdf` | Docling markdown/json | proportion mediane, ventes, calculs, role municipal |
| F-2.1, r. 13 | `C:\Users\simon\knowledge\F-2.1, R. 13.pdf` | Docling markdown/json | role d'evaluation, fichier mutations, dossier propriete, methodes, conciliation |

## Lecture de maturite

Statut global: **PARTIEL_A_DURCIR**.

Le runtime v0 couvre deja la traceabilite technique, les sources, les comparables, certains blocages de date/fiabilite et l'audit. Les exigences knowledge ajoutent surtout des metadonnees de mandat, de scope, de consentement, de confidentialite, d'independance et de certification humaine qui ne doivent pas rester implicites.

## Gates prioritaires

| ID | Priorite | Source | Exigence source | Couverture actuelle | Gate produit recommande | Evidence attendue |
|---|---|---|---|---|---|---|
| KQG-001 | P0 | CUSPAP 6.2, 7.2, 7.3, 7.4, 7.7, 7.8 | Un rapport identifie client autorise, utilisateurs autorises, usage autorise, objet, definition de valeur, date effective et date du rapport. | `mandate.date_reference` existe; client/utilisateur/usage/definition de valeur non explicites. | Bloquer `PRET_REVISION_FINALE` si le mandat normalise ne contient pas `authorized_client`, `authorized_users`, `authorized_use`, `purpose`, `value_definition`, `effective_date`, `report_date`. | `dossier_normalise.mandate`, rapport final, audit `mandate_validated`. |
| KQG-002 | P0 | CUSPAP 5.8 | Le work-file existe avant/contemporain au rapport, contient rapports/drafts, certification, donnees et documentation de support, et doit rester recuperable. | Source index, audit JSONL et artefacts existent; pas de manifeste work-file complet ni retention liee au dossier. | Creer un `work_file_manifest.json` par dossier et bloquer la signature si un artefact requis ou une preuve de source manque. | Manifest work-file, hashes, chemins artefacts, politique retention. |
| KQG-003 | P0 | CUSPAP 7.5 | Le scope of work doit decrire inspection, recherche, analyse, limites; l'inspection est obligatoire sauf condition limitative extraordinaire. | `source_documents`, `quality`, `traceability` existent; statut d'inspection et limites non modelises. | Ajouter `scope_of_work.inspection_status`, `inspection_type`, `inspection_limitations`, `extraordinary_limiting_conditions`, `data_sources_reliability`. | Section scope du rapport, audit `scope_validated`, flags revue humaine. |
| KQG-004 | P0 | CUSPAP 7.5.1.viii | Ne pas se fier uniquement a une sortie IA; confirmer la credibilite de toute sortie IA utilisee. | Le runtime est IA/agent-ready mais la validation humaine de sorties IA n'est pas encodee comme exigence CUSPAP. | Gate `ai_output_validated_by_human` avant toute conclusion finale; interdire la certification automatique. | Decision evaluateur, trace des corrections, audit `ai_output_human_validated`. |
| KQG-005 | P0 | CUSPAP 7.9, 7.10 | Les hypotheses, conditions limitatives, hypotheses extraordinaires et conditions hypothetiques doivent etre identifiees. | `hypotheses` existe dans le dossier normalise; classification et exposition rapport incompletes. | Bloquer si une hypothese n'a pas `type`, `impact`, `source`, `review_status`; afficher toute condition extraordinaire dans le rapport. | `hypotheses[]`, rapport, file revue humaine. |
| KQG-006 | P0 | CUSPAP 6.2, 7.11, 7.12 | La certification signee engage la responsabilite du membre; signature numerique sous controle du membre. | Revue humaine preparee; pas de certification professionnelle exploitable. | Statut production impossible sans `certification_status=SIGNED_BY_EVALUATOR`; enregistrer identite, role, date, version artefacts. | Audit `certification_signed`, hash rapport, reviewer identity. |
| KQG-007 | P0 | OEAQ C-26 r.123, art. 17-19.1; CUSPAP 5.10 | Sauvegarder l'independance, eviter conflits, divulguer par ecrit et obtenir autorisation si conflit/apparence. | RBAC/audit existent; intake conflit absent. | Ajouter questionnaire conflit/independance au mandat; bloquer si conflit non resolu ou non autorise. | `conflict_check.json`, consentement client, mention au rapport si applicable. |
| KQG-008 | P0 | OEAQ art. 51; CUSPAP 5.9 | Confidentialite: usage limite aux fins confiees, non-divulgation hors autorisation ou obligation legale. | Anonymisation et RBAC existent; release/recipient list non liee a l'usage autorise. | Gate de diffusion: chaque export doit declarer destinataire, base d'autorisation et usage; bloquer destinataire non autorise. | Audit access/release, `authorized_users`, log export. |
| KQG-009 | P1 | OEAQ art. 39-42.1 | Informer le client de l'ampleur/modalites, obtenir consentement, informer sur fait nouveau, expliquer les services, informer recours a un tiers. | Mandat technique existe; consentement client et recours aux tiers non structures. | Ajouter `client_consent_status`, `scope_change_events`, `third_party_assistance_disclosure`. | Consentement, audit changement scope, disclosure tiers/OCR/data providers. |
| KQG-010 | P1 | CUSPAP 7.5; F-2.1 r.13 art. 3-9 | Donnees municipales/role: fichier mutations, dossier propriete, unites de voisinage, methodes, conciliation. | `role_evaluation_municipale` est source reference; pas de distinction forte entre role statutory et evaluation marche. | Etiqueter toute donnee de role municipal comme `statutory_assessment_reference`, jamais comme conclusion de valeur marchande sans analyse. | Source taxonomy, rapport comparables, justification. |
| KQG-011 | P1 | F-2.1 r.10 art. 2-6, 11-17 | Ventes: definition reglementaire, date de signature du contrat, exclusions/rajustements, epuration statistique pour proportion mediane. | `date_vente` et fenetre 1095 jours existent; pas de module proportion mediane. | Si module municipal active, separer ventes de marche privees et ventes admissibles proportion mediane; journaliser exclusions/rajustements. | `municipal_sales_basis.json`, calculs, exceptions. |
| KQG-012 | P1 | OEAQ art. 40-41; CUSPAP 7.5 | Avis/conseils complets: connaissance suffisante des faits, methodologie et etendue des recherches dans le rapport. | Rapport runtime brouillon existe; couverture methodologique partielle. | Ajouter section obligatoire `methodology_and_research_extent` dans brouillon rapport. | Rapport, checklist evaluateur. |

## Champs a ajouter au dossier normalise v1

| Bloc | Champs |
|---|---|
| `mandate` | `authorized_client`, `authorized_users`, `authorized_use`, `purpose`, `value_definition`, `effective_date`, `effective_date_type`, `report_date`, `report_format` |
| `scope_of_work` | `inspection_status`, `inspection_type`, `inspection_date`, `inspection_limitations`, `extraordinary_limiting_conditions`, `data_sources_reliability`, `ai_use_disclosure` |
| `work_file` | `manifest_path`, `required_artifacts`, `draft_reports`, `certification_artifact`, `retention_rule`, `retrieval_owner` |
| `professional_review` | `reviewer_id`, `reviewer_role`, `conflict_check_status`, `ai_output_validation_status`, `certification_status`, `signed_at` |
| `confidentiality` | `authorized_recipients`, `release_basis`, `export_log_required`, `client_access_request_status` |
| `municipal_context` | `role_source_status`, `mutation_file_reference`, `neighborhood_unit_reference`, `median_proportion_applicable`, `statutory_vs_market_label` |

## Backlog executable

| ID | Phase cible | Priorite | Action |
|---|---|---|---|
| KQ-P0-01 | B/D | P0 | Versionner `DOSSIER-NORMALISE-V1.yaml` avec les blocs `mandate`, `scope_of_work`, `work_file`, `professional_review`, `confidentiality`. |
| KQ-P0-02 | C/D | P0 | Ajouter validation runtime des metadonnees de mandat et des hypotheses classees. |
| KQ-P0-03 | E/H | P0 | Ajouter formulaire UI evaluateur pour conflit/independance, validation IA et certification. |
| KQ-P0-04 | F/J | P0 | Ajouter gate de diffusion/confidentialite lie aux utilisateurs autorises. |
| KQ-P0-05 | H/J | P0 | Faire signer par un evaluateur agree la matrice des gates avant tout GO production. |
| KQ-P1-01 | C/H | P1 | Ajouter section rapport `methodology_and_research_extent` et source rationale. |
| KQ-P1-02 | G/H | P1 | Ajouter controles de qualite des donnees tierces et justification de fiabilite. |
| KQ-P1-03 | H/K | P1 | Creer module municipal optionnel pour distinguer role, proportion mediane et evaluation marche. |

## Decision Go/No-Go knowledge

- **GO preparation**: utiliser cette matrice pour enrichir les contrats v1 et la revue evaluateur.
- **NO_GO conformite professionnelle**: ne pas annoncer une conformite CUSPAP/OEAQ tant que les gates P0 ne sont pas implementes, testes et signes par un evaluateur agree.
- **NO_GO production**: tout rapport final doit rester `BROUILLON` ou `A_REVOIR` tant que la certification humaine et les autorisations de diffusion ne sont pas en place.

## Questions terrain a poser aux evaluateurs

1. Quels champs de mandat sont absolument requis avant de commencer un dossier reel?
2. Dans quels cas accepter une absence d'inspection, et quelle formulation de condition limitative extraordinaire employer?
3. Quelle preuve minimale veut-on dans le work-file pour les comparables, ajustements, hypotheses et conciliation?
4. Comment formaliser la validation humaine d'une sortie IA sans faire croire a une certification automatique?
5. Quelles donnees du role municipal sont acceptables comme reference, et lesquelles ne doivent jamais alimenter directement une conclusion de valeur marche?
