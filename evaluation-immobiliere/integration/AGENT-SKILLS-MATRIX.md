# Agent skills matrix

Registre des skills projet utilises par les agents du runtime Aston-like.

## Agents

### compliance-qa

- `analyse-conformite`
- `recherche-cadre-legal`
- `recherche-domaines-specialises`
- `recherche-jurisprudence-discipline`
- `recherche-mefq-methodologie`
- `recherche-normes-professionnelles`
- `redaction-rapport-conformite`

### comps-market

- `analyse-selection-comparables`
- `recherche-marche-donnees`
- `recherche-mefq-methodologie`
- `recherche-normes-professionnelles`
- `recherche-registre-cadastre`

### data-facts

- `analyse-extraction-faits`
- `recherche-baux-revenus`
- `recherche-cadre-legal`
- `recherche-domaines-specialises`
- `recherche-marche-donnees`
- `recherche-mefq-methodologie`
- `recherche-normes-professionnelles`
- `recherche-registre-cadastre`
- `recherche-urbanisme-construction`
- `redaction-fiches-techniques`

### redaction

- `recherche-normes-professionnelles`
- `redaction-analyse-marche`
- `redaction-rapport-evaluation`

### valuation-draft

- `analyse-approche-comparaison`
- `analyse-approche-cout`
- `analyse-approche-revenu`
- `analyse-reconciliation-valeur`
- `recherche-baux-revenus`
- `recherche-domaines-specialises`
- `recherche-mefq-methodologie`
- `recherche-normes-professionnelles`

## Skills

### analyse-approche-comparaison

- Type: `analyse`
- Agents: `valuation-draft`
- Sources: `01-mefq-manuel`, `00-cuspap`, `04-oeaq-normes`, `15-methodes-internationaux`
- Analysis encodee: oui
- Fichier: `skills/analyse-approche-comparaison/SKILL.md`

### analyse-approche-cout

- Type: `analyse`
- Agents: `valuation-draft`
- Sources: `01-mefq-manuel`, `_legacy-unstructured`, `00-cuspap`, `04-oeaq-normes`
- Analysis encodee: oui
- Fichier: `skills/analyse-approche-cout/SKILL.md`

### analyse-approche-revenu

- Type: `analyse`
- Agents: `valuation-draft`
- Sources: `01-mefq-manuel`, `23-baux-logement-revenu`, `00-cuspap`, `04-oeaq-normes`
- Analysis encodee: oui
- Fichier: `skills/analyse-approche-revenu/SKILL.md`

### analyse-conformite

- Type: `analyse`
- Agents: `compliance-qa`
- Sources: `00-cuspap`, `04-oeaq-normes`, `05-oeaq-reglements`, `09-jurisprudence-discipline`
- Analysis encodee: oui
- Fichier: `skills/analyse-conformite/SKILL.md`

### analyse-extraction-faits

- Type: `analyse`
- Agents: `data-facts`
- Sources: `01-mefq-manuel`, `02-mefq-complements`, `15-methodes-internationaux`
- Analysis encodee: oui
- Fichier: `skills/analyse-extraction-faits/SKILL.md`

### analyse-reconciliation-valeur

- Type: `analyse`
- Agents: `valuation-draft`
- Sources: `01-mefq-manuel`, `00-cuspap`, `04-oeaq-normes`
- Analysis encodee: oui
- Fichier: `skills/analyse-reconciliation-valeur/SKILL.md`

### analyse-selection-comparables

- Type: `analyse`
- Agents: `comps-market`
- Sources: `01-mefq-manuel`, `15-methodes-internationaux`, `00-cuspap`, `04-oeaq-normes`
- Analysis encodee: oui
- Fichier: `skills/analyse-selection-comparables/SKILL.md`

### recherche-baux-revenus

- Type: `recherche`
- Agents: `valuation-draft`, `data-facts`
- Sources: `23-baux-logement-revenu`
- Analysis encodee: oui
- Fichier: `skills/recherche-baux-revenus/SKILL.md`

### recherche-cadre-legal

- Type: `recherche`
- Agents: `compliance-qa`, `data-facts`
- Sources: `03-loi-fiscalite-municipale`, `05-oeaq-reglements`, `16-droit-immobilier`
- Analysis encodee: oui
- Fichier: `skills/recherche-cadre-legal/SKILL.md`

### recherche-domaines-specialises

- Type: `recherche`
- Agents: `data-facts`, `valuation-draft`, `compliance-qa`
- Sources: `13-sources-specialisees`, `19-expropriation-recours`, `20-copropriete-fonds-prevoyance`, `24-patrimoine-culturel-contraintes`, `25-financement-hypothecaire-risque`, `26-agricole-specialise`, `27-energie-performance-batiment`
- Analysis encodee: oui
- Fichier: `skills/recherche-domaines-specialises/SKILL.md`

### recherche-jurisprudence-discipline

- Type: `recherche`
- Agents: `compliance-qa`
- Sources: `09-jurisprudence-discipline`
- Analysis encodee: oui
- Fichier: `skills/recherche-jurisprudence-discipline/SKILL.md`

### recherche-marche-donnees

- Type: `recherche`
- Agents: `comps-market`, `data-facts`
- Sources: `_legacy-unstructured`, `15-methodes-internationaux`, `12-fournisseurs-donnees`
- Analysis encodee: oui
- Fichier: `skills/recherche-marche-donnees/SKILL.md`

### recherche-mefq-methodologie

- Type: `recherche`
- Agents: `data-facts`, `comps-market`, `valuation-draft`, `compliance-qa`
- Sources: `01-mefq-manuel`, `02-mefq-complements-et-outils`, `03-loi-fiscalite-municipale`
- Analysis encodee: oui
- Fichier: `skills/recherche-mefq-methodologie/SKILL.md`

### recherche-normes-professionnelles

- Type: `recherche`
- Agents: `compliance-qa`, `data-facts`, `valuation-draft`, `comps-market`, `redaction`
- Sources: `00-cuspap`, `04-oeaq-normes`, `06-aic`, `07-aic-practice`
- Analysis encodee: oui
- Fichier: `skills/recherche-normes-professionnelles/SKILL.md`

### recherche-registre-cadastre

- Type: `recherche`
- Agents: `data-facts`, `comps-market`
- Sources: `21-cadastre-donnees`, `22-droits-fonciers`
- Analysis encodee: oui
- Fichier: `skills/recherche-registre-cadastre/SKILL.md`

### recherche-urbanisme-construction

- Type: `recherche`
- Agents: `data-facts`
- Sources: `17-urbanisme-zonage`, `18-construction-inspection`
- Analysis encodee: oui
- Fichier: `skills/recherche-urbanisme-construction/SKILL.md`

### redaction-analyse-marche

- Type: `redaction`
- Agents: `redaction`
- Sources: `01-mefq-manuel`, `10-rapports-precedents-firme`, `12-fournisseurs-donnees`
- Analysis encodee: oui
- Fichier: `skills/redaction-analyse-marche/SKILL.md`

### redaction-fiches-techniques

- Type: `redaction`
- Agents: `data-facts`
- Sources: `01-mefq-manuel`, `02-mefq-complements`, `04-oeaq-normes`
- Analysis encodee: oui
- Fichier: `skills/redaction-fiches-techniques/SKILL.md`

### redaction-rapport-conformite

- Type: `redaction`
- Agents: `compliance-qa`
- Sources: `00-cuspap`, `04-oeaq-normes`, `09-jurisprudence-discipline`
- Analysis encodee: oui
- Fichier: `skills/redaction-rapport-conformite/SKILL.md`

### redaction-rapport-evaluation

- Type: `redaction`
- Agents: `redaction`
- Sources: `00-cuspap`, `04-oeaq-normes`, `10-rapports-precedents-firme`
- Analysis encodee: oui
- Fichier: `skills/redaction-rapport-evaluation/SKILL.md`
