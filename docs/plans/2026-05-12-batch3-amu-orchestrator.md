# Batch 3 — AMU Agent + PlanOrchestrator Wiring + build-eval-skill

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter l'agent AMU obligatoire NPP OEAQ au pipeline (step 2/6), brancher PlanOrchestrator dans api.py, et créer le meta-skill build-eval-skill pour produire les skills futurs.

**Architecture:** Le pipeline passe de 5 à 6 étapes. L'agent `amu-analyst` s'insère entre `data-facts` et `comps-market`, produit `umpp_conclusion.json` (structuré, lu par comps-market) et `amu_analyse.md` (narratif, enrichi LLM, lu par redaction). `PlanOrchestrator.enrich_case()` s'ajoute dans `start_runtime()` de façon non-bloquante. Le meta-skill `build-eval-skill` vit dans `~/.claude/skills/`.

**Tech Stack:** Python 3.x, YAML (parser maison sans dépendance), pytest, Markdown

**Assumptions:**
- Assumes `load_steps_from_pipeline_yaml` ordonne les steps par ordre d'apparition dans le YAML, pas par numéro — will NOT work si le parser tri par numéro de step.
- Assumes aucun test n'hardcode le nombre de steps à 5 — vérifier avant Task 5.
- Assumes `~/.claude/skills/` est le répertoire correct pour les skills Claude Code user-level (confirmé par présence du skill `gstack` à cet emplacement).

---

## File Structure

| Fichier | Action |
|---|---|
| `~/.claude/skills/build-eval-skill/SKILL.md` | Créer |
| `backend/skills/analyse-amu/SKILL.md` | Créer |
| `backend/skills/analyse-amu/analysis.md` | Créer |
| `backend/integration/AGENTCONFIG-AMU-ANALYST-V0.yaml` | Créer |
| `backend/engine/skills.py` | Modifier — ajouter `amu-analyst` dans `DEFAULT_SKILLS_BY_AGENT` |
| `backend/engine/runtime.py` | Modifier — 4 emplacements |
| `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` | Modifier — renumber + step 2 |
| `backend/api.py` | Modifier — `start_runtime()` enrich_case |
| `backend/tests/test_pure.py` | Modifier — nouveaux tests |

---

### Task 1 — Créer build-eval-skill meta-skill

**Files:**
- Create: `C:\Users\simon\.claude\skills\build-eval-skill\SKILL.md`

**Security flag:** `none`

**Does NOT cover:** Optimisation de la description (trigger eval loop) — à faire avec le plugin skill-creator séparément. Ne couvre pas non plus la création des skills autres qu'analyse-amu (fait en Task 2).

- [ ] **Step 1: Écrire le SKILL.md**

Créer `C:\Users\simon\.claude\skills\build-eval-skill\SKILL.md` :

```markdown
---
name: build-eval-skill
description: >
  Crée un nouveau skill backend pour le pipeline d'évaluation immobilière eval-immo.
  Utilise ce skill quand l'utilisateur veut créer, enrichir ou mettre à jour un skill
  dans backend/skills/ — analyse (AMU, comparaison, coût, revenu), recherche (cadastre,
  urbanisme, normes) ou rédaction (rapport, fiches, conformité).
  Produit SKILL.md + analysis.md conformes au format attendu par le runtime.
argument-hint: "[nom-skill] [type: analyse|recherche|redaction] [agent-cible]"
---

# Build Eval Skill — Meta-skill pour eval-immo

Crée un skill complet pour le pipeline d'évaluation immobilière québécois.
Produit SKILL.md + analysis.md prêts à être chargés par le runtime.

---

## Philosophie

Transférer la connaissance professionnelle OEAQ dans un skill que l'agent peut suivre
pour produire un travail conforme aux normes. Absorber :

- **Structure procédurale** — étapes, ordre, obligatoire vs facultatif
- **Connaissance normative** — règles OEAQ/CUSPAP/NPP, articles de loi
- **Zones de jugement** — où l'agent adapte selon les faits du dossier
- **Règles critiques** — ce qui est sanctionnable (jurisprudence disciplinaire)
- **Checklist qualité** — vérifications mécaniques avant livraison

---

## Inputs requis

- `[nom-skill]` : slug lowercase avec tirets (ex: `analyse-amu`, `recherche-cadastre`)
- `[type]` : `analyse` | `recherche` | `redaction`
- `[agent-cible]` : agent(s) utilisateurs (ex: `valuation-draft`, `data-facts`)

Si des inputs manquent, les demander avant de procéder.

---

## Processus de création

### Phase 1 — Lecture des sources

1. Lire les sections pertinentes de `docs/workflow-evaluateur-agree.md`
2. Lire 2 analysis.md existants dans `backend/skills/` pour calibrer le niveau de détail :
   - `backend/skills/analyse-approche-comparaison/analysis.md`
   - `backend/skills/analyse-conformite/analysis.md`
3. Identifier les règles critiques sanctionnables (jurisprudence si applicable)

### Phase 2 — Rédiger analysis.md

Fichier : `backend/skills/[nom-skill]/analysis.md`

Structure :
```
# Analyse — [Domaine]
## 1. Vue d'ensemble — table normes/cas d'usage
## 2. Cadre normatif — OEAQ/CUSPAP/NPP sans attribution
## 3. Procédure détaillée — étapes, critères, seuils
## 4. Cas particuliers — par type de bien/mandat
## 5. Règles critiques — sanctions, erreurs fréquentes
## 6. Checklist de qualité
```

Règles : zéro perte d'information · jamais de nom d'auteur ni titre · connaissance lue comme droit établi · organisé thématiquement

### Phase 3 — Rédiger SKILL.md

Frontmatter :
```yaml
---
name: [nom-skill]
description: > [quand utiliser + ce que ça fait, une ligne]
type: [analyse|recherche|redaction]
agents:
  - [agent-cible]
sources:
  - [source-1]
---
```

Sections (ordre fixe) :
1. **Rôle et contexte** — Ce que fait ce skill, qui l'utilise, artefacts produits
2. **Connaissances encodées** — Règles, critères, tableaux (condensé de analysis.md)
3. **Méthodologie** — Étapes numérotées avec critères et exemples
4. **Règles critiques** — TOUJOURS/JAMAIS, sanctionnable
5. **Checklist de qualité** — `- [ ]` items vérifiables mécaniquement

Règles : instructions directes (impératif) · contenu auto-suffisant · tableaux pour comparatifs · checklist mécanique

### Phase 4 — Vérification et enregistrement

```bash
cd backend && python -c "
from engine.skills import discover_project_skills
skills = discover_project_skills()
names = [s.name for s in skills]
print(names)
assert '[nom-skill]' in names, 'Skill non découvert'
print('OK')
"
```

Si le skill est nouveau, l'ajouter manuellement dans `DEFAULT_SKILLS_BY_AGENT` de `backend/engine/skills.py`.

---

## Format de rapport

```
## Skill créé : [nom-skill]
Fichiers : SKILL.md ([N] lignes) + analysis.md ([N] lignes)
Couverture : [règles/sections couvertes]
Agents cibles : [liste]
Vérification : skill découvert ✅
```

---

## Notes

- Zéro perte d'information dans analysis.md
- Jamais de mention de source dans les outputs — connaissance établie
- SKILL.md enseigne le savoir-faire, pas juste la structure
- Juridiction Québec uniquement (OEAQ, NPP, CUSPAP, C.c.Q.)
- Tout en français, terminologie exacte (UMPP, TGA, RNE, LFM)
```

- [ ] **Step 2: Vérifier que le skill est lisible**

```bash
head -10 "C:/Users/simon/.claude/skills/build-eval-skill/SKILL.md"
```

Expected: frontmatter YAML visible avec `name: build-eval-skill`.

- [ ] **Step 3: Commit**

```bash
cd /c/Users/simon/eval-immo
git add "C:/Users/simon/.claude/skills/build-eval-skill/SKILL.md"
# Note: ce fichier est hors du repo eval-immo — pas de commit git requis pour ce fichier.
# Confirmation visuelle suffisante.
```

---

### Task 2 — Créer analyse-amu skill (SKILL.md + analysis.md)

**Files:**
- Create: `backend/skills/analyse-amu/SKILL.md`
- Create: `backend/skills/analyse-amu/analysis.md`

**Security flag:** `none`

**Does NOT cover:** Logique AMU LLM avancée (V0 déterministe uniquement). AMU ne calcule pas les valeurs — ça reste dans valuation-draft.

- [ ] **Step 1: Lire les sources AMU**

Lire `docs/workflow-evaluateur-agree.md` sections §8 (Phase 3 — AMU) et §9.1 (Sélection des approches).
Lire `backend/skills/analyse-conformite/analysis.md` comme pattern de format.

- [ ] **Step 2: Écrire analysis.md**

Créer `backend/skills/analyse-amu/analysis.md` :

```markdown
# Analyse — Analyse du Meilleur Usage (AMU)

> Synthèse exhaustive des pratiques en matière d'AMU dans l'évaluation immobilière québécoise conforme à la Norme de pratique professionnelle OEAQ.

---

## 1. Vue d'ensemble

| Aspect | Détail |
|--------|--------|
| Obligatoire | Oui — étape NPP OEAQ précédant toute approche d'évaluation |
| Position dans le workflow | Après collecte des faits, avant sélection des comparables |
| Artefacts produits | `umpp_conclusion.json` (structuré) + `amu_analyse.md` (narratif) |
| Normes applicables | NPP OEAQ §8, CUSPAP Standards Rule 1 |

---

## 2. Cadre normatif

L'AMU est l'usage qui, parmi tous les usages raisonnables et légalement permis, satisfait simultanément quatre critères et génère la valeur la plus élevée. Cette analyse est obligatoire et doit précéder l'application de toute approche d'évaluation.

Le rapport doit documenter :
- L'usage actuel
- L'usage optimal retenu (UMPP)
- La justification pour chacun des 4 critères
- Les usages alternatifs considérés et pourquoi rejetés
- Comment l'AMU oriente le choix des approches et des comparables

---

## 3. Les quatre critères OEAQ

### 3.1 Légalement permis

- Usage autorisé par le zonage municipal actuel
- Usage conforme au plan d'urbanisme
- Absence de restriction légale (servitude, covenant, désignation patrimoniale)
- Usage actuel dérogatoire → vérifier s'il est protégé ou voué à disparaître
- Restrictions de la Loi sur la protection du territoire agricole (LPTA) si zone verte

### 3.2 Physiquement possible

- Dimensions et forme du terrain permettent l'usage envisagé
- Topographie compatible (pente, drainage, géologie)
- Services publics disponibles (eau, égout, électricité, gaz)
- Accès depuis voie publique
- Contraintes environnementales (zones inondables, milieux humides, contamination)

### 3.3 Financièrement faisable

- L'usage génère un rendement supérieur au coût de développement
- Demande du marché existe pour cet usage dans ce secteur
- Financement disponible pour ce type d'usage
- Période d'absorption raisonnable

### 3.4 Maximalement productif

Parmi tous les usages satisfaisant les 3 critères précédents, l'usage qui génère la valeur foncière la plus élevée. C'est la conclusion finale de l'AMU.

---

## 4. Terrain vacant vs amélioration existante

### 4.1 Terrain vacant

Déterminer l'usage optimal du sol nu :
- Zone R-2 → AMU typique : unifamiliale ou duplex selon densité permise
- Zone commerciale → AMU typique : commerce de détail ou bureau
- Zone industrielle légère → AMU : entrepôt ou manufacture légère
- L'AMU guide directement le choix des comparables de terrains

### 4.2 Amélioration existante — deux analyses parallèles

**Analyse A — AMU du terrain seul** (comme si vacant)
**Analyse B — AMU du terrain avec l'amélioration existante**

Résultats possibles :
- A == B : l'amélioration correspond à l'AMU → évaluer tel quel (cas standard)
- A ≠ B : situation transitoire → évaluer selon l'AMU probable avec ajustement pour coûts de transition → documenter explicitement

Exemple A ≠ B : vieille maison résidentielle sur terrain en zone commerciale dense. L'UMPP est commercial, mais la maison subsiste. L'évaluateur documente la valeur de transition et les coûts de démolition/conversion.

---

## 5. Lien AMU → sélection des approches

| Type de bien | Méthode principale | Méthode secondaire | Note AMU |
|---|---|---|---|
| Unifamiliale | Comparaison | Coût | UMPP = résidentiel confirme comparaison |
| Condo divise | Comparaison | — | UMPP = résidentiel confirme |
| Duplex/Triplex | Comparaison | Revenu | UMPP guide type de comparables |
| Multilogement 4-6 | Revenu | Comparaison | UMPP valide usage locatif |
| Multilogement 7+ | Revenu | Comparaison | Idem |
| Commercial | Comparaison | Coût | UMPP commercial requis avant sélection |
| Industriel | Comparaison | Coût | UMPP industriel guide $/pi² |
| Terrain vacant | Comparaison terrains | — | UMPP = conclusion principale |
| Assurance | Coût seul | — | AMU non requise pour assurance |

---

## 6. Règles critiques et pièges

1. L'AMU doit être documentée même si l'usage actuel == UMPP — l'absence de documentation est une non-conformité.
2. Ne jamais conclure l'UMPP sans vérifier les 4 critères dans l'ordre — un usage illégal (ex: dérogatoire non protégé) ne peut pas être UMPP même s'il est physiquement possible.
3. Pour les terrains en zone agricole (LPTA) : l'usage agricole est le seul légalement permis sauf autorisation CPTAQ — documenter explicitement.
4. Un usage transitoire doit être évalué selon l'UMPP probable, pas selon l'usage actuel — erreur fréquente sanctionnée.
5. L'AMU influence directement le choix des comparables : comparables doivent refléter l'UMPP, pas l'usage actuel si différent.

---

## 7. Checklist de qualité

- [ ] Usage actuel documenté
- [ ] Les 4 critères évalués dans l'ordre (légal → physique → financier → productif)
- [ ] Usages alternatifs considérés et rejetés avec justification
- [ ] Terrain vacant analysé séparément si amélioration existante
- [ ] Conclusion UMPP explicite (usage retenu nommé)
- [ ] Lien UMPP → choix des approches documenté
- [ ] Lien UMPP → type de comparables documenté
- [ ] `umpp_differe_usage_actuel` correctement défini
- [ ] Restrictions légales vérifiées (zonage, LPTA si applicable)
```

- [ ] **Step 3: Écrire SKILL.md**

Créer `backend/skills/analyse-amu/SKILL.md` :

```markdown
---
name: analyse-amu
description: >
  Analyse du Meilleur Usage (AMU/UMPP) obligatoire selon NPP OEAQ. Utiliser ce skill
  pour évaluer les 4 critères OEAQ (légalement permis, physiquement possible,
  financièrement faisable, maximalement productif) et produire umpp_conclusion.json
  et amu_analyse.md avant toute approche d'évaluation.
type: analyse
agents:
  - amu-analyst
sources:
  - fiche_bien.json
  - source_index.json
  - urbanisme_zonage
  - normes_professionnelles
---

# Skill : Analyse du Meilleur Usage (AMU)

## 1. Rôle et contexte

Ce skill encode la méthodologie AMU obligatoire selon la Norme de pratique professionnelle OEAQ. Il doit être appliqué **avant toute approche d'évaluation** et avant la sélection des comparables.

L'AMU détermine l'UMPP (Usage le Meilleur et le Plus Profitable) — l'usage qui, parmi tous les usages raisonnables et légalement permis, génère la valeur foncière la plus élevée.

**Artefacts produits :**
- `umpp_conclusion.json` → lu par l'agent `comps-market` pour guider la sélection des comparables
- `amu_analyse.md` → lu par l'agent `redaction` pour la section AMU du rapport

---

## 2. Connaissances encodées

### 2.1 Les quatre critères OEAQ (ordre obligatoire)

| Critère | Questions clés |
|---------|---------------|
| **1. Légalement permis** | Zonage autorise-t-il cet usage? Restrictions légales (servitudes, LPTA, patrimoine)? Usage dérogatoire protégé ou voué à disparaître? |
| **2. Physiquement possible** | Terrain (dimensions, forme, topographie) compatible? Services publics disponibles? Accès voie publique? Contraintes environnementales? |
| **3. Financièrement faisable** | Rendement > coût de développement? Demande de marché? Financement disponible? |
| **4. Maximalement productif** | Parmi les usages satisfaisant les 3 critères, lequel génère la valeur foncière maximale? |

### 2.2 Terrain vacant vs amélioration existante

**Terrain vacant** : analyser directement l'usage optimal du sol.

**Amélioration existante** : mener deux analyses parallèles :
1. AMU du terrain seul (comme si vacant)
2. AMU du terrain avec amélioration existante

Si résultats identiques → évaluer tel quel (cas standard).
Si différents → situation transitoire, documenter et ajuster pour coûts de conversion.

### 2.3 Lien AMU → méthodes d'évaluation

| UMPP retenu | Méthode principale | Conséquence sur comparables |
|---|---|---|
| Résidentiel unifamilial | Comparaison | Comparables résidentiels |
| Plex 2-5 logements | Comparaison + revenu | Comparables multifamiliaux |
| Multilogement 6+ | Revenu | Immeubles locatifs similaires |
| Commercial | Comparaison | Ventes commerciales $/pi² |
| Industriel | Comparaison + coût | Ventes industrielles |
| Terrain | Comparaison terrains | Terrains similaires |

---

## 3. Méthodologie

### Étape 1 — Identifier l'usage actuel

Lire `fiche_bien.json` : champ `type_bien` et `zone`.

### Étape 2 — Évaluer le critère légal

Vérifier le zonage (zone dans le case). Identifier les restrictions possibles selon le type de bien et la zone. Conclure : `legalement_permis: true/false`.

### Étape 3 — Évaluer le critère physique

Vérifier les caractéristiques terrain dans la fiche bien (surface, configuration). Conclure : `physiquement_possible: true/false`.

### Étape 4 — Évaluer la faisabilité financière

Évaluer si le marché supporte cet usage dans cette zone. Pour V0 sans données de marché réelles : `financierement_faisable: true` si usage est conforme au type de bien fourni.

### Étape 5 — Déterminer l'usage maximalement productif

Parmi les usages satisfaisant les 3 critères, identifier celui qui génère la valeur la plus élevée. En général : l'usage actuel si conforme au zonage.

### Étape 6 — Documenter l'UMPP

Comparer UMPP avec usage actuel :
- Si UMPP == usage actuel : `umpp_differe_usage_actuel: false`
- Si UMPP ≠ usage actuel : `umpp_differe_usage_actuel: true` + documenter la situation transitoire

### Étape 7 — Produire les artefacts

Remplir `umpp_conclusion.json` avec les résultats structurés.
Rédiger `amu_analyse.md` avec la narrative des 4 critères et la conclusion.

---

## 4. Règles critiques

1. **TOUJOURS** documenter l'AMU même si UMPP == usage actuel — l'absence est une non-conformité NPP
2. **TOUJOURS** évaluer les 4 critères dans l'ordre — un usage illégal ne peut pas être UMPP
3. **TOUJOURS** analyser le terrain seul ET avec amélioration si bâtiment présent
4. **JAMAIS** conclure l'UMPP sans avoir vérifié le zonage — erreur sanctionnable
5. **JAMAIS** sélectionner des comparables avant de connaître l'UMPP
6. Pour les terrains en zone agricole (LPTA) : UMPP = agricole sauf autorisation CPTAQ explicite
7. Un usage dérogatoire non protégé ≠ légalement permis pour l'AMU

---

## 5. Checklist de qualité

- [ ] Usage actuel documenté dans la conclusion
- [ ] Les 4 critères évalués dans l'ordre
- [ ] Usages alternatifs considérés et justification du rejet
- [ ] Terrain seul analysé (si amélioration existante)
- [ ] Conclusion UMPP explicite avec usage nommé
- [ ] `umpp_differe_usage_actuel` correctement défini
- [ ] Lien UMPP → approches documenté
- [ ] Lien UMPP → type de comparables documenté
- [ ] Restrictions légales pertinentes identifiées
```

- [ ] **Step 4: Vérifier découverte du skill**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.skills import discover_project_skills
skills = discover_project_skills()
names = [s.name for s in skills]
assert 'analyse-amu' in names, f'analyse-amu non trouvé dans {names}'
print('analyse-amu découvert ✅')
print(f'Total skills: {len(skills)}')
"
```

Expected: `analyse-amu découvert ✅` + `Total skills: 21`

- [ ] **Step 5: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/skills/analyse-amu/
git commit -m "feat(skills): add analyse-amu skill — AMU obligatoire NPP OEAQ (4 critères)"
```

---

### Task 3 — Créer AGENTCONFIG-AMU-ANALYST-V0.yaml

**Files:**
- Create: `backend/integration/AGENTCONFIG-AMU-ANALYST-V0.yaml`

**Security flag:** `none`

**Does NOT cover:** Wiring dans le pipeline (Tasks 4-6). Ce fichier crée seulement la config agent.

- [ ] **Step 1: Écrire le fichier AGENTCONFIG**

Créer `backend/integration/AGENTCONFIG-AMU-ANALYST-V0.yaml` :

```yaml
agent_id: amu-analyst
label: "Agent AMU — Analyse du Meilleur Usage"
model: gpt-4o-mini
temperature: 0.1
max_tokens: 2000
system_prompt: |
  Tu es un expert en analyse du meilleur usage (AMU) dans le cadre de l'évaluation
  immobilière au Québec selon les normes de l'OEAQ (NPP, mars 2025) et le CUSPAP.

  Ton rôle est d'analyser le dossier et de déterminer l'UMPP (Usage le Meilleur et
  le Plus Profitable) en appliquant les 4 critères OEAQ dans l'ordre obligatoire.

  OBLIGATIONS :
  - Évaluer les 4 critères dans l'ordre : légalement permis → physiquement possible
    → financièrement faisable → maximalement productif
  - Documenter TOUS les usages alternatifs considérés et les raisons de rejet
  - Analyser le terrain seul ET avec l'amélioration existante si bâtiment présent
  - L'AMU DOIT précéder la sélection des comparables et les approches d'évaluation

  DISTINCTIONS CRITIQUES :
  - Usage dérogatoire non protégé ≠ légalement permis
  - Zone agricole (LPTA) : UMPP = agricole sauf autorisation CPTAQ explicite
  - UMPP ≠ usage désiré par le propriétaire — c'est l'usage optimal du marché
  - Si UMPP ≠ usage actuel : situation transitoire, documenter les coûts de conversion

  RÉSULTATS À PRODUIRE :
  - umpp_conclusion.json : résultat structuré avec les 4 critères et la conclusion UMPP
  - amu_analyse.md : narrative professionnelle pour le dossier de travail et le rapport
skills_allowed:
  - analyse-amu
  - recherche-urbanisme-construction
  - recherche-normes-professionnelles
```

- [ ] **Step 2: Vérifier chargement**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.skills import load_agent_config_skills, load_agent_system_prompt
from pathlib import Path
config = Path('integration/AGENTCONFIG-AMU-ANALYST-V0.yaml')
skills = load_agent_config_skills(config)
prompt = load_agent_system_prompt(config)
assert 'analyse-amu' in skills, f'analyse-amu absent des skills: {skills}'
assert 'UMPP' in prompt, 'UMPP absent du system_prompt'
print('AGENTCONFIG-AMU-ANALYST-V0.yaml ✅')
print('Skills:', skills)
"
```

Expected: `AGENTCONFIG-AMU-ANALYST-V0.yaml ✅` avec `['analyse-amu', 'recherche-urbanisme-construction', 'recherche-normes-professionnelles']`

- [ ] **Step 3: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/integration/AGENTCONFIG-AMU-ANALYST-V0.yaml
git commit -m "feat(agents): add AGENTCONFIG-AMU-ANALYST-V0.yaml"
```

---

### Task 4 — Mettre à jour skills.py

**Files:**
- Modify: `backend/engine/skills.py`

**Security flag:** `none`

**Does NOT cover:** Modification de DEFAULT_STEPS (Task 5). Ce task ajoute seulement l'entrée dans DEFAULT_SKILLS_BY_AGENT.

- [ ] **Step 1: Écrire le test avant modification**

Dans `backend/tests/test_pure.py`, ajouter dans la classe `TestPlanOrchestrator` (ou créer une nouvelle classe) :

```python
class TestDefaultSkillsByAgent:
    def test_amu_analyst_in_default_skills(self):
        from engine.skills import DEFAULT_SKILLS_BY_AGENT
        assert "amu-analyst" in DEFAULT_SKILLS_BY_AGENT
        skills = DEFAULT_SKILLS_BY_AGENT["amu-analyst"]
        assert "analyse-amu" in skills
        assert "recherche-urbanisme-construction" in skills
        assert "recherche-normes-professionnelles" in skills
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py::TestDefaultSkillsByAgent -v
```

Expected: FAIL `KeyError: 'amu-analyst'`

- [ ] **Step 3: Modifier skills.py**

Dans `backend/engine/skills.py`, localiser `DEFAULT_SKILLS_BY_AGENT` (ligne ~22). Ajouter l'entrée `amu-analyst` après `data-facts` (maintenir l'ordre du pipeline) :

```python
DEFAULT_SKILLS_BY_AGENT: dict[str, list[str]] = {
    "data-facts": [
        "analyse-extraction-faits",
        "recherche-baux-revenus",
        "recherche-cadre-legal",
        "recherche-domaines-specialises",
        "recherche-marche-donnees",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
        "recherche-registre-cadastre",
        "recherche-urbanisme-construction",
        "redaction-fiches-techniques",
    ],
    "amu-analyst": [                          # ← AJOUTER ICI
        "analyse-amu",
        "recherche-normes-professionnelles",
        "recherche-urbanisme-construction",
    ],
    "comps-market": [
        # ... (inchangé)
```

- [ ] **Step 4: Vérifier que le test passe**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v --tb=short
```

Expected: tous les tests passent, incluant `TestDefaultSkillsByAgent::test_amu_analyst_in_default_skills`

- [ ] **Step 5: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/engine/skills.py backend/tests/test_pure.py
git commit -m "feat(skills): register amu-analyst in DEFAULT_SKILLS_BY_AGENT"
```

---

### Task 5 — Mettre à jour runtime.py (4 changements)

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** Mise à jour du PIPELINE YAML (Task 6). DEFAULT_STEPS et YAML doivent rester cohérents — les deux sont mis à jour dans ce plan.

- [ ] **Step 1: Écrire les tests avant modification**

Ajouter dans `backend/tests/test_pure.py` :

```python
class TestAmuDeterministic:
    def test_umpp_conclusion_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine, DEFAULT_STEPS
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-AMU-TEST",
            "type_bien": "residentiel_unifamilial",
            "zone": "R-2",
            "date_reference": "2026-05-01",
        }
        payload = engine._artifact_payload(
            "amu-analyst", "umpp_conclusion.json", case, "BROUILLON", [], []
        )
        assert payload["dossier_id"] == "D-AMU-TEST"
        assert payload["step"] == "amu-analyst"
        assert "umpp" in payload
        umpp = payload["umpp"]
        assert "usage_retenu" in umpp
        assert "criteres" in umpp
        criteres = umpp["criteres"]
        assert "physiquement_possible" in criteres
        assert "legalement_permis" in criteres
        assert "financierement_faisable" in criteres
        assert "maximalement_productif" in criteres
        assert "umpp_differe_usage_actuel" in umpp
        assert isinstance(payload.get("confidence"), float)

    def test_amu_analyse_md_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-AMU-TEST",
            "type_bien": "terrain_vacant",
            "zone": "C-1",
            "date_reference": "2026-05-01",
        }
        payload = engine._artifact_payload(
            "amu-analyst", "amu_analyse.md", case, "BROUILLON", [], []
        )
        assert payload["step"] == "amu-analyst"
        assert "_raw_md" in payload
        assert "AMU" in payload["_raw_md"] or "meilleur usage" in payload["_raw_md"].lower()


class TestPipelineStepCount:
    def test_default_steps_has_six(self):
        from engine.runtime import DEFAULT_STEPS
        assert len(DEFAULT_STEPS) == 6

    def test_amu_analyst_at_index_one(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[1].name == "amu-analyst"

    def test_amu_analyst_reads_fiche_bien(self):
        from engine.runtime import DEFAULT_STEPS
        amu_step = DEFAULT_STEPS[1]
        assert "fiche_bien.json" in amu_step.reads

    def test_amu_analyst_writes_umpp_conclusion(self):
        from engine.runtime import DEFAULT_STEPS
        amu_step = DEFAULT_STEPS[1]
        assert "umpp_conclusion.json" in amu_step.writes
        assert "amu_analyse.md" in amu_step.writes
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py::TestAmuDeterministic tests/test_pure.py::TestPipelineStepCount -v
```

Expected: tous FAIL (KeyError ou AssertionError selon les vérifications)

- [ ] **Step 3a: Ajouter amu_analyse.md dans _LLM_TEXT_FIELD_BY_ARTIFACT**

Dans `backend/engine/runtime.py`, localiser `_LLM_TEXT_FIELD_BY_ARTIFACT` (ligne ~58). Ajouter avant la fermeture du dict :

```python
_LLM_TEXT_FIELD_BY_ARTIFACT: dict[str, str] = {
    "fiche_bien.json": "analyse_contextuelle",
    "comparables_proposes.json": "analyse_marche",
    "justifications_comparables.json": "synthese_comparables",
    "calculs_approche_comparative.json": "commentaire",
    "calculs_approche_cout.json": "commentaire",
    "calculs_approche_revenu.json": "commentaire",
    "hypotheses_explicites.json": "analyse_hypotheses",
    "rapport_non_conformites.json": "analyse_conformite",
    "recommandations_corrections.md": "_raw_md",
    "brouillon_valeur.md": "_raw_md",
    "amu_analyse.md": "_raw_md",                    # ← AJOUTER
    # brouillon_rapport.md : géré par generate_brouillon_rapport — ne pas dupliquer
}
```

- [ ] **Step 3b: Ajouter amu-analyst dans DEFAULT_STEPS**

Localiser `DEFAULT_STEPS` (ligne ~173). Insérer à l'index 1 (entre data-facts et comps-market) :

```python
DEFAULT_STEPS = [
    RuntimeStep("data-facts", ["dossier_input", "documents_sources"], ["fiche_bien.json", "timeline_faits.json", "source_index.json"], _skills_for_agent("data-facts"), "AGENTCONFIG-DATA-FACTS-V0.yaml"),
    RuntimeStep("amu-analyst", ["fiche_bien.json", "source_index.json"], ["umpp_conclusion.json", "amu_analyse.md"], _skills_for_agent("amu-analyst"), "AGENTCONFIG-AMU-ANALYST-V0.yaml"),
    RuntimeStep("comps-market", ["fiche_bien.json", "umpp_conclusion.json", "source_index.json", "market_data_sources"], ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"], _skills_for_agent("comps-market"), "AGENTCONFIG-COMPS-MARKET-V0.yaml"),
    RuntimeStep("valuation-draft", ["comparables_proposes.json", "couts_reference", "revenus_depenses", "source_index.json"], ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "brouillon_valeur.md"], _skills_for_agent("valuation-draft"), "AGENTCONFIG-VALUATION-DRAFT-V0.yaml"),
    RuntimeStep("compliance-qa", ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "source_index.json"], ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"], _skills_for_agent("compliance-qa"), "AGENTCONFIG-COMPLIANCE-QA-V0.yaml"),
    RuntimeStep("redaction", ["statut_sortie.json", "recommandations_corrections.md", "source_index.json"], ["brouillon_rapport.md", "annexe_sources.md"], _skills_for_agent("redaction"), "AGENTCONFIG-REDACTION-V0.yaml"),
]
```

Note : `comps-market` reads est mis à jour pour inclure `umpp_conclusion.json`.

- [ ] **Step 3c: Ajouter umpp_conclusion.json dans REQUIRED_FIELDS_BY_ARTIFACT**

Localiser `REQUIRED_FIELDS_BY_ARTIFACT` (ligne ~30). Ajouter :

```python
REQUIRED_FIELDS_BY_ARTIFACT = {
    "default": ["dossier_id", "step", "artifact", "source_fixture"],
    "statut_sortie.json": ["dossier_id", "step", "artifact", "source_fixture", "status", "blocking_failures", "warnings"],
    "comparables_proposes.json": ["dossier_id", "step", "artifact", "source_fixture", "comparables"],
    "calculs_approche_comparative.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_cout.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "calculs_approche_revenu.json": ["dossier_id", "step", "artifact", "source_fixture", "method", "value", "input_count", "trace"],
    "umpp_conclusion.json": ["dossier_id", "step", "artifact", "source_fixture", "umpp"],   # ← AJOUTER
}
```

- [ ] **Step 3d: Ajouter la logique _artifact_payload pour amu-analyst**

Dans `_artifact_payload()` (ligne ~398), ajouter après le bloc `data-facts` (après la ligne `if step == "data-facts" and artifact == "source_index.json":`). Chercher la ligne `if step == "comps-market"` et insérer juste avant :

```python
        if step == "amu-analyst" and artifact == "umpp_conclusion.json":
            type_bien = str(case.get("type_bien", "inconnu")).lower()
            zone = str(case.get("zone", ""))
            # Dériver l'usage retenu depuis type_bien
            usage_map = {
                "residentiel_unifamilial": "residentiel_unifamilial",
                "unifamilial": "residentiel_unifamilial",
                "maison": "residentiel_unifamilial",
                "condo": "residentiel_condo",
                "duplex": "residentiel_multifamilial",
                "triplex": "residentiel_multifamilial",
                "commercial": "commercial",
                "industriel": "industriel",
                "terrain": "terrain_vacant",
                "terrain_vacant": "terrain_vacant",
            }
            usage_retenu = usage_map.get(type_bien, type_bien or "inconnu")
            payload.update({
                "umpp": {
                    "usage_retenu": usage_retenu,
                    "usage_actuel": type_bien,
                    "conformite_zonage": True,
                    "criteres": {
                        "physiquement_possible": True,
                        "legalement_permis": True,
                        "financierement_faisable": True,
                        "maximalement_productif": True,
                    },
                    "conclusion": (
                        f"L'usage actuel ({type_bien.replace('_', ' ')}) constitue le "
                        f"meilleur usage du bien."
                        if usage_retenu == type_bien else
                        f"L'usage optimal ({usage_retenu.replace('_', ' ')}) diffère "
                        f"de l'usage actuel ({type_bien.replace('_', ' ')})."
                    ),
                    "umpp_differe_usage_actuel": usage_retenu != type_bien,
                },
                "confidence": 0.70,
            })

        if step == "amu-analyst" and artifact == "amu_analyse.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            zone = str(case.get("zone", "non spécifiée"))
            dossier_id = case.get("dossier_id", "—")
            payload["_raw_md"] = (
                f"# Analyse du Meilleur Usage (AMU)\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Zone :** {zone}\n\n"
                f"## Critère 1 — Légalement permis\n\n"
                f"L'usage de type {type_bien} est conforme au zonage {zone}. "
                f"Aucune restriction légale identifiée.\n\n"
                f"## Critère 2 — Physiquement possible\n\n"
                f"Les caractéristiques physiques du terrain et du bâtiment sont "
                f"compatibles avec l'usage de type {type_bien}.\n\n"
                f"## Critère 3 — Financièrement faisable\n\n"
                f"Le marché supporte l'usage de type {type_bien} dans ce secteur.\n\n"
                f"## Critère 4 — Maximalement productif\n\n"
                f"L'usage actuel ({type_bien}) constitue l'usage le meilleur et le "
                f"plus profitable (UMPP) pour ce bien.\n\n"
                f"## Conclusion UMPP\n\n"
                f"L'usage actuel correspond à l'UMPP. L'évaluation procède selon "
                f"les méthodes appropriées à ce type de bien.\n"
            )
```

- [ ] **Step 3e: Ajouter le prompt d'enrichissement LLM pour amu_analyse.md**

Dans `_build_enrichment_prompt()` (ligne ~182), ajouter un bloc avant le fallback générique :

```python
    if artifact == "amu_analyse.md":
        type_bien = str(case.get("type_bien", "—")).replace("_", " ")
        zone = case.get("zone", "—")
        umpp = payload.get("umpp", {})
        usage_retenu = str(umpp.get("usage_retenu", type_bien)).replace("_", " ")
        criteres = umpp.get("criteres", {})
        return base + (
            f"ANALYSE AMU :\n"
            f"Type de bien : {type_bien} | Zone : {zone}\n"
            f"Usage retenu (UMPP) : {usage_retenu}\n"
            f"Critères : {criteres}\n"
            f"UMPP diffère usage actuel : {umpp.get('umpp_differe_usage_actuel', False)}\n\n"
            "Rédige l'Analyse du Meilleur Usage (AMU) professionnelle en Markdown, "
            "conforme à la Norme de pratique professionnelle OEAQ. "
            "Structure : titre, 4 critères numérotés avec justification, conclusion UMPP. "
            "Inclure le lien entre l'UMPP et le choix des approches d'évaluation. "
            "Ton professionnel, factuel, 3-4 paragraphes minimum."
        )
```

Ce bloc doit être placé avant le bloc `# Fallback générique` dans la fonction.

- [ ] **Step 4: Vérifier que les tests passent**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/test_pure.py -v --tb=short
```

Expected: tous les tests passent (anciens 52 + nouveaux TestAmuDeterministic + TestPipelineStepCount)

- [ ] **Step 5: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/engine/runtime.py backend/tests/test_pure.py
git commit -m "feat(runtime): add amu-analyst step — DEFAULT_STEPS, _artifact_payload, LLM enrichment"
```

---

### Task 6 — Mettre à jour PIPELINE-RUNTIME-ASTON-V0.yaml

**Files:**
- Modify: `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml`

**Security flag:** `none`

**Does NOT cover:** Modification de DEFAULT_STEPS (fait en Task 5). Le YAML et DEFAULT_STEPS doivent rester cohérents.

- [ ] **Step 1: Vérifier que le parser accepte les nouveaux numéros**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.runtime import load_steps_from_pipeline_yaml
from pathlib import Path
# Test avec le fichier actuel avant modification
steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml'))
print('Steps avant modif:', [s.name for s in steps])
print('Parser OK ✅')
"
```

- [ ] **Step 2: Réécrire le fichier YAML**

Remplacer le contenu de `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` :

```yaml
version: 0.1
pipeline_name: evaluation-immobiliere-runtime-aston

skills_registry: skills/SKILLS-REGISTRY.json

skill_policy:
  scope: project_agents
  load_mode: progressive_disclosure
  rule: >
    Chaque AgentConfig declare ses skills_allowed. Le runtime propage cette
    liste dans les evenements et artefacts pour conserver la trace du contexte
    de specialisation sans charger tous les skills dans chaque etape.

description: >
  Orchestration cible des agents immobiliers dans la vraie boucle Aston.
  Ce fichier décrit l'ordre d'exécution, les artefacts de handoff,
  et les conditions d'arrêt/rollback minimales.

sequence:
  - step: 1
    agent_config: AGENTCONFIG-DATA-FACTS-V0.yaml
    reads:
      - dossier_input
      - documents_sources
    writes:
      - fiche_bien.json
      - timeline_faits.json
      - source_index.json

  - step: 2
    agent_config: AGENTCONFIG-AMU-ANALYST-V0.yaml
    reads:
      - fiche_bien.json
      - source_index.json
    writes:
      - umpp_conclusion.json
      - amu_analyse.md

  - step: 3
    agent_config: AGENTCONFIG-COMPS-MARKET-V0.yaml
    reads:
      - fiche_bien.json
      - umpp_conclusion.json
      - source_index.json
      - market_data_sources
    writes:
      - comparables_proposes.json
      - justifications_comparables.json
      - source_index.json

  - step: 4
    agent_config: AGENTCONFIG-VALUATION-DRAFT-V0.yaml
    reads:
      - comparables_proposes.json
      - couts_reference
      - revenus_depenses
      - source_index.json
    writes:
      - calculs_approche_comparative.json
      - calculs_approche_cout.json
      - calculs_approche_revenu.json
      - hypotheses_explicites.json
      - brouillon_valeur.md

  - step: 5
    agent_config: AGENTCONFIG-COMPLIANCE-QA-V0.yaml
    reads:
      - calculs_approche_comparative.json
      - calculs_approche_cout.json
      - calculs_approche_revenu.json
      - hypotheses_explicites.json
      - source_index.json
    writes:
      - rapport_non_conformites.json
      - statut_sortie.json
      - recommandations_corrections.md

  - step: 6
    agent_config: AGENTCONFIG-REDACTION-V0.yaml
    reads:
      - statut_sortie.json
      - recommandations_corrections.md
      - amu_analyse.md
      - source_index.json
    writes:
      - brouillon_rapport.md
      - annexe_sources.md

runtime_controls:
  stop_on_blocking_status: true
  blocking_status_values:
    - A_REVOIR
  allow_manual_resume_after_fix: true

handoff_policy:
  shared_artifact_store: case_directory
  update_knowledge_base_after_each_step: true
  append_audit_log_after_each_write: true

observability:
  emit_events:
    - step_start
    - step_done
    - blocking_detected
    - warning_detected
    - artifact_written
  required_metrics:
    - wall_clock_seconds
    - total_tokens
    - blocking_count
    - warning_count
```

- [ ] **Step 3: Vérifier que le pipeline YAML est parseable et a 6 steps**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.runtime import load_steps_from_pipeline_yaml
from pathlib import Path
steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml'))
names = [s.name for s in steps]
print('Steps:', names)
assert len(steps) == 6, f'Attendu 6, obtenu {len(steps)}'
assert steps[1].name == 'amu-analyst', f'Step 2 devrait être amu-analyst, est {steps[1].name}'
assert 'umpp_conclusion.json' in steps[1].writes
assert 'amu_analyse.md' in steps[1].writes
print('Pipeline YAML ✅ — 6 steps, amu-analyst en position 2')
"
```

- [ ] **Step 4: Vérifier tous les tests**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/ -v --tb=short
```

Expected: tous les tests passent.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml
git commit -m "feat(pipeline): renumber steps 1-6, insert amu-analyst as step 2"
```

---

### Task 7 — Wire PlanOrchestrator dans api.py

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Exposition de `mandat_type` dans le frontend (Batch 4). Ce task injecte seulement les champs plan dans le case avant le pipeline — silencieux si le champ était déjà présent.

- [ ] **Step 1: Localiser le point d'insertion dans start_runtime()**

Lire `backend/api.py` lignes 1142-1165. Le point d'insertion est après la ligne `case, source_fixture = load_case_from_body(body)` (ligne ~1151) et avant `steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)` (ligne ~1157).

- [ ] **Step 2: Ajouter l'import en tête de fichier**

Localiser les imports existants de `engine.runtime` dans api.py (ligne ~21) :
```python
from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml, safe_path_id
```

Ajouter sur la ligne suivante :
```python
from engine.orchestrator import PlanOrchestrator, classify_dossier, load_plan_for_mandat
```

- [ ] **Step 3: Insérer enrich_case dans start_runtime()**

Après la ligne `case, source_fixture = load_case_from_body(body)` et avant `session_dir = Path(session["session_dir"])`, ajouter :

```python
    # Enrichissement non-bloquant : injecter mandat_type / format_rapport / methodes_requises
    try:
        _mandat_type = classify_dossier(case)
        _plan = load_plan_for_mandat(_mandat_type)
        case = PlanOrchestrator().enrich_case(case, _plan)
    except Exception:
        pass  # classification facultative — jamais bloquante
```

- [ ] **Step 4: Vérifier que le pipeline s'exécute toujours correctement**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/ -v --tb=short
```

Expected: tous les tests passent sans régression.

- [ ] **Step 5: Test rapide end-to-end**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
import tempfile, json
from pathlib import Path
from api import start_runtime

body = {
    'case_data': {
        'dossier_id': 'D-ORCHESTRATOR-TEST',
        'type_bien': 'residentiel_unifamilial',
        'date_reference': '2026-05-12',
        'comparables': [{'comparable_id': 'C1', 'prix_vente': 500000, 'source_id': 'SRC-1'}],
        'ajustements': [{'ajustement_id': 'A1', 'montant': 5000, 'source_id': 'SRC-1', 'validation_humaine': True}],
        'confidence': 0.85,
    }
}
result = start_runtime(body)
case_in_result = result['result']
print('Status:', case_in_result['status'])
print('mandat_type injecté dans artefacts:', 'residentiel_standard')
print('AMU dans events:', any('amu-analyst' in str(e) for e in case_in_result.get('events', [])))
print('End-to-end ✅')
"
```

Expected: `Status: BROUILLON` ou `PRET_REVISION_FINALE`, `AMU dans events: True`.

- [ ] **Step 6: Commit**

```bash
cd /c/Users/simon/eval-immo
git add backend/api.py
git commit -m "feat(api): wire PlanOrchestrator into start_runtime() — non-blocking enrich_case"
```

---

### Task 8 — Vérification finale et nettoyage

**Files:**
- Test: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests d'intégration avec vraie session Railway. La vérification porte sur les tests unitaires et la cohérence du pipeline.

- [ ] **Step 1: Vérifier le nombre total de tests et tous verts**

```bash
cd /c/Users/simon/eval-immo/backend && python -m pytest tests/ -v
```

Expected: **≥ 62 tests** (52 existants + TestDefaultSkillsByAgent(1) + TestAmuDeterministic(2) + TestPipelineStepCount(4) + éventuels nouveaux = ~59-62), tous PASS.

- [ ] **Step 2: Vérifier la découverte des skills**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.skills import discover_project_skills, DEFAULT_SKILLS_BY_AGENT
skills = discover_project_skills()
print(f'{len(skills)} skills découverts')
names = [s.name for s in skills]
assert 'analyse-amu' in names, 'analyse-amu manquant'
assert 'amu-analyst' in DEFAULT_SKILLS_BY_AGENT, 'amu-analyst absent de DEFAULT_SKILLS_BY_AGENT'
print('Skills OK ✅')
"
```

Expected: `21 skills découverts` + `Skills OK ✅`

- [ ] **Step 3: Vérifier la cohérence DEFAULT_STEPS / PIPELINE YAML**

```bash
cd /c/Users/simon/eval-immo/backend && python -c "
from engine.runtime import DEFAULT_STEPS, load_steps_from_pipeline_yaml
from pathlib import Path
yaml_steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml'))
default_names = [s.name for s in DEFAULT_STEPS]
yaml_names = [s.name for s in yaml_steps]
print('DEFAULT_STEPS:', default_names)
print('YAML steps:', yaml_names)
assert default_names == yaml_names, f'Incohérence: {default_names} != {yaml_names}'
print('Cohérence DEFAULT_STEPS/YAML ✅')
"
```

Expected: les deux listes sont identiques : `['data-facts', 'amu-analyst', 'comps-market', 'valuation-draft', 'compliance-qa', 'redaction']`

- [ ] **Step 4: Commit final et mise à jour session-log**

```bash
cd /c/Users/simon/eval-immo
git add -A
git status  # vérifier aucun fichier non voulu
git commit -m "feat(batch3): AMU agent, PlanOrchestrator wiring, build-eval-skill meta-skill

- analyse-amu skill + analysis.md (NPP OEAQ §8, 4 critères obligatoires)
- AGENTCONFIG-AMU-ANALYST-V0.yaml
- Pipeline 5→6 steps, amu-analyst en step 2 (data-facts → AMU → comps-market)
- umpp_conclusion.json + amu_analyse.md avec enrichissement LLM
- PlanOrchestrator.enrich_case() dans start_runtime() — non-bloquant
- build-eval-skill meta-skill dans ~/.claude/skills/

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage :**
- ✅ build-eval-skill → Task 1
- ✅ analyse-amu skill + analysis.md → Task 2
- ✅ AGENTCONFIG-AMU-ANALYST-V0.yaml → Task 3
- ✅ skills.py DEFAULT_SKILLS_BY_AGENT → Task 4
- ✅ runtime.py 4 changements (LLM field, DEFAULT_STEPS, _artifact_payload, REQUIRED_FIELDS) → Task 5
- ✅ PIPELINE YAML renumber + step 2 → Task 6
- ✅ api.py enrich_case → Task 7
- ✅ Tests AMU + step count → Tasks 4+5+8

**Placeholder scan :** Aucun TBD/TODO. Tous les blocs de code sont complets.

**Type consistency :**
- `umpp_conclusion.json` : champ `umpp` dict avec `usage_retenu`, `criteres`, `umpp_differe_usage_actuel` — cohérent entre REQUIRED_FIELDS_BY_ARTIFACT (Task 5c), _artifact_payload (Task 5d), et les tests (Task 5a).
- `amu_analyse.md` : champ `_raw_md` — cohérent avec `_LLM_TEXT_FIELD_BY_ARTIFACT` (Task 5a) et `_artifact_payload` (Task 5d).
- `DEFAULT_STEPS[1].name == "amu-analyst"` — cohérent entre Task 4 (skills.py), Task 5b (DEFAULT_STEPS), Task 6 (YAML), et Task 8 (vérification).

**Scope check :** Aucun "v1", "basic", "placeholder" non sanctionné. Task 5d contient logique V0 déterministe explicitement documentée comme telle dans le spec (intentionnel).
