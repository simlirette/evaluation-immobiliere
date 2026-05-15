# Batch 4 — Mandat Intake + FTA Skill + Frontend Plan de mandat

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter l'agent `mandat-intake` (step 0), les skills `redaction-lettre-mandat` et `analyse-approche-fta`, et exposer les champs mandat dans le frontend DossierPanel.

**Architecture:** Nouvel agent déterministe V0 inséré en position 0 du pipeline (7 steps). Produit deux artefacts : `conflit_interets.json` (déterministe) et `lettre_mandat.md` (enrichi LLM). Les champs mandat (`mandat_type`, `format_rapport`, `methodes_requises`, `methode_preponderante`) sont persistés dans `session.json` après `enrich_case()` et exposés via `app_session_view()`. Le frontend lit `AppState.active.mandat` et affiche une section "Plan de mandat" dans DossierPanel.

**Tech Stack:** Python (backend/engine), Flask-like api.py, YAML (pipeline/agentconfig), TypeScript/React (src/)

**Assumptions:**
- `enrich_case()` enrichit déjà `case` avec `mandat_type`, `format_rapport`, `methodes_requises`, `methode_preponderante` — Batch 3 wiring déjà en place dans `api.py`.
- `session["session_dir"]` est défini avant le bloc de persistance mandat (il est défini dans `create_session()` avant `start_runtime()`).
- Les 59 tests existants ne hardcodent pas `len(DEFAULT_STEPS) == 6` sauf `TestPipelineStepCount.test_default_steps_has_six` — qui sera mis à jour dans Task 9.
- `fetchPropertyFacts` dans DossierPanel lit `AppState.active.fact_chips` — on ajoutera `mandat` comme champ séparé dans le même fetch via `fetchAppState`.

---

## File Structure

| Fichier | Action |
|---|---|
| `backend/skills/redaction-lettre-mandat/SKILL.md` | Créer |
| `backend/skills/redaction-lettre-mandat/analysis.md` | Créer |
| `backend/skills/analyse-approche-fta/SKILL.md` | Créer |
| `backend/skills/analyse-approche-fta/analysis.md` | Créer |
| `backend/integration/AGENTCONFIG-MANDAT-INTAKE-V0.yaml` | Créer |
| `backend/engine/skills.py` | Modifier (2 changements) |
| `backend/engine/runtime.py` | Modifier (5 changements) |
| `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` | Modifier (renumber 1→7, insert step 1) |
| `backend/api.py` | Modifier (2 changements) |
| `src/lib/runtime-api.ts` | Modifier (ajouter `mandat` dans AppState.active) |
| `src/components/panels/DossierPanel.tsx` | Modifier (section "Plan de mandat") |
| `backend/tests/test_pure.py` | Modifier (3 nouveaux tests + mise à jour) |

---

### Task 1: Créer le skill `redaction-lettre-mandat`

**Files:**
- Create: `backend/skills/redaction-lettre-mandat/analysis.md`
- Create: `backend/skills/redaction-lettre-mandat/SKILL.md`

**Security flag:** `none`

**Does NOT cover:** Signature numérique de la lettre (Batch 5). Validation de la présence du commanditaire (V0 = `[COMMANDITAIRE]` placeholder).

- [ ] **Step 1: Créer `analysis.md`**

```markdown
# Analyse — Rédaction de la lettre de mandat (§6.3 OEAQ)

## Source doctrine
workflow-evaluateur-agree.md §6.3 — Établissement du mandat et lettre d'engagement

## Rôle de l'artefact
La lettre de mandat est un document obligatoire selon le Code de déontologie de l'OEAQ.
Elle doit être remise au commanditaire AVANT le début de l'inspection. Elle constitue
le contrat écrit entre l'évaluateur et le commanditaire.

## 10 éléments obligatoires (§6.3 OEAQ)

1. **Identification précise de la propriété** — adresse complète, description légale
2. **Identification du commanditaire et du client** — nom, coordonnées, relation
3. **Type d'acte professionnel** — évaluation / examen / consultation
4. **Type de rapport** — complet / restreint / sommaire
5. **Fin d'évaluation** — hypothécaire, succession, litige, vente, assurance, etc.
6. **Date d'évaluation (date de référence)**
7. **Étendue de l'inspection** — interne, externe, non-accès
8. **Hypothèses et limitations préalables connues**
9. **Honoraires et conditions de paiement**
10. **Date de livraison prévue** + **Signatures des deux parties**

## Workflow de rédaction

### Étape 1 — Collecter les informations disponibles
- Extraire du dossier : type de bien, adresse anonymisée, dossier_id, date de référence
- Extraire du plan de mandat : mandat_type, format_rapport, methodes_requises
- Identifier le commanditaire (si fourni ; sinon `[COMMANDITAIRE]`)

### Étape 2 — Structurer la lettre
- En-tête : date, référence dossier, adresse commanditaire
- Corps : 10 sections correspondant aux éléments obligatoires
- Honoraires : `[À CONFIRMER selon entente]`
- Date livraison : `[À CONFIRMER]`
- Signature : deux blocs (évaluateur agréé + commanditaire)

### Étape 3 — Valider la conformité déontologique
- Tous les 10 éléments présents ?
- Ton professionnel, juridiction Québec ?
- Références OEAQ explicites si mandat complexe ?

## Règles critiques

- Les honoraires ne peuvent PAS être conditionnels à la valeur obtenue (violation du Code de déontologie OEAQ)
- La lettre doit précéder l'inspection — ne pas rédiger après coup
- Si UMPP ≠ usage actuel : mentionner dans les hypothèses et limitations
- Chaque rapport amendé nécessite une nouvelle lettre ou un avenant

## Types de mandat → fin d'évaluation

| mandat_type | Fin d'évaluation typique |
|---|---|
| residentiel_standard | Hypothécaire / vente |
| succession | Succession / liquidation |
| litige | Litige judiciaire / TAQ |
| assurance | Valeur assurable |
| commercial_revenu | Hypothécaire commercial / investissement |
| expropriation | Expropriation / indemnisation |
```

- [ ] **Step 2: Créer `SKILL.md`**

```markdown
---
name: redaction-lettre-mandat
description: Rédige la lettre de mandat professionnelle conforme au Code de déontologie OEAQ §6.3 (10 éléments obligatoires)
type: redaction
agents:
  - mandat-intake
  - redaction
sources:
  - workflow-evaluateur-agree.md
---

# Skill — Rédaction de la lettre de mandat

## Rôle

Rédige la lettre de mandat (lettre d'engagement) conforme au Code de déontologie OEAQ.
Document obligatoire devant être remis au commanditaire avant l'inspection.

## Les 10 éléments obligatoires (§6.3)

| # | Élément | Requis si absent |
|---|---|---|
| 1 | Identification précise de la propriété | BLOCAGE |
| 2 | Identification du commanditaire | WARNING — utiliser [COMMANDITAIRE] |
| 3 | Type d'acte professionnel | BLOCAGE |
| 4 | Type de rapport | BLOCAGE |
| 5 | Fin d'évaluation | BLOCAGE |
| 6 | Date d'évaluation | BLOCAGE |
| 7 | Étendue de l'inspection | WARNING |
| 8 | Hypothèses et limitations préalables | WARNING |
| 9 | Honoraires et conditions | WARNING — [À CONFIRMER] acceptable V0 |
| 10 | Date de livraison + signatures | WARNING — [À CONFIRMER] acceptable V0 |

## Méthodologie

1. Lire `analysis.md` pour la doctrine complète
2. Extraire du dossier : dossier_id, type_bien, adresse, date_reference, mandat_type, format_rapport
3. Rédiger les 10 sections en Markdown, ton professionnel, juridiction Québec
4. Honoraires et date livraison : utiliser `[À CONFIRMER]` si non fournis
5. Commanditaire : utiliser `[COMMANDITAIRE]` si non identifié

## Règles critiques

- Honoraires jamais conditionnels à la valeur (violation déontologique OEAQ)
- Lettre précède l'inspection — document de départ, pas de validation
- Chaque mandat = une lettre distincte

## Checklist de conformité

- [ ] 10 éléments présents ou justifiés
- [ ] Ton professionnel, aucune valeur préjugée
- [ ] Juridiction Québec mentionnée
- [ ] Deux blocs de signature (évaluateur agréé + commanditaire)
```

- [ ] **Step 3: Vérifier les fichiers créés**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "
from engine.skills import discover_project_skills
skills = discover_project_skills()
names = [s.name for s in skills]
assert 'redaction-lettre-mandat' in names, f'Not found in {names}'
s = next(s for s in skills if s.name == 'redaction-lettre-mandat')
assert s.has_analysis, 'analysis.md manquant'
assert 'mandat-intake' in s.agents, f'agents={s.agents}'
print('OK redaction-lettre-mandat skill discoverable')
"
```

Expected: `OK redaction-lettre-mandat skill discoverable`

- [ ] **Step 4: Commit**

```bash
git add backend/skills/redaction-lettre-mandat/
git commit -m "feat(skills): add redaction-lettre-mandat skill (OEAQ §6.3)"
```

---

### Task 2: Créer le skill `analyse-approche-fta`

**Files:**
- Create: `backend/skills/analyse-approche-fta/analysis.md`
- Create: `backend/skills/analyse-approche-fta/SKILL.md`

**Security flag:** `none`

**Does NOT cover:** Calcul automatisé DCF (les calculs réels sont dans `calculs_approche_revenu.json`). Analyse de sensibilité (§9.8) — documentée mais non générée automatiquement en V0.

- [ ] **Step 1: Créer `analysis.md`**

```markdown
# Analyse — Approche par flux de trésorerie actualisés (FTA / DCF)

## Source doctrine
workflow-evaluateur-agree.md §9.7 — Approche — Flux de trésorerie actualisés (FTA / DCF)

## Quand utiliser le DCF

- Revenus non stabilisés : vacance élevée, baux expirant bientôt, loyers en escalade contractuelle
- Propriétés en redéveloppement ou repositionnement
- Portefeuilles commerciaux complexes (tours de bureaux, centres commerciaux)
- Mandats exigeant une analyse de sensibilité poussée
- Baux hors marché (above-market ou below-market leases)
- La capitalisation directe suppose des revenus stables — le DCF lève cette hypothèse

## Étape 1 — Définir la période de projection

```
Typiquement 5 à 10 ans selon le type de bien et la nature des baux :
  ├── Immeubles commerciaux avec baux long terme : 10 ans
  ├── Multilogements : 5–7 ans (revenus plus prévisibles)
  └── Propriétés en repositionnement : selon durée de la stratégie
```

## Étape 2 — Projeter les flux de trésorerie annuels

Pour chaque année de la période de projection :
```
  Revenus bruts potentiels (RBP)
  − Vacance et pertes sur créances
  = Revenus bruts effectifs (RBE)
  − Charges d'exploitation (taxes, assurances, entretien, gestion)
  = Revenu net d'exploitation (RNE)
```

Hypothèses de projection :
- Taux de croissance des revenus (par bail ou par marché)
- Taux de vacance normalisé
- Évolution des charges (inflation)

## Étape 3 — Calculer la valeur terminale

```
Valeur terminale = RNE(année N+1) ÷ Exit cap rate (taux de sortie)
```

Taux de sortie (exit cap rate) :
- Généralement légèrement supérieur au taux d'entrée (going-in cap rate)
- Reflète le vieillissement du bien
- Écart typique : 25–50 points de base au-dessus du taux d'entrée

## Étape 4 — Déterminer le taux d'actualisation

```
Composantes :
  ├── Taux sans risque (obligations gouvernementales 10 ans)
  ├── Prime de risque immobilier (liquidité, gestion, marché)
  ├── Prime de risque spécifique au bien (âge, localisation, qualité locataires)
  └── Prime d'illiquidité

Taux typiques Québec 2025 :
  ├── Multirésidentiel : 5,0 % – 6,5 %
  ├── Commercial/bureau : 6,0 % – 8,0 %
  └── Industriel : 5,5 % – 7,0 %
```

## Étape 5 — Actualiser tous les flux

```
VP d'un flux futur = Flux année N ÷ (1 + taux d'actualisation)^N

Valeur par FTA = Σ VP(RNE années 1 à N) + VP(valeur terminale)
```

## Exemple numérique (§9.7) — Immeuble commercial 5 ans

```
Taux d'actualisation : 7,0 %     Exit cap rate : 6,5 %

Année   RNE       Facteur VP (7%)   VP du flux
  1    100 000      0,9346           93 458
  2    103 000      0,8734           89 960
  3    106 090      0,8163           86 601
  4    109 273      0,7629           83 367
  5    112 551      0,7130           80 249

Valeur terminale = 112 551 × (1,02) ÷ 0,065 = 1 765 893
VP valeur terminale = 1 765 893 × 0,7130 = 1 259 082

VALEUR PAR FTA = 93 458 + 89 960 + 86 601 + 83 367 + 80 249 + 1 259 082
              = 1 692 717 $ → arrondi à 1 690 000 $
```

## Cas spéciaux : baux hors marché

### Bail sous le marché (below-market lease)
- Loyer réel < loyer du marché
- Valeur de continuation < valeur marchande stabilisée
- Méthode : DCF avec loyers réels années 1 à N, puis loyers marché années N+1 et suivantes

### Bail sur le marché (above-market lease)
- Loyer réel > loyer du marché
- Valeur de continuation > valeur marchande stabilisée
- Même approche DCF bipartite

## Règles critiques

- Le taux d'actualisation ≠ le taux de capitalisation
- Documenter TOUTES les hypothèses : taux de croissance, vacance, charges, taux d'actualisation, exit cap rate
- Analyse de sensibilité obligatoire dans les rapports commerciaux (§9.8)
- Arrondis cohérents avec la précision des données sources
```

- [ ] **Step 2: Créer `SKILL.md`**

```markdown
---
name: analyse-approche-fta
description: Applique l'approche par flux de trésorerie actualisés (FTA/DCF) pour immeubles revenus/commercial — §9.7 workflow OEAQ
type: analyse
agents:
  - valuation-draft
sources:
  - workflow-evaluateur-agree.md
---

# Skill — Analyse par flux de trésorerie actualisés (FTA / DCF)

## Rôle

Méthode de valorisation par actualisation des flux de trésorerie futurs. Complément
à l'approche revenu par capitalisation directe pour les revenus non stabilisés,
baux complexes et propriétés commerciales en repositionnement.

## Quand utiliser FTA vs capitalisation directe

| Situation | Capitalisation directe | FTA/DCF |
|---|---|---|
| Revenus stables et permanents | Préféré | Optionnel |
| Vacance élevée / baux expirant | Non adapté | Requis |
| Baux hors marché | Difficile | Requis |
| Repositionnement | Non adapté | Requis |
| Portefeuille commercial complexe | Insuffisant | Requis |

## Méthodologie (5 étapes)

1. **Période de projection** : 5–10 ans selon type de bien
2. **Flux annuels** : RBP − Vacance − Charges = RNE, projeté année par année
3. **Valeur terminale** : RNE(N+1) ÷ exit cap rate
4. **Taux d'actualisation** : taux sans risque + primes de risque immobilier
5. **Actualisation** : VP = Flux_N ÷ (1 + r)^N; Valeur = Σ VP(flux) + VP(terminale)

## Paramètres clés à documenter

- Période de projection (N années)
- Taux de croissance des revenus (% par an)
- Taux de vacance normalisé (%)
- Taux d'actualisation (%) + décomposition
- Exit cap rate (%) + justification par rapport au going-in cap rate

## Règles critiques

- Taux d'actualisation ≠ taux de capitalisation (concepts distincts)
- Toutes les hypothèses DOIVENT être documentées et défendables
- Analyse de sensibilité requise pour rapports commerciaux (§9.8)
- Arrondis : cohérents avec la précision des intrants

## Checklist

- [ ] Période de projection justifiée selon type de bien
- [ ] RNE projeté pour chaque année avec hypothèses explicites
- [ ] Valeur terminale calculée avec exit cap rate justifié
- [ ] Taux d'actualisation décomposé (sans risque + primes)
- [ ] VP calculée pour chaque flux + valeur terminale
- [ ] Valeur totale arrondie de manière cohérente
- [ ] Analyse de sensibilité si rapport commercial
```

- [ ] **Step 3: Vérifier les fichiers créés**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "
from engine.skills import discover_project_skills
skills = discover_project_skills()
names = [s.name for s in skills]
assert 'analyse-approche-fta' in names, f'Not found in {names}'
s = next(s for s in skills if s.name == 'analyse-approche-fta')
assert s.has_analysis, 'analysis.md manquant'
assert 'valuation-draft' in s.agents, f'agents={s.agents}'
print('OK analyse-approche-fta skill discoverable')
"
```

Expected: `OK analyse-approche-fta skill discoverable`

- [ ] **Step 4: Commit**

```bash
git add backend/skills/analyse-approche-fta/
git commit -m "feat(skills): add analyse-approche-fta skill (DCF §9.7)"
```

---

### Task 3: Créer `AGENTCONFIG-MANDAT-INTAKE-V0.yaml`

**Files:**
- Create: `backend/integration/AGENTCONFIG-MANDAT-INTAKE-V0.yaml`

**Security flag:** `none`

**Does NOT cover:** Appel LLM réel pour analyse conflits d'intérêts (V0 déterministe). Signature numérique.

- [ ] **Step 1: Créer le fichier**

```yaml
agent_id: mandat-intake
label: "Agent Mandat — Réception et formalisation du mandat"
model: gpt-4o-mini
temperature: 0.1
max_tokens: 2000
system_prompt: |
  Tu es un expert en formalisation de mandats d'évaluation immobilière au Québec,
  conforme au Code de déontologie de l'OEAQ et à la Norme de pratique professionnelle (NPP 2025).

  Ton rôle est de produire deux artefacts pour chaque dossier reçu :

  1. La lettre de mandat professionnelle (lettre_mandat.md) — document obligatoire §6.3
     du Code de déontologie, remis au commanditaire avant l'inspection.
     10 éléments obligatoires : identification propriété, commanditaire, type acte
     professionnel, type rapport, fin d'évaluation, date référence, étendue inspection,
     hypothèses et limitations, honoraires, date livraison et signatures.

  2. La vérification des conflits d'intérêts (conflit_interets.json) — première
     étape déontologique selon §6.2. En V0, cette vérification est déterministe
     (aucun conflit détecté par défaut).

  OBLIGATIONS :
  - Lettre de mandat en Markdown professionnel, juridiction Québec
  - Ton neutre et factuel — ne pas préjuger de la valeur
  - Honoraires toujours mentionnés comme [À CONFIRMER] si non fournis
  - Commanditaire : [COMMANDITAIRE] si non identifié dans le dossier

  RÈGLE CRITIQUE :
  - Les honoraires ne peuvent pas être conditionnels à la valeur obtenue
    (violation formelle du Code de déontologie OEAQ)
skills_allowed:
  - redaction-lettre-mandat
  - recherche-cadre-legal
  - recherche-normes-professionnelles
```

- [ ] **Step 2: Vérifier le fichier**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "
from engine.skills import load_agent_config_skills, load_agent_system_prompt
from pathlib import Path
p = Path('integration/AGENTCONFIG-MANDAT-INTAKE-V0.yaml')
assert p.exists(), 'fichier manquant'
skills = load_agent_config_skills(p)
assert 'redaction-lettre-mandat' in skills, f'skills={skills}'
prompt = load_agent_system_prompt(p)
assert 'mandat' in prompt.lower(), 'system_prompt vide'
print('OK AGENTCONFIG-MANDAT-INTAKE-V0.yaml valide')
"
```

Expected: `OK AGENTCONFIG-MANDAT-INTAKE-V0.yaml valide`

- [ ] **Step 3: Commit**

```bash
git add backend/integration/AGENTCONFIG-MANDAT-INTAKE-V0.yaml
git commit -m "feat(agents): add AGENTCONFIG-MANDAT-INTAKE-V0"
```

---

### Task 4: Mettre à jour `backend/engine/skills.py`

**Files:**
- Modify: `backend/engine/skills.py`

**Security flag:** `none`

**Does NOT cover:** Chargement dynamique de nouveaux agents (non prévu en V0).

- [ ] **Step 1: Écrire le test (failing)**

```python
# Dans backend/tests/test_pure.py, ajouter à la classe TestDefaultSkillsByAgent :

def test_mandat_intake_in_default_skills(self):
    from engine.skills import DEFAULT_SKILLS_BY_AGENT
    assert "mandat-intake" in DEFAULT_SKILLS_BY_AGENT
    skills = DEFAULT_SKILLS_BY_AGENT["mandat-intake"]
    assert "redaction-lettre-mandat" in skills

def test_fta_in_valuation_draft_skills(self):
    from engine.skills import DEFAULT_SKILLS_BY_AGENT
    assert "analyse-approche-fta" in DEFAULT_SKILLS_BY_AGENT["valuation-draft"]
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py::TestDefaultSkillsByAgent -x -q 2>&1
```

Expected: FAIL — `AssertionError` sur `mandat-intake` et/ou `analyse-approche-fta`

- [ ] **Step 3: Implémenter les changements dans `skills.py`**

Dans `DEFAULT_SKILLS_BY_AGENT`, ajouter `"mandat-intake"` AVANT `"data-facts"` :

```python
DEFAULT_SKILLS_BY_AGENT: dict[str, list[str]] = {
    "mandat-intake": [
        "redaction-lettre-mandat",
        "recherche-cadre-legal",
        "recherche-normes-professionnelles",
    ],
    "data-facts": [
        # ... inchangé
```

Et dans `"valuation-draft"`, ajouter `"analyse-approche-fta"` :

```python
    "valuation-draft": [
        "analyse-approche-comparaison",
        "analyse-approche-cout",
        "analyse-approche-fta",
        "analyse-approche-revenu",
        "analyse-reconciliation-valeur",
        "recherche-baux-revenus",
        "recherche-domaines-specialises",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
    ],
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py::TestDefaultSkillsByAgent -x -q 2>&1
```

Expected: PASS (3 tests : `test_amu_analyst_in_default_skills` + 2 nouveaux)

- [ ] **Step 5: Commit**

```bash
git add backend/engine/skills.py backend/tests/test_pure.py
git commit -m "feat(skills): add mandat-intake and analyse-approche-fta to DEFAULT_SKILLS_BY_AGENT"
```

---

### Task 5: Mettre à jour `backend/engine/runtime.py` (5 changements)

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** Appel LLM pour `conflit_interets.json` (déterministe V0). Logique `lettre_mandat.md` enrichie par le redaction agent (step 7 peut lire l'artefact mais ne le recrée pas).

- [ ] **Step 1: Écrire les tests (failing)**

```python
# Dans backend/tests/test_pure.py, ajouter la classe :

class TestMandatIntakeDeterministic:
    def test_conflit_interets_fields(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-MANDAT-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-12",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "conflit_interets.json", case, "BROUILLON", [], []
        )
        assert payload["dossier_id"] == "D-MANDAT-TEST"
        assert payload["step"] == "mandat-intake"
        assert payload["artifact"] == "conflit_interets.json"
        assert payload["conflit_detecte"] is False
        assert payload["verification_completee"] is True
        assert "commentaire" in payload

    def test_lettre_mandat_md_raw_md(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from engine.runtime import RuntimeEngine
        engine = RuntimeEngine()
        case = {
            "dossier_id": "D-MANDAT-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-12",
            "mandat_type": "residentiel_standard",
            "format_rapport": "abrege",
        }
        payload = engine._artifact_payload(
            "mandat-intake", "lettre_mandat.md", case, "BROUILLON", [], []
        )
        assert payload["step"] == "mandat-intake"
        assert "_raw_md" in payload
        assert "Lettre de mandat" in payload["_raw_md"] or "mandat" in payload["_raw_md"].lower()
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py::TestMandatIntakeDeterministic -x -q 2>&1
```

Expected: FAIL — `AssertionError` ou `KeyError` car `mandat-intake` non géré

- [ ] **Step 3a: `_LLM_TEXT_FIELD_BY_ARTIFACT` — ajouter `lettre_mandat.md`**

Dans `runtime.py`, après `"amu_analyse.md": "_raw_md",` :

```python
    "lettre_mandat.md": "_raw_md",
```

- [ ] **Step 3b: `REQUIRED_FIELDS_BY_ARTIFACT` — ajouter `conflit_interets.json`**

Dans `REQUIRED_FIELDS_BY_ARTIFACT`, ajouter après la clé `"umpp_conclusion.json"` :

```python
    "conflit_interets.json": ["dossier_id", "step", "artifact", "source_fixture", "conflit_detecte"],
```

- [ ] **Step 3c: `DEFAULT_STEPS` — insérer `mandat-intake` à l'index 0 et mettre à jour `redaction`**

Remplacer le début de `DEFAULT_STEPS` :

```python
DEFAULT_STEPS = [
    RuntimeStep("mandat-intake", ["dossier_input"], ["lettre_mandat.md", "conflit_interets.json"], _skills_for_agent("mandat-intake"), "AGENTCONFIG-MANDAT-INTAKE-V0.yaml"),
    RuntimeStep("data-facts", ["dossier_input", "documents_sources"], ["fiche_bien.json", "timeline_faits.json", "source_index.json"], _skills_for_agent("data-facts"), "AGENTCONFIG-DATA-FACTS-V0.yaml"),
    RuntimeStep("amu-analyst", ["fiche_bien.json", "source_index.json"], ["umpp_conclusion.json", "amu_analyse.md"], _skills_for_agent("amu-analyst"), "AGENTCONFIG-AMU-ANALYST-V0.yaml"),
    RuntimeStep("comps-market", ["fiche_bien.json", "umpp_conclusion.json", "source_index.json", "market_data_sources"], ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"], _skills_for_agent("comps-market"), "AGENTCONFIG-COMPS-MARKET-V0.yaml"),
    RuntimeStep("valuation-draft", ["comparables_proposes.json", "couts_reference", "revenus_depenses", "source_index.json"], ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "brouillon_valeur.md"], _skills_for_agent("valuation-draft"), "AGENTCONFIG-VALUATION-DRAFT-V0.yaml"),
    RuntimeStep("compliance-qa", ["calculs_approche_comparative.json", "calculs_approche_cout.json", "calculs_approche_revenu.json", "hypotheses_explicites.json", "source_index.json"], ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"], _skills_for_agent("compliance-qa"), "AGENTCONFIG-COMPLIANCE-QA-V0.yaml"),
    RuntimeStep("redaction", ["statut_sortie.json", "recommandations_corrections.md", "amu_analyse.md", "lettre_mandat.md", "source_index.json"], ["brouillon_rapport.md", "annexe_sources.md"], _skills_for_agent("redaction"), "AGENTCONFIG-REDACTION-V0.yaml"),
]
```

- [ ] **Step 3d: `_artifact_payload` — ajouter les blocs `mandat-intake`**

Dans la méthode `_artifact_payload`, après le bloc `if step == "amu-analyst" and artifact == "amu_analyse.md":` et avant le bloc de fin (`if artifact == "source_index.json":` ou similaire), ajouter :

```python
        if step == "mandat-intake" and artifact == "conflit_interets.json":
            payload.update({
                "conflit_detecte": False,
                "verification_completee": True,
                "commentaire": "Aucun conflit d'interets detecte — verification V0 deterministe.",
            })

        if step == "mandat-intake" and artifact == "lettre_mandat.md":
            type_bien = str(case.get("type_bien", "inconnu")).replace("_", " ")
            mandat_type = str(case.get("mandat_type", "residentiel_standard"))
            format_rapport = str(case.get("format_rapport", "abrege"))
            date_ref = case.get("date_reference", "—")
            dossier_id = case.get("dossier_id", "—")
            payload["_raw_md"] = (
                f"# Lettre de mandat\n\n"
                f"**Dossier :** {dossier_id}  \n"
                f"**Type de bien :** {type_bien}  \n"
                f"**Type de mandat :** {mandat_type}  \n"
                f"**Format du rapport :** {format_rapport}  \n"
                f"**Date de référence :** {date_ref}\n\n"
                f"## Identification du bien\n\n"
                f"Bien de type {type_bien} tel que décrit dans le dossier {dossier_id}.\n\n"
                f"## Type d'acte professionnel\n\n"
                f"Évaluation immobilière — rapport {format_rapport}.\n\n"
                f"## Fin d'évaluation\n\n"
                f"Mandat de type {mandat_type}.\n\n"
                f"## Honoraires et conditions\n\n"
                f"À confirmer selon entente avec le commanditaire.\n\n"
                f"## Signatures\n\n"
                f"_Évaluateur agréé (É.A.) — signature requise_  \n"
                f"_Commanditaire — signature requise_\n"
            )
```

- [ ] **Step 3e: `_build_enrichment_prompt` — ajouter le bloc `lettre_mandat.md`**

Dans `_build_enrichment_prompt`, avant le bloc `# Fallback générique` (dernières lignes), ajouter :

```python
    if artifact == "lettre_mandat.md":
        mandat_type = str(case.get("mandat_type", "residentiel_standard"))
        format_rapport = str(case.get("format_rapport", "abrege"))
        methodes = case.get("methodes_requises", [])
        return base + (
            f"MANDAT :\n"
            f"Type de bien : {type_bien} | Mandat : {mandat_type} | Format rapport : {format_rapport}\n"
            f"Methodes requises : {methodes}\n\n"
            "Redige la lettre de mandat professionnelle en Markdown conforme au Code de deontologie OEAQ. "
            "Structure obligatoire : identification du bien, identification du commanditaire (laisser [COMMANDITAIRE] si absent), "
            "type d'acte professionnel, type de rapport, fin d'evaluation, date de reference, "
            "etendue de l'inspection, hypotheses et limitations prealables, honoraires ([A CONFIRMER]), "
            "date de livraison prevue ([A CONFIRMER]), lignes de signature. "
            "Ton professionnel, juridiction Quebec, references deontologiques OEAQ."
        )
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py::TestMandatIntakeDeterministic -x -q 2>&1
```

Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/engine/runtime.py backend/tests/test_pure.py
git commit -m "feat(runtime): add mandat-intake step + lettre_mandat.md + conflit_interets.json"
```

---

### Task 6: Mettre à jour `PIPELINE-RUNTIME-ASTON-V0.yaml`

**Files:**
- Modify: `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml`

**Security flag:** `none`

**Does NOT cover:** Validation YAML formelle (le parser custom `load_steps_from_pipeline_yaml` suffit).

- [ ] **Step 1: Remplacer le contenu du fichier**

Remplacer la section `sequence:` entière :

```yaml
sequence:
  - step: 1
    agent_config: AGENTCONFIG-MANDAT-INTAKE-V0.yaml
    reads:
      - dossier_input
    writes:
      - lettre_mandat.md
      - conflit_interets.json

  - step: 2
    agent_config: AGENTCONFIG-DATA-FACTS-V0.yaml
    reads:
      - dossier_input
      - documents_sources
    writes:
      - fiche_bien.json
      - timeline_faits.json
      - source_index.json

  - step: 3
    agent_config: AGENTCONFIG-AMU-ANALYST-V0.yaml
    reads:
      - fiche_bien.json
      - source_index.json
    writes:
      - umpp_conclusion.json
      - amu_analyse.md

  - step: 4
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

  - step: 5
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

  - step: 6
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

  - step: 7
    agent_config: AGENTCONFIG-REDACTION-V0.yaml
    reads:
      - statut_sortie.json
      - recommandations_corrections.md
      - amu_analyse.md
      - lettre_mandat.md
      - source_index.json
    writes:
      - brouillon_rapport.md
      - annexe_sources.md
```

- [ ] **Step 2: Vérifier la cohérence YAML ↔ DEFAULT_STEPS**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "
from pathlib import Path
from engine.runtime import DEFAULT_STEPS, load_steps_from_pipeline_yaml
yaml_steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml'))
yaml_names = [s.name for s in yaml_steps]
default_names = [s.name for s in DEFAULT_STEPS]
assert yaml_names == default_names, f'MISMATCH: yaml={yaml_names} vs default={default_names}'
assert len(yaml_steps) == 7, f'Expected 7 steps, got {len(yaml_steps)}'
print('OK pipeline coherent, 7 steps:', yaml_names)
"
```

Expected: `OK pipeline coherent, 7 steps: ['mandat-intake', 'data-facts', 'amu-analyst', 'comps-market', 'valuation-draft', 'compliance-qa', 'redaction']`

- [ ] **Step 3: Commit**

```bash
git add backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml
git commit -m "feat(pipeline): renumber 1-7, insert mandat-intake step 1"
```

---

### Task 7: Mettre à jour `backend/api.py`

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** Exposition de `conflit_interets.json` dans l'interface (V0 = non affiché). Session invalidation si `mandat_type` change entre deux runs.

- [ ] **Step 1: Persistance `mandat_*` dans `start_runtime()`**

Dans `start_runtime()`, après le bloc `except Exception: pass  # classification facultative` et avant `session_dir = Path(session["session_dir"])`, ajouter :

```python
    # Persister les champs plan dans la session pour exposition frontend
    for _field in ("mandat_type", "format_rapport", "methodes_requises", "methode_preponderante"):
        if case.get(_field) is not None:
            session[_field] = case[_field]
    write_json(Path(session["session_dir"]) / "session.json", session)
```

- [ ] **Step 2: Exposer `mandat` dans `app_session_view()`**

Dans la dict retournée par `app_session_view()` (après la clé `"workflow":`), ajouter :

```python
        "mandat": {
            "mandat_type": session.get("mandat_type"),
            "format_rapport": session.get("format_rapport"),
            "methodes_requises": session.get("methodes_requises", []),
            "methode_preponderante": session.get("methode_preponderante"),
        } if session.get("mandat_type") else None,
```

- [ ] **Step 3: Vérifier syntaxe Python**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "import api; print('OK api.py imports clean')"
```

Expected: `OK api.py imports clean`

- [ ] **Step 4: Commit**

```bash
git add backend/api.py
git commit -m "feat(api): persist mandat_* fields in session, expose in app_session_view"
```

---

### Task 8: Mettre à jour le frontend

**Files:**
- Modify: `src/lib/runtime-api.ts`
- Modify: `src/components/panels/DossierPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Affichage du détail de `conflit_interets.json`. Édition des champs mandat (read-only V0). Internationalisation des labels.

- [ ] **Step 1: Ajouter `mandat` dans `AppState` (`runtime-api.ts`)**

Dans `src/lib/runtime-api.ts`, dans l'interface `AppState`, dans le bloc `active: null | {`, après `fact_chips: FactChip[]` et avant `comparables:` :

```typescript
    mandat: {
      mandat_type: string
      format_rapport: string
      methodes_requises: string[]
      methode_preponderante: string
    } | null
```

- [ ] **Step 2: Ajouter la fonction `fetchMandat` ou réutiliser `fetchAppState`**

Vérifier si `fetchAppState` existe déjà dans `runtime-api.ts`. Si oui, la réutiliser. Sinon, ajouter :

```typescript
export async function fetchAppState(dossierId: string): Promise<AppState> {
  return runtimeJson<AppState>(`/app/state?session_id=${encodeURIComponent(dossierId)}`)
}
```

*(Note : Chercher d'abord `fetchAppState` ou `fetchPropertyFacts` pour comprendre le pattern existant avant d'ajouter.)*

- [ ] **Step 3: Ajouter état `mandat` et fetch dans `DossierPanel.tsx`**

Dans `DossierPanel`, après `const [chips, setChips] = useState<FactChip[]>([])` :

```typescript
  const [mandat, setMandat] = useState<AppState['active'] extends null | infer T ? T extends null ? null : T['mandat'] : null>(null)
```

Simplification : utiliser le type inline :

```typescript
  type MandatData = {
    mandat_type: string
    format_rapport: string
    methodes_requises: string[]
    methode_preponderante: string
  } | null
  const [mandat, setMandat] = useState<MandatData>(null)
```

Dans le `useEffect` existant, ajouter le fetch de `mandat` :

```typescript
  useEffect(() => {
    if (!dossierId) return
    setLoading(true)
    Promise.all([
      fetchDocuments(dossierId),
      fetchPropertyFacts(dossierId),
      fetchAppState(dossierId),
    ]).then(([docs, facts, appState]) => {
      setDocuments(docs)
      setChips(facts)
      setMandat(appState.active?.mandat ?? null)
      setLoading(false)
    })
  }, [dossierId])
```

*(Si `fetchAppState` n'existe pas encore, l'ajouter dans `runtime-api.ts` — voir step 2.)*

- [ ] **Step 4: Rendre la section "Plan de mandat" dans `DossierPanel.tsx`**

Dans le bloc `return (...)`, après le bloc `{chips.length > 0 && (...)}` et avant `{documents.length > 0 && ...}` :

```tsx
        {mandat && (
          <AgentMessage agentName="Agent Mandat">
            {'Plan de mandat'}
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              <Chip label={`Mandat\u00a0: ${mandat.mandat_type.replace(/_/g, '\u00a0')}`} highlight />
              <Chip label={`Format\u00a0: ${mandat.format_rapport.replace(/_/g, '\u00a0')}`} highlight />
              {mandat.methodes_requises.map((m, i) => (
                <Chip key={i} label={m.replace(/_/g, '\u00a0')} />
              ))}
            </div>
          </AgentMessage>
        )}
```

- [ ] **Step 5: Vérifier TypeScript compile**

```bash
cd /c/Users/simon/eval-immo
npx tsc --noEmit 2>&1 | head -30
```

Expected: 0 erreurs TypeScript

- [ ] **Step 6: Commit**

```bash
git add src/lib/runtime-api.ts src/components/panels/DossierPanel.tsx
git commit -m "feat(frontend): add mandat section in DossierPanel (AppState.active.mandat)"
```

---

### Task 9: Tests finaux et vérification pipeline

**Files:**
- Modify: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** Tests d'intégration end-to-end (session complète). Tests frontend (hors scope V0).

- [ ] **Step 1: Mettre à jour `TestPipelineStepCount`**

Remplacer les tests existants dans `TestPipelineStepCount` :

```python
class TestPipelineStepCount:
    def test_default_steps_has_seven(self):
        from engine.runtime import DEFAULT_STEPS
        assert len(DEFAULT_STEPS) == 7

    def test_mandat_intake_at_index_zero(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[0].name == "mandat-intake"

    def test_data_facts_at_index_one(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[1].name == "data-facts"

    def test_amu_analyst_at_index_two(self):
        from engine.runtime import DEFAULT_STEPS
        assert DEFAULT_STEPS[2].name == "amu-analyst"

    def test_mandat_intake_writes_lettre_mandat(self):
        from engine.runtime import DEFAULT_STEPS
        step = DEFAULT_STEPS[0]
        assert "lettre_mandat.md" in step.writes
        assert "conflit_interets.json" in step.writes

    def test_redaction_reads_lettre_mandat(self):
        from engine.runtime import DEFAULT_STEPS
        redaction = DEFAULT_STEPS[6]
        assert redaction.name == "redaction"
        assert "lettre_mandat.md" in redaction.reads
```

- [ ] **Step 2: Vérifier que les nouveaux tests passent**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py::TestPipelineStepCount -x -q 2>&1
```

Expected: PASS (6 tests)

- [ ] **Step 3: Vérifier que tous les tests passent (≥66)**

```bash
cd /c/Users/simon/eval-immo/backend
python -m pytest tests/test_pure.py -q 2>&1
```

Expected: ≥66 tests passés (59 existants + 2 TestMandatIntakeDeterministic + 2 TestDefaultSkillsByAgent nouveaux + 6 TestPipelineStepCount mise à jour = au moins 66 green)

- [ ] **Step 4: Vérifier la cohérence YAML ↔ DEFAULT_STEPS une dernière fois**

```bash
cd /c/Users/simon/eval-immo/backend
python -c "
from pathlib import Path
from engine.runtime import DEFAULT_STEPS, load_steps_from_pipeline_yaml
yaml_steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml'))
assert [s.name for s in yaml_steps] == [s.name for s in DEFAULT_STEPS]
print('OK pipeline 7 steps coherent')
print('Steps:', [s.name for s in DEFAULT_STEPS])
"
```

Expected: `OK pipeline 7 steps coherent` + liste des 7 étapes

- [ ] **Step 5: Commit final**

```bash
git add backend/tests/test_pure.py
git commit -m "test: update TestPipelineStepCount to 7 steps, add Batch 4 assertions"
```

---

## Self-Review

**1. Spec coverage:**
- `redaction-lettre-mandat` skill → Task 1 ✓
- `analyse-approche-fta` skill → Task 2 ✓
- `AGENTCONFIG-MANDAT-INTAKE-V0.yaml` → Task 3 ✓
- `skills.py` (mandat-intake + fta in valuation-draft) → Task 4 ✓
- `runtime.py` 5 changements (5a LLM field, 5b REQUIRED_FIELDS, 5c DEFAULT_STEPS 6→7, 5d _artifact_payload, 5e _build_enrichment_prompt) → Task 5 ✓
- `PIPELINE-RUNTIME-ASTON-V0.yaml` 1→7 steps → Task 6 ✓
- `api.py` (mandat_* session persistence + app_session_view) → Task 7 ✓
- Frontend `runtime-api.ts` + `DossierPanel.tsx` → Task 8 ✓
- Tests (TestMandatIntakeDeterministic + TestPipelineStepCount mise à jour + TestDefaultSkillsByAgent mise à jour) → Tasks 4+5+9 ✓

**2. Placeholder scan:** Aucun TBD/TODO dans le plan. Tous les blocs de code sont complets.

**3. Type consistency:** `AppState['active']['mandat']` correspond au type défini dans `runtime-api.ts`. `MandatData` en local dans DossierPanel évite les imports circulaires.

**4. Scope-reduction scan:** Aucun "simple/basic/placeholder" non sanctionné. V0 déterministe pour `conflit_interets.json` est explicitement dans la spec.
