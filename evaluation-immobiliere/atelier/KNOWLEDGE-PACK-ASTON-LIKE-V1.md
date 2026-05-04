# Knowledge Pack Aston-like V1

_As-of date: 2026-05-01 (America/Toronto)_

## Decision

Le runtime cible doit consommer un Knowledge Pack scelle, pas les documents
originaux de knowledge.

Le dossier `C:\Users\simon\knowledge` reste une zone d'ingestion locale. Il
n'est pas une dependance runtime. Le pack canonique courant est:

`C:\Users\simon\knowledge\packs\quebec-real-estate-knowledge-pack-v1`

## Contenu du pack

| Artefact | Role |
|---|---|
| `pack.json` | identite, version, couverture et fingerprint du pack |
| `runtime/source-catalog.json` | catalogue runtime sans chemins originaux |
| `runtime/gates-seed-v1.json` | gates produit initiaux |
| `runtime/knowledge-contract-v1.json` | contrat minimal pour agents/runtime |
| `runtime/deployment-policy.md` | politique d'utilisation Aston-like |
| `runtime/requirements-matrix-v1.md` | matrice V1 normalisee pour le pack |
| `evidence/markdown` | preuves extraites, consultables par les agents |
| `evidence/docling-json` | sorties structurees Docling disponibles |
| `sources/coverage.json` | couverture d'indexation |
| `sources/source-catalog-full.json` | catalogue complet des sources et extractions |

## Ce qui est exclu du runtime

- PDFs originaux.
- Pages HTML originales telechargees.
- Modeles Excel/XLT originaux.
- Notes non revisees.
- Rapports internes non anonymises.

Le pack V1 a ete valide sans fichiers `pdf`, `html`, `htm`, `xlt`, `xls` ou
`xlsx`, et les preuves runtime ont ete assainies pour ne plus exposer les
chemins locaux `C:\Users\simon\knowledge`.

## Difference avec Aston legal

Aston legal peut se concentrer sur corpus juridique, doctrine, jurisprudence et
raisonnement de dossier.

L'infrastructure evaluateur immobilier doit ajouter des controles propres au
metier:

- inspection et limites d'inspection;
- scope of work;
- work-file;
- distinction role municipal vs valeur marchande;
- validation humaine des sorties IA;
- conflit/independance;
- confidentialite et diffusion;
- certification/signature evaluateur.

## Regle de promotion

Un pack peut devenir runtime-ready seulement si:

1. chaque source a un `source_id` et un SHA256;
2. les sources indexees ont une preuve Markdown;
3. les sources metadata-only sont explicitement listees;
4. chaque gate pointe vers une source ou une section source;
5. le fingerprint du pack est inscrit dans le manifest runtime;
6. les gates P0 sont signes ou approuves par un evaluateur avant tout GO
   production.

## Statut V1

Fingerprint:

`3f948ce65b54e5ff6eb988e0f228fa75599a6b58909b3ed006d2f1d99d9d1e5f`

Couverture:

- 68 sources cataloguees.
- 62 preuves Markdown.
- 38 sorties Docling JSON.
- 6 fichiers metadata-only.
- 0 document original inclus dans le pack.

## Prochaine phase

Produire `MATRICE-EXIGENCES-KNOWLEDGE-QUEBEC-V2.md` depuis ce pack, pas depuis
les PDFs originaux.
