# MATRICE EXIGENCES KNOWLEDGE QUEBEC V2

_As-of date: 2026-05-01 (America/Toronto)_

## Objet

Transformer le `Knowledge Pack` Quebec immobilier V1 en exigences produit
testables pour `evaluation-immobiliere`, en mode Aston-like:

- le runtime consomme un pack scelle;
- les documents originaux ne sont pas une dependance runtime;
- chaque gate renvoie a des `source_id`, sections ou articles;
- aucune conformite professionnelle n'est declaree sans validation humaine par
  un evaluateur agree.

Pack de reference:

`C:\Users\simon\knowledge\packs\quebec-real-estate-knowledge-pack-v1`

Fingerprint:

`3f948ce65b54e5ff6eb988e0f228fa75599a6b58909b3ed006d2f1d99d9d1e5f`

Couverture du pack: 68 sources cataloguees, 62 preuves Markdown, 38 sorties
Docling JSON, 6 sources metadata-only, 0 document original inclus.

## Changement V2 vs V1

La V1 etait une matrice de demarrage basee sur quelques sources. La V2 devient
la matrice de contrat runtime:

- remplacement des chemins PDF par des `source_id`;
- ajout de CUSPAP comme source structuree `00-*`;
- ajout explicite des normes de pratique OEAQ, MEFQ, discipline et sources
  municipales;
- reclassement de certains controles en P0, surtout consentement client,
  methodologie, et recours a des tiers essentiels;
- separation plus nette entre evaluation privee de valeur marchande et
  processus municipal/statutaire;
- definition d'un `DOSSIER-NORMALISE-V2` minimal.

## Sources runtime principales

| Bloc | Source runtime | References utilisees | Usage produit |
|---|---|---|---|
| CUSPAP/NUPPEC 2026 | `SRC-00-A637B1B575` | CUSPAP 5.8, 5.9, 5.10, 6.2, 7.3, 7.5, 7.9, 7.10, 7.12 | work-file, confidentialite, conflit, rapport, scope, inspection, IA/AVM, assistance professionnelle |
| OEAQ normes de pratique | `SRC-04-38B80BBC2F` | NPP regles coercitives/directives, Normes 1-4, 13-14, 19-22 | methodes, erreurs significatives, rapport comprehensible, examen/revue, municipal, assurance |
| OEAQ code de deontologie | `SRC-05-1CC7B06665` | arts. 17-19.1, 34, 39-42.1, 51, 920 | independance, conflits, signature, consentement, tiers, confidentialite, rapport faux/incomplet |
| Loi fiscalite municipale | `SRC-03-456F142EBE` | F-2.1 arts. 14-18, 19-22, 30-41, 36.1 | role municipal, acces, renseignements, statut de l'evaluateur municipal |
| Role evaluation fonciere | `SRC-03-65CABE4940` | F-2.1 r.13 arts. 3-9 | mutations, dossier propriete, unites de voisinage, methodes, conciliation |
| Proportion mediane | `SRC-03-75F40B7D4E` | F-2.1 r.10 arts. 2-6, 11-18, 25-28 | ventes admissibles, ajustements, exclusions, epuration statistique |
| Manuel MEFQ 2025 | `SRC-01-6784A9F599` et `SRC-01-*` | Manuel et parties MEFQ | support municipal et structure des dossiers |
| Discipline OEAQ | `SRC-09-*` | decisions discipline/sanction | signaux QA: rapport incomplet, insuffisance methodologique, explications insuffisantes |

## Lecture de maturite

Statut global: **GO_CONTRATS_RUNTIME, NO_GO_PRODUCTION**.

Le projet peut maintenant passer de la documentation a des contrats et gates
executables. Par contre, il ne doit pas produire ou laisser entendre une
conformite CUSPAP/OEAQ tant que les gates P0 ne sont pas implementes, testes et
signes par un evaluateur agree.

## Gates V2

| ID | Priorite | Domaine | Sources | Regle produit runtime | Evidence attendue |
|---|---|---|---|---|---|
| KQG-001 | P0 | Mandat et identite du rapport | `SRC-00-A637B1B575` CUSPAP 6.2, 7.3, 7.4; `SRC-04-38B80BBC2F` NPP Norme 1 elements 1-4 | Bloquer `PRET_REVISION_FINALE` si le dossier ne declare pas client autorise, utilisateurs autorises, usage autorise, objet, but, definition/source de valeur, date effective et date de rapport. | `dossier_normalise.mandate`, rapport brouillon, audit `mandate_validated`. |
| KQG-002 | P0 | Work-file | `SRC-00-A637B1B575` CUSPAP 5.8 | Un `work_file_manifest.json` doit exister avant signature, avec rapports/drafts, certification signee/datee, donnees de support, hashes, retention et responsable de recuperation. | Manifest work-file, hashes, artefacts, politique retention. |
| KQG-003 | P0 | Scope, inspection et donnees | `SRC-00-A637B1B575` CUSPAP 7.5; `SRC-04-38B80BBC2F` NPP Norme 1 element 5 | Bloquer si inspection, limites d'inspection, recherches, analyse appliquee, sources et fiabilite des donnees ne sont pas structurees. Toute absence d'inspection doit etre justifiee par condition limitative extraordinaire ou retrait du mandat si l'information requise est indisponible. | `scope_of_work`, `inspection`, `data_sources`, audit `scope_validated`. |
| KQG-004 | P0 | Validation IA/AVM | `SRC-00-A637B1B575` CUSPAP 7.5.1.viii | Interdire toute conclusion finale basee uniquement sur sortie IA/AVM. Exiger confirmation humaine de la credibilite et trace des corrections. | `ai_use[]`, validation evaluateur, audit `ai_output_human_validated`. |
| KQG-005 | P0 | Hypotheses, reserves et conditions | `SRC-00-A637B1B575` CUSPAP 7.9, 7.10; `SRC-04-38B80BBC2F` NPP directives/ecarts | Chaque hypothese, reserve, condition limitative extraordinaire ou condition hypothetique doit avoir type, impact, source, justification et statut de revue. Les ecarts aux directives doivent etre acceptes par le client et expliques au rapport. | `assumptions_conditions[]`, rapport, consentement/ecart. |
| KQG-006 | P0 | Certification et signature | `SRC-00-A637B1B575` CUSPAP 6.2, 7.12; `SRC-05-1CC7B06665` art. 34 | Aucun rapport final sans `certification_status=SIGNED_BY_EVALUATOR`, identite, role, date, version d'artefacts et hash du rapport. Aucune signature automatique. | Audit `certification_signed`, hash rapport, identite evaluateur. |
| KQG-007 | P0 | Independance et conflits | `SRC-05-1CC7B06665` arts. 17-19.1; `SRC-00-A637B1B575` CUSPAP 5.10 | Questionnaire conflit/independance obligatoire au mandat. Conflit non resolu bloque le mandat; conflit autorisable exige divulgation ecrite, autorisation client et mention au rapport si applicable. | `conflict_check.json`, consentements, rapport. |
| KQG-008 | P0 | Confidentialite et diffusion | `SRC-00-A637B1B575` CUSPAP 5.9; `SRC-05-1CC7B06665` art. 51 | Chaque export doit declarer destinataire, base d'autorisation et usage. Bloquer tout destinataire non autorise. Pour photos d'occupant/personnel, exiger consentement et conservation au work-file. | `release_log`, `authorized_recipients`, consentements photos. |
| KQG-009 | P0 | Consentement client et changements de scope | `SRC-05-1CC7B06665` arts. 39-42.1 | Le client doit etre informe de l'ampleur/modalites et consentir. Tout fait nouveau modifiant scope ou modalites doit declencher un evenement de changement et un nouveau consentement. | `client_consent_status`, `scope_change_events[]`, audit consentement. |
| KQG-010 | P0 | Tiers essentiels et assistance professionnelle | `SRC-05-1CC7B06665` art. 42.1; `SRC-00-A637B1B575` CUSPAP 7.12 | Recours a un tiers pour aspects essentiels ou assistance professionnelle doit etre declare avant usage, avec role, etendue, competence/verifications et impact sur le rapport. | `third_party_assistance[]`, disclosure client, traces verification. |
| KQG-011 | P0 | Methodologie, recherches et methodes | `SRC-05-1CC7B06665` arts. 40-41; `SRC-04-38B80BBC2F` NPP Norme 1 elements 10-12; `SRC-00-A637B1B575` CUSPAP 7.5 | Le rapport doit exposer methodologie et etendue des recherches. Plus d'une methode reconnue doit etre consideree lorsque pertinent; une seule methode exige justification. | `methodology`, `methods_considered[]`, `single_method_justification`. |
| KQG-012 | P0 | Reconciliation et conclusion | `SRC-04-38B80BBC2F` NPP Norme 1 reconciliation; `SRC-03-65CABE4940` F-2.1 r.13 art. 9 si municipal | Avant conclusion, refaire une revue du processus, droits evalues, date de reference, indications de valeur et raisonnement analytique menant a la valeur finale. | `reconciliation`, `final_value_rationale`, checklist evaluateur. |
| KQG-013 | P1 | Examen/revue professionnelle | `SRC-04-38B80BBC2F` NPP Normes 3-4 | Si un workflow de revue est active, l'examinateur doit juger completude, donnees, methodes, techniques, analyses et conclusions, et declarer la nature du processus d'examen. | `review_process`, `review_findings[]`, statut resolution. |
| KQG-014 | P1 | Role municipal vs valeur marche | `SRC-03-456F142EBE`; `SRC-03-65CABE4940`; `SRC-01-*` | Toute donnee de role municipal doit etre etiquetee `statutory_assessment_reference`; elle ne peut pas devenir une conclusion de valeur marchande sans analyse de marche independante. | Taxonomie source, citations municipal, justification de non-transfert. |
| KQG-015 | P1 | Dossier municipal | `SRC-03-65CABE4940` arts. 3-9; `SRC-01-*` MEFQ | Module municipal optionnel: mutations, dossier propriete, unites de voisinage, SIG, taux de variation, methodes et conciliation doivent etre separes du workflow prive. | `municipal_context`, `mutation_file`, `property_file`, `neighborhood_unit`. |
| KQG-016 | P1 | Proportion mediane et ventes admissibles | `SRC-03-75F40B7D4E` arts. 2-6, 11-18, 25-28 | Si module proportion mediane actif, separer ventes de marche privees et ventes admissibles reglementaires; journaliser rajustements, exclusions, epuration et rapports requis. | `municipal_sales_basis.json`, exclusions, calculs, rapport ministeriel si applicable. |
| KQG-017 | P1 | Signaux de risque disciplinaire | `SRC-09-*`; `SRC-05-1CC7B06665` art. 920 | Ajouter un controle QA qui detecte rapport incomplet, conclusion predeterminee, explications insuffisantes, absence d'informations essentielles, ou incoherence de methode. | `discipline_risk_flags[]`, revue humaine obligatoire si flag P1. |
| KQG-018 | P2 | Verticaux specialises | `SRC-04-*`; futures sources specialisees admises au pack | Assurance, fonds de prevoyance, expropriation et autres mandats specialises doivent etre des profils separes, pas des variantes implicites du rapport residentiel standard. | `assignment_profile`, schema specialise, gates dedies. |

## DOSSIER-NORMALISE-V2 minimal

| Bloc | Champs requis |
|---|---|
| `knowledge_pack` | `pack_name`, `pack_version`, `pack_fingerprint_sha256`, `source_ids_used[]` |
| `mandate` | `authorized_client`, `authorized_users[]`, `authorized_use`, `purpose`, `value_definition`, `value_definition_source`, `effective_date`, `report_date`, `report_format`, `assignment_profile` |
| `subject_property` | `address`, `cadastre`, `rights_appraised`, `property_interest`, `legal_restrictions`, `highest_and_best_use_required` |
| `scope_of_work` | `inspection_status`, `inspection_type`, `inspection_date`, `inspection_limitations[]`, `research_performed[]`, `analysis_applied[]`, `data_sources_reliability[]` |
| `data_sources` | `source_id`, `source_type`, `source_role`, `reliability_review`, `limitations`, `third_party_provided` |
| `ai_use` | `tool`, `task`, `output_hash`, `used_in_report`, `human_validation_status`, `validated_by`, `validated_at`, `corrections[]` |
| `assumptions_conditions` | `type`, `text`, `source`, `impact`, `client_disclosure_status`, `report_disclosure_status`, `review_status` |
| `methodology` | `methods_considered[]`, `methods_used[]`, `method_rejection_reasons[]`, `single_method_justification`, `research_extent`, `market_forces_review` |
| `reconciliation` | `indications[]`, `rights_reviewed`, `effective_date_reviewed`, `rationale`, `final_value`, `reviewer_status` |
| `work_file` | `manifest_path`, `required_artifacts[]`, `drafts[]`, `certification_artifact`, `retention_rule`, `retrieval_owner`, `artifact_hashes[]` |
| `third_party_assistance` | `name_or_provider`, `role`, `essential_aspect`, `client_informed_at`, `competence_review`, `extent_disclosed_in_report` |
| `professional_review` | `reviewer_id`, `reviewer_role`, `checklist_version`, `findings[]`, `resolved_findings[]`, `certification_status` |
| `confidentiality_release` | `authorized_recipients[]`, `release_basis`, `export_log_required`, `photos_consent_status`, `client_confidential_info_flags[]` |
| `municipal_context` | `is_municipal_assignment`, `role_reference_status`, `mutation_file_reference`, `property_file_reference`, `neighborhood_unit_reference`, `median_proportion_applicable`, `statutory_vs_market_label` |
| `discipline_risk` | `risk_flags[]`, `severity`, `review_required`, `resolution_notes` |

## Acceptance criteria implementation

1. Le runtime inscrit le fingerprint du pack dans chaque dossier et chaque
   rapport genere.
2. Aucun gate ne cite un chemin local `C:\Users\simon\knowledge`; les citations
   utilisent `source_id`, section/article et hash.
3. Les gates P0 bloquent les statuts `PRET_REVISION_FINALE`, `SIGNATURE`,
   `EXPORT` ou `PRODUCTION` selon le domaine.
4. Les sorties IA sont toujours marquees comme aide ou brouillon tant que
   `human_validation_status` n'est pas approuve.
5. Le rapport final exige signature/certification humaine et hash des artefacts.
6. Les donnees municipales sont etiquetees selon leur role: reference
   statutaire, intrant de marche, comparable verifie, ou calcul municipal.
7. Les tests incluent au moins un dossier valide, un dossier sans inspection,
   un dossier avec sortie IA non validee, un conflit non resolu, un export non
   autorise et un cas municipal.

## Backlog executable

| ID | Priorite | Phase cible | Action |
|---|---|---|---|
| KQ2-P0-01 | P0 | Contrats | Creer `DOSSIER-NORMALISE-V2.yaml` et `GATES-KNOWLEDGE-QUEBEC-V2.yaml` depuis cette matrice. |
| KQ2-P0-02 | P0 | Runtime | Ajouter `knowledge_pack.pack_fingerprint_sha256` a tous les manifests dossier/rapport. |
| KQ2-P0-03 | P0 | Runtime | Implementer les blocages KQG-001 a KQG-012. |
| KQ2-P0-04 | P0 | UI evaluateur | Ajouter formulaires mandat, inspection, conflit, consentement, assistance tierce, validation IA et certification. |
| KQ2-P0-05 | P0 | Artefacts | Generer `work_file_manifest.json` et hashes d'artefacts a chaque dossier. |
| KQ2-P0-06 | P0 | Tests | Ajouter fixtures de dossiers et tests de gates P0. |
| KQ2-P1-01 | P1 | Revue | Ajouter workflow d'examen/revue professionnelle et resolution de findings. |
| KQ2-P1-02 | P1 | Municipal | Isoler module municipal: role, mutation, voisinage, proportion mediane. |
| KQ2-P1-03 | P1 | QA | Ajouter signaux discipline et rapport de risques. |

## Decision Go/No-Go

- **GO prochaine phase**: contrats et gates runtime V2.
- **NO_GO rapport final**: tant que signature/certification humaine, work-file,
  confidentialite/export et validation IA ne sont pas implementes.
- **NO_GO conformite professionnelle**: tant qu'un evaluateur agree n'a pas
  approuve la matrice et les tests P0.

## Questions terrain restantes

1. Quel format exact de work-file veut-on imposer pour les mandats residentiels
   vs commerciaux?
2. Quels cas d'absence d'inspection sont acceptables dans la pratique de la
   firme et quelle formulation standard doit etre employee?
3. Qui peut agir comme reviewer interne et quel niveau de revue est requis
   avant signature?
4. Quels fournisseurs de donnees sont consideres fiables par defaut, et
   lesquels exigent validation renforcee?
5. Quels profils specialises doivent etre prioritaires apres le flux residentiel
   standard: commercial, assurance, contestation municipale, expropriation ou
   fonds de prevoyance?
