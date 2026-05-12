# Plan — Infrastructure agentique eval-immo

> Version : V3 → V4  
> Date de rédaction : 2026-05-12  
> Basé sur : `docs/workflow-evaluateur-agree.md`, état actuel `backend/`

---

## 1. État actuel — Ce qui existe déjà

### Pipeline runtime (déterministe)

```
dossier_input → [data-facts] → [comps-market] → [valuation-draft] → [compliance-qa] → [redaction]
```

| Agent actuel | Rôle | LLM actuel |
|---|---|---|
| `data-facts` | Fiche bien, timeline, index sources | ❌ déterministe |
| `comps-market` | Comparables proposés, justifications | ❌ déterministe |
| `valuation-draft` | Calculs 3 approches, hypothèses | ❌ déterministe |
| `compliance-qa` | Non-conformités, statut sortie | ❌ déterministe |
| `redaction` | Brouillon rapport.md, annexe sources | ✅ OpenAI (fallback déterministe) |

### Gaps critiques
- Aucun **AGENTCONFIG-*.yaml** n'existe (`integration/` vide sauf pipeline)
- Aucun **SKILL.md** n'existe (`skills/` vide)
- Aucun **connecteur données réelles** (tout tourne sur fixtures JSON)
- Aucun **routage par type de mandat** (même pipeline pour tous les cas)
- Aucun **agent OCR/documents** (PDF uploadés mais non parsés)
- Aucun **agent orchestrateur** (séquence linéaire fixe)

---

## 2. Architecture cible V4

```
                        ┌─────────────────────────────────────────────┐
                        │              ORCHESTRATEUR                   │
                        │  type_mandat × type_bien → plan d'exécution  │
                        └────────────┬────────────────────────────────┘
                                     │
          ┌──────────┬───────────────┼──────────────┬──────────┐
          ▼          ▼               ▼              ▼          ▼
    [ingestion]  [registre]    [data-facts]   [marché]  [valuation]
    OCR / parse  foncier +     faits, dates   comps     3 approches
    documents    rôle munic.   hypothèses     ajust.    réconciliation
          │          │               │              │          │
          └──────────┴───────────────┴──────────────┴──────────┘
                                     │
                        ┌────────────▼────────────┐
                        │      COMPLIANCE-QA       │
                        │  OEAQ norms + B00x rules │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │        REDACTION         │
                        │  brouillon rapport LLM   │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │      ADMIN/PACKAGE       │
                        │  PDF final, livraison    │
                        └─────────────────────────┘
```

### 8 agents V4

| Agent | Nouveau | Priorité |
|---|---|---|
| `orchestrateur` | ✅ nouveau | P0 |
| `ingestion-documents` | ✅ nouveau | P0 |
| `registre-donnees` | ✅ nouveau | P1 |
| `data-facts` | ♻️ étendre | P0 |
| `comps-market` | ♻️ étendre | P0 |
| `valuation-draft` | ♻️ étendre | P0 |
| `compliance-qa` | ♻️ étendre | P0 |
| `redaction` | ♻️ étendre | P1 |
| `admin-package` | ✅ nouveau | P2 |

---

## 3. Batch 1 — Fondations LLM (P0)

**Objectif** : Brancher OpenAI sur tous les agents existants. Passer de 1 seul appel LLM (redaction) à 5.

### 3.1 Créer les AGENTCONFIG YAML manquants

Chemin : `backend/integration/AGENTCONFIG-{NOM}-V0.yaml`

Chaque fichier suit ce schéma :

```yaml
agent_id: data-facts
label: "Agent Dossier"
model: gpt-4o-mini
temperature: 0.1
max_tokens: 2000
system_prompt: |
  Tu es un expert en évaluation immobilière québécoise (OEAQ).
  [prompt spécifique à l'agent]
skills_allowed:
  - analyse-extraction-faits
  - recherche-registre-cadastre
  - ...
```

**Fichiers à créer** (5) :
- `AGENTCONFIG-DATA-FACTS-V0.yaml`
- `AGENTCONFIG-COMPS-MARKET-V0.yaml`
- `AGENTCONFIG-VALUATION-DRAFT-V0.yaml`
- `AGENTCONFIG-COMPLIANCE-QA-V0.yaml`
- `AGENTCONFIG-REDACTION-V0.yaml`

### 3.2 Créer les SKILL.md

Chemin : `backend/skills/{nom-skill}/SKILL.md`

Format frontmatter :
```markdown
---
name: analyse-extraction-faits
description: >
  Extraire les faits structurés d'un document source (acte notarié,
  fiche cadastrale, contrat de bail) et les classer par catégorie.
type: analyse
agents:
  - data-facts
sources:
  - documents_sources
  - registre_foncier
---

## Procédure

[Contenu de la skill — instructions détaillées pour l'agent]
```

**Skills à créer** (13, couvrant tous les agents) :

| Skill | Agents |
|---|---|
| `analyse-extraction-faits` | data-facts |
| `recherche-registre-cadastre` | data-facts, comps-market |
| `recherche-baux-revenus` | data-facts, valuation-draft |
| `recherche-urbanisme-construction` | data-facts |
| `recherche-cadre-legal` | data-facts, compliance-qa |
| `analyse-selection-comparables` | comps-market |
| `recherche-marche-donnees` | comps-market |
| `analyse-approche-comparaison` | valuation-draft |
| `analyse-approche-cout` | valuation-draft |
| `analyse-approche-revenu` | valuation-draft |
| `analyse-reconciliation-valeur` | valuation-draft |
| `analyse-conformite` | compliance-qa |
| `recherche-normes-professionnelles` | compliance-qa, redaction |
| `redaction-rapport-evaluation` | redaction |

### 3.3 LLM par step dans `runtime.py`

Modifier `RuntimeEngine.run_case_data()` :
- Après `_artifact_payload()`, si `OPENAI_API_KEY` présent ET step a un system_prompt dans son AGENTCONFIG → appeler `_enrich_artifact_llm(step, payload, case)`
- `_enrich_artifact_llm()` appelle OpenAI, retourne payload enrichi
- Conserver fallback déterministe si pas de clé

**Fichiers modifiés** :
- `backend/engine/runtime.py` — ajouter `_enrich_artifact_llm()`, modifier `run_case_data()`
- `backend/engine/skills.py` — ajouter `load_agent_system_prompt(config_path)` qui lit `system_prompt:` du YAML

### 3.4 Tests

```
backend/tests/test_agentconfig_loading.py  — vérifie 5 YAML chargeables
backend/tests/test_skill_discovery.py      — vérifie 13+ SKILL.md découvertes
backend/tests/test_llm_enrichment.py       — mock OpenAI, vérifie enrichissement
```

**Vérification** :
```bash
cd backend && python -m pytest tests/ -k "agentconfig or skill or llm" -v
```

---

## 4. Batch 2 — Agent orchestrateur (P0)

**Objectif** : Remplacer la séquence linéaire fixe par un plan d'exécution adapté au type de mandat.

### 4.1 Classifier le dossier

Ajouter dans `api.py` un step initial (avant le pipeline) :

```python
def classify_dossier(case: dict) -> dict:
    """Retourne {type_mandat, type_bien, plan_agents, date_reference_required}"""
```

Logique de classification basée sur `docs/workflow-evaluateur-agree.md` section 2 :

| Champ dossier | Valeur | `type_mandat` |
|---|---|---|
| `mandat` | `hypothecaire` | `hypothecaire` |
| `mandat` | `succession` / `partage` | `successoral` |
| `mandat` | `expropriation` | `expropriation` |
| `mandat` | `contestation_role` | `municipal_lfi` |
| `mandat` | `fiscal_jvm` | `fiscal` |
| ... | ... | ... |

### 4.2 Plans d'exécution par mandat

Créer `backend/integration/PLANS-MANDATS-V0.yaml` :

```yaml
plans:
  hypothecaire:
    agents: [ingestion-documents, registre-donnees, data-facts, comps-market, valuation-draft, compliance-qa, redaction]
    date_reference: signature_pret
    rapport_type: forme_courte_hypothecaire
    compliance_rules: [B001, B002, B003, CONF002, CONF003]

  successoral:
    agents: [ingestion-documents, data-facts, comps-market, valuation-draft, compliance-qa, redaction]
    date_reference: deces_ou_donation
    rapport_type: forme_courte_succession
    compliance_rules: [B001, B002, JVM_FISCAL]

  municipal_lfi:
    agents: [ingestion-documents, registre-donnees, data-facts, comps-market, valuation-draft, compliance-qa, redaction]
    date_reference: date_reference_triennale  # ex: 2023-07-01 pour rôle 2025-2027
    rapport_type: rapport_opposition_lfi
    compliance_rules: [B001, B002, LFM_ART93, TRIENNALITE]
    special: date_reference_from_role_triennal

  expropriation:
    agents: [ingestion-documents, registre-donnees, data-facts, comps-market, valuation-draft, compliance-qa, redaction]
    date_reference: avis_expropriation
    rapport_type: rapport_expropriation
    compliance_rules: [B001, B002, AVANT_APRES_METHOD]
    special: methode_avant_apres_optionnelle

  fiscal:
    agents: [ingestion-documents, data-facts, comps-market, valuation-draft, compliance-qa, redaction]
    date_reference: date_transaction_ou_evaluation
    rapport_type: rapport_jvm_fiscal
    compliance_rules: [B001, JVM_LIR_ART69, ARC_JVM_DEF]
```

### 4.3 Nouvel agent `orchestrateur` dans `api.py`

```python
ASSISTANT_AGENT_PROFILES["orchestrateur"] = {
    "label": "Orchestrateur",
    "agent_config": "AGENTCONFIG-ORCHESTRATEUR-V0.yaml",
    "focus": "classification mandat, plan agents, routing, prochaines étapes",
}
```

L'orchestrateur répond aux questions du type :
- "Quel est le plan pour ce dossier ?"
- "Quel type de rapport dois-je produire ?"
- "Quelle date de référence ?"

### 4.4 Modifier `create_session` et `run_case_data`

```python
# api.py
def run_dossier(case: dict, session_dir: Path) -> dict:
    classification = classify_dossier(case)
    plan = load_plan_for_mandat(classification["type_mandat"])
    steps = build_steps_from_plan(plan)  # filtre DEFAULT_STEPS selon plan
    engine = RuntimeEngine(steps=steps)
    return engine.run_case_data(case, session_dir)
```

**Fichiers modifiés** :
- `backend/api.py` — `run_dossier()`, `classify_dossier()`, `load_plan_for_mandat()`
- `backend/integration/PLANS-MANDATS-V0.yaml` — nouveau
- `backend/integration/AGENTCONFIG-ORCHESTRATEUR-V0.yaml` — nouveau

---

## 5. Batch 3 — Agent ingestion-documents (P0)

**Objectif** : Transformer les PDFs uploadés en données structurées exploitables par le pipeline.

### 5.1 Nouvelle dépendance

```
# backend/requirements.txt
openai>=1.30.0
python-dotenv>=1.0.0
pymupdf>=1.24.0      # PyMuPDF — extraction texte PDF
pillow>=10.0.0       # images dans PDF
```

### 5.2 Nouveau module `backend/engine/ingestion.py`

```python
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """PyMuPDF → texte brut. Fallback vision API si texte < 100 chars (PDF scanné)."""

def parse_document_with_llm(text: str, doc_type: str) -> dict:
    """
    OpenAI → structured extraction.
    doc_type: acte_notarie | bail | fiche_mls | permis_construction | rapport_expertise
    Retourne: {type, date, parties, adresse, surface, montant, clauses_speciales, ...}
    """

def classify_document_type(text: str) -> str:
    """Heuristique + LLM pour détecter le type de document."""
```

### 5.3 Nouvel artifact : `documents_parsed.json`

```json
{
  "dossier_id": "...",
  "step": "ingestion-documents",
  "artifact": "documents_parsed.json",
  "documents": [
    {
      "doc_id": "doc_001",
      "filename": "acte_vente_2024.pdf",
      "type": "acte_notarie",
      "date": "2024-03-15",
      "extracted_fields": {
        "adresse": "123 rue Principale, Montréal",
        "prix_vente": 485000,
        "superficie_terrain": 320,
        "superficie_batiment": 145,
        "parties": {"vendeur": "...", "acheteur": "..."}
      },
      "confidence": 0.92,
      "raw_text_chars": 4521
    }
  ]
}
```

### 5.4 Intégration dans le pipeline

Ajouter `ingestion-documents` comme step 0 dans `PIPELINE-RUNTIME-ASTON-V0.yaml` :

```yaml
  - step: 0
    agent_config: AGENTCONFIG-INGESTION-DOCUMENTS-V0.yaml
    reads:
      - documents_binaires
    writes:
      - documents_parsed.json
      - source_index.json
```

Modifier `data-facts` pour lire `documents_parsed.json` en priorité sur `documents_sources`.

**Fichiers modifiés/créés** :
- `backend/engine/ingestion.py` — nouveau
- `backend/requirements.txt` — ajouter pymupdf, pillow
- `backend/integration/AGENTCONFIG-INGESTION-DOCUMENTS-V0.yaml` — nouveau
- `backend/integration/PIPELINE-RUNTIME-ASTON-V0.yaml` — ajouter step 0

---

## 6. Batch 4 — Agent registre-donnees (P1)

**Objectif** : Connecter aux sources publiques pour enrichir automatiquement les faits.

### 6.1 Sources de données prioritaires

| Source | Données | Accès |
|---|---|---|
| Registre foncier Québec | Propriétaire, hypothèques, droits réels | Web scraping / API MRNF |
| Rôle municipal (portails) | Valeur réelle, description, zonage | Scraping portail villes |
| BDIMMO / DLC | Ventes comparables résidentielles | Accord commercial |
| Centris | Inscriptions actives, historique prix | API partenaire |
| GESTIM Plus | Ventes tertiaires, revenus | Accord commercial |
| Répertoire des évaluateurs (OEAQ) | Vérification praticien | Web public |

### 6.2 Nouveau module `backend/engine/registre.py`

```python
class RegistreConnector:
    """Abstraction multi-source avec cache Redis optionnel."""

    def fetch_foncier(self, matricule: str) -> dict:
        """Registre foncier → {proprietaire, hypotheques, servitudes, droits}"""

    def fetch_role_municipal(self, adresse: str, ville: str) -> dict:
        """Portail municipal → {valeur_reelle, date_depot, description_physique}"""

    def search_ventes_comparables(self, params: ComparableSearchParams) -> list[dict]:
        """DLC/Centris → ventes comparables avec filtres (rayon, date, type_bien)"""

    def fetch_zonage(self, adresse: str) -> dict:
        """PAFIO / portail ville → {zonage, usages_permis, COS, hauteur_max}"""
```

### 6.3 Nouvel artifact : `registre_donnees.json`

```json
{
  "dossier_id": "...",
  "step": "registre-donnees",
  "artifact": "registre_donnees.json",
  "matricule": "4266-12-3456-7-000",
  "adresse_normalisee": "123, rue Principale, Montréal (QC) H1A 1A1",
  "foncier": {
    "proprietaire_actuel": "...",
    "date_acte": "2019-06-12",
    "hypotheques": [],
    "servitudes": ["servitude_passage_cour_arriere"]
  },
  "role_municipal": {
    "valeur_reelle": 425000,
    "annee_role": 2024,
    "description": "Maison 2 étages, 6 pièces",
    "superficie_terrain_m2": 320
  },
  "ventes_recentes_secteur": [...],
  "source": "registre_foncier_qc + ville_montreal",
  "fetched_at": "2026-05-12T14:32:00Z"
}
```

### 6.4 Variables d'environnement requises

```
# Nouvelles dans Railway + .env local
REGISTRE_FONCIER_API_KEY=...    # MRNF si disponible
DLC_API_KEY=...                 # Données du marché résidentiel
CENTRIS_API_KEY=...             # Inscriptions et ventes MLS/Centris
REDIS_URL=...                   # Cache optionnel pour données foncières
```

**Fichiers créés** :
- `backend/engine/registre.py`
- `backend/integration/AGENTCONFIG-REGISTRE-DONNEES-V0.yaml`

---

## 7. Batch 5 — Enrichissement agents existants (P0)

### 7.1 `comps-market` — Ajustements réels

Actuellement : sélection de comparables sans ajustements calculés.  
Cible : ajustements par paire (terrain, surface, âge, équipements, localisation).

**Modifier `engine/tools.py`** — `search_comparables()` :
```python
def calculate_adjustments(subject: dict, comparable: dict, market_data: dict) -> dict:
    """
    Retourne liste d'ajustements avec source_id pour chaque ligne.
    Applique grilles AMU (Ajustements selon données de Marché Uniformisées).
    """
```

Nouvel artifact : `grille_ajustements.json` (step comps-market, writes)

### 7.2 `valuation-draft` — Approches réelles

**Approche revenu (capitalisation directe)** :
```python
def calculate_revenu_approach(case: dict) -> dict:
    # RBE → RNE → TGA → valeur
    # TGA depuis données DLC secteur (actuellement proxy 0)
    revenus = case.get("revenus_annuels", {})
    depenses = case.get("depenses_annuels", {})
    tga = fetch_tga_from_market(case["zone"], case["type_bien"])  # nouveau
    rne = revenus["brut"] - depenses["total"]
    return {"value": rne / tga, "tga": tga, "rne": rne}
```

**Approche coût (remplacement)** :
```python
def calculate_cout_approach(case: dict) -> dict:
    # valeur_terrain + coût_reconstruction - dépréciation
    # Coûts Marshall & Swift / Altus par type construction + région
    cout_pied_carre = fetch_construction_cost(case["type_construction"], case["region"])
    ...
```

### 7.3 `compliance-qa` — Règles OEAQ complètes

Ajouter dans `runtime.py` les règles manquantes selon `workflow-evaluateur-agree.md` :

| Code | Règle | Section workflow |
|---|---|---|
| `OEAQ001` | Date référence ≤ date rapport | §3.2 |
| `OEAQ002` | Minimum 3 comparables résidentiels | §7.3 |
| `OEAQ003` | Superficie en m² (unité standardisée) | §4.1 |
| `OEAQ004` | JVM fiscale ≠ valeur marchande ordinaire si mandat fiscal | §12 |
| `OEAQ005` | Décote indivision documentée si condo indivise | §5.3 |
| `OEAQ006` | Méthode avant-après si expropriation partielle | §10.2 |
| `LFM001` | Date référence = date triennale rôle si contestation | §11.1 |
| `ARC001` | JVM définie selon art. 69(1) LIR si don bienfaisance | §12.4 |

---

## 8. Batch 6 — Frontend : UI agents (P1)

**Objectif** : Visualiser l'état de chaque agent en temps réel.

### 8.1 État agent dans `AppState`

`src/lib/runtime-api.ts` — type `AppState` déjà a `assistant.agents` :
```typescript
agents: Array<{
  agent: string    // "data-facts"
  label: string    // "Agent Dossier"
  status: string   // "idle" | "running" | "done" | "blocked"
  focus: string    // description de ce que l'agent fait
}>
```

Ajouter :
```typescript
progress?: {
  current_step: number       // 2
  total_steps: number        // 7
  current_artifact?: string  // "comparables_proposes.json"
  started_at?: string
}
artifacts?: Array<{
  name: string
  step: string
  written_at: string
  preview?: string  // premiers 200 chars si markdown
}>
```

### 8.2 Nouveau composant `AgentPipelineView`

Fichier : `src/components/AgentPipelineView.tsx`

```
┌─────────────────────────────────────────────────────┐
│  Pipeline d'évaluation                              │
│                                                     │
│  ✅ Ingestion       → documents_parsed.json         │
│  ✅ Registre        → registre_donnees.json         │
│  ✅ Faits           → fiche_bien.json               │
│  🔄 Comparables     → comparables_proposes.json...  │
│  ⏳ Valuation       en attente                      │
│  ⏳ Conformité      en attente                      │
│  ⏳ Rédaction       en attente                      │
│                                                     │
│  [Voir artefact]  [Chat avec agent]                 │
└─────────────────────────────────────────────────────┘
```

### 8.3 Polling SSE ou polling simple

Option A — **Polling simple** (30s) : appel `/api/runtime/status?session_id=X`  
Option B — **SSE** : endpoint `/stream?session_id=X` déjà défini dans `api.py`

Recommandation : commencer avec polling (option A), migrer vers SSE après MVP.

**Fichiers créés/modifiés** :
- `src/components/AgentPipelineView.tsx` — nouveau
- `src/lib/runtime-api.ts` — enrichir types `AppState`
- `src/app/dossier/[id]/page.tsx` — intégrer `AgentPipelineView`

---

## 9. Batch 7 — Agent admin-package (P2)

**Objectif** : Finaliser le dossier, générer le PDF certifiable, notifier le client.

### 9.1 Fonctions

1. **Validation finale** — l'évaluateur signe électroniquement (`POST /review`)
2. **Génération PDF** — rapport.md → PDF avec en-tête OEAQ, signature, cachet
3. **Package livrable** — PDF + annexes + sources → ZIP chiffré
4. **Notification** — email client avec lien sécurisé (TTL 48h)

### 9.2 Dépendances

```
# backend/requirements.txt
weasyprint>=62.0    # HTML/CSS → PDF (ou reportlab selon complexité)
```

### 9.3 Nouvel endpoint `POST /package`

```python
# api.py
def handle_package(session_id: str, evaluator_signature: dict) -> dict:
    """
    1. Charge brouillon_rapport.md
    2. Ajoute signature évaluateur
    3. Génère PDF avec entête OEAQ
    4. Crée ZIP: rapport.pdf + annexe_sources.md + registre_donnees.json
    5. Upload Supabase storage bucket dossier-documents
    6. Retourne {package_url, expires_at, checksum_sha256}
    """
```

---

## 10. Ordre d'implémentation recommandé

```
Semaine 1 — Batch 1 : AGENTCONFIG YAMLs + SKILL.md + LLM par step
Semaine 2 — Batch 2 : Orchestrateur + classification mandats
Semaine 3 — Batch 3 : Ingestion documents (OCR + LLM extraction)
Semaine 4 — Batch 4 : Connecteur registre (au moins rôle municipal)
Semaine 5 — Batch 5 : Enrichissement comps + approche revenu réelle
Semaine 6 — Batch 6 : Frontend pipeline view
Semaine 7 — Batch 7 : Package PDF
```

---

## 11. Contrats d'interface entre agents

Chaque agent doit respecter le contrat :

```
INPUT  : artifact précédent (JSON) + case.json + session_id
OUTPUT : artifact JSON avec {dossier_id, step, artifact, source_ids[], confidence}
ERREUR : artifact JSON avec {error: true, blocking_failures: [...]}
```

Règle absolue (déjà dans `runtime.py`) :
- Tout comparable doit avoir `source_id`
- Tout ajustement sensible (≥ 25 000 $) doit avoir `validation_humaine: true`
- Tout artifact doit avoir `dossier_id` + `step` + `artifact`

---

## 12. Vérification par batch

### Batch 1
```bash
cd backend
python -c "from engine.skills import discover_project_skills; print(len(discover_project_skills()), 'skills')"
python -c "from engine.runtime import load_steps_from_pipeline_yaml; from pathlib import Path; steps = load_steps_from_pipeline_yaml(Path('integration/PIPELINE-RUNTIME-ASTON-V0.yaml')); print('OK', len(steps), 'steps')"
python -m pytest tests/ -v
```

### Batch 2
```bash
python -c "from api import classify_dossier; r = classify_dossier({'mandat': 'hypothecaire', 'type_bien': 'unifamiliale'}); print(r)"
```

### Batch 3
```bash
python -c "from engine.ingestion import extract_text_from_pdf; print('OK')"
```

### Batch 4
```bash
python -c "from engine.registre import RegistreConnector; r = RegistreConnector(); print('OK')"
```

---

## 13. Variables d'environnement récapitulatif

| Variable | Existante | Batch | Usage |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | B1 | LLM agents |
| `OPENAI_MODEL` | ✅ | B1 | Modèle (défaut gpt-4o-mini) |
| `RUNTIME_API_TOKEN` | ✅ | — | Auth BFF |
| `SESSIONS_DIR` | ✅ | — | Volume Railway |
| `REGISTRE_FONCIER_API_KEY` | ❌ | B4 | MRNF registre |
| `DLC_API_KEY` | ❌ | B4 | Comparables résidentiels |
| `CENTRIS_API_KEY` | ❌ | B4 | MLS/Centris |
| `REDIS_URL` | ❌ | B4 | Cache données foncières |
| `SMTP_HOST` / `SMTP_API_KEY` | ❌ | B7 | Notifications email |
