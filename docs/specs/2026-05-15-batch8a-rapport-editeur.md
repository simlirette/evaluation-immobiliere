# Batch 8a — Rapport éditeur

## Scope

Permettre à l'évaluateur agréé de lire, modifier et sauvegarder le brouillon de rapport produit par le pipeline, depuis l'interface eval-immo. Le pipeline génère `brouillon_rapport.md` via LLM ou template déterministe ; ce batch le rend visible et éditable avec un éditeur riche (TipTap).

**In scope :**
- Afficher `report.preview` (contenu `brouillon_rapport.md`) dans le split view de `RapportDoc`
- Éditeur TipTap WYSIWYG : gras, italique, titres, listes, tableaux
- Sauvegarde du rapport édité → écrase le fichier session côté backend
- Régénérer le rapport : "Forme abrégée" (défaut) / "Forme complète" via bouton
- Améliorer le prompt LLM : inclure commanditaire, mandat, comparables complets, conformité, hypothèses ; `max_tokens` 2000 → 4000 ; system prompt aligné sur CUSPAP
- Format toggle : deux system prompts distincts (`ABREGE` 5-6 pages / `COMPLET` 15 sections CUSPAP)

**Non-goals :**
- Historique des versions Supabase (Batch 8b)
- Export Word (.docx) / PDF (Batch 8b)
- Pipeline live view / polling (Batch 9)
- E-signature numérique
- Diff / track changes entre versions

---

## Architecture

### Flux de données

```
AppState.active.report.preview  (markdown, max 16KB)
  └─ RapportPanel.state.reportText: string
       └─ RapportDoc props: reportText
            └─ if reportText → RapportEditor (TipTap)
               else          → structured view fallback (existant)
                    └─ import: marked(reportText) → HTML → tiptap.setContent(html)
                    └─ édition utilisateur
                    └─ save: tiptap.getHTML() → turndown() → saveRapport(sessionId, md)
                                 → POST /app/report { session_id, content }
                    └─ "Générer forme complète" → generateRapport(sessionId, 'complet')
                                 → POST /app/report/generate { session_id, format }
                                 → LLM call → new md → tiptap.setContent(new html)
```

### Backend : prompt amélioré

`_build_rapport_prompt_v2(case, format, valuation_values, status, blocking, warnings)` inclut :

```
FORMAT: {format} — {'Rapport abrégé (formulaire)' | 'Rapport narratif complet 15 sections'}
DOSSIER: {dossier_id}
COMMANDITAIRE: {commanditaire.nom} — {commanditaire.organisation}
FIN ÉVALUATION: {commanditaire.fin_evaluation}
TYPE MANDAT: {mandat.mandat_type}
DATE RÉFÉRENCE: {date_reference}

IDENTIFICATION:
- Adresse: {adresse}
- Type de bien: {type_bien}
- Zone / secteur: {zone}
- Surface habitable: {surface.value} {surface.unit}
- Surface terrain: {terrain} m²
- Année construction: {annee_construction}
- Nb logements: {nb_logements}
- Usage: {usage}

APPROCHES DE VALEUR:
- Approche comparative: {approche_comparative}
- Approche par le coût: {approche_cout}
- Approche par le revenu: {approche_revenu}
- Valeur réconciliée: {conclusion_value}

COMPARABLES RETENUS ({n}):
| # | Source | Adresse | Prix vente | Date | Score |
|---|--------|---------|------------|------|-------|
{comp_rows}

STATUT CONFORMITÉ: {status}
BLOCAGES ({n}): {blocking_list}
AVERTISSEMENTS ({n}): {warnings_list}

HYPOTHÈSES EXPLICITES: {hypotheses}
```

Deux system prompts distincts :
- `_RAPPORT_SYSTEM_PROMPT_ABREGE` : 6 sections, formulaire, tous les 16 éléments CUSPAP obligatoires
- `_RAPPORT_SYSTEM_PROMPT_COMPLET` : 15 sections narratives complètes, lettre de transmission, attestation

### Nouveaux endpoints backend

```python
# POST /app/report
# Body: { "session_id": "...", "content": "..." }
# Écrase artifacts/{dossier_id}/redaction.brouillon_rapport.md
# Returns: { "ok": true }

# POST /app/report/generate
# Body: { "session_id": "...", "format": "abrege" | "complet" }
# Régénère via LLM (ou fallback déterministe si pas de clé)
# Sauvegarde le résultat + retourne le texte
# Returns: { "ok": true, "content": "..." }
```

---

## Modifications fichiers

| Fichier | Type | Description |
|---------|------|-------------|
| `backend/engine/runtime.py` | Modify | `_build_rapport_prompt_v2`, `_RAPPORT_SYSTEM_PROMPT_ABREGE`, `_RAPPORT_SYSTEM_PROMPT_COMPLET`, `_RAPPORT_MAX_TOKENS` 2000→4000, `generate_brouillon_rapport(format='abrege')` |
| `backend/api.py` | Modify | `app_save_rapport()`, `app_generate_rapport()`, routage `/app/report` et `/app/report/generate` |
| `backend/tests/test_pure.py` | Modify | 4 nouvelles classes de test (voir section Tests) |
| `src/lib/runtime-api.ts` | Modify | `saveRapport(sessionId, content)`, `generateRapport(sessionId, format)` |
| `src/components/panels/RapportPanel.tsx` | Modify | Ajouter `reportText` à `RapportState`, handlers `handleSaveReport`, `handleGenerateReport` |
| `src/components/shared/RapportDoc.tsx` | Modify | Prop `reportText: string`, if reportText → `<RapportEditor>` |
| `src/components/shared/RapportEditor.tsx` | Create | TipTap editor + toolbar + boutons save/generate |
| `package.json` | Modify | Ajouter dépendances TipTap + marked + turndown |

**Aucun changement :** `runtime.py` (structure pipeline), `tools.py`, YAML pipeline, Supabase schemas.

---

## Dépendances npm (nouvelles)

```json
"@tiptap/react": "^2.10",
"@tiptap/starter-kit": "^2.10",
"@tiptap/extension-table": "^2.10",
"@tiptap/extension-table-row": "^2.10",
"@tiptap/extension-table-cell": "^2.10",
"@tiptap/extension-table-header": "^2.10",
"marked": "^12.0",
"turndown": "^7.2",
"turndown-plugin-gfm": "^1.0.2"
```

Dev :
```json
"@types/turndown": "^5.0"
```

---

## UX — RapportEditor

```
┌─────────────────────────────────────────────────────┐
│ [B] [I] [H1] [H2] [¶] [table] │ [Sauvegarder ✓]   │  ← toolbar
│─────────────────────────────────────────────────────│
│ BROUILLON DE RAPPORT D'ÉVALUATION                   │
│                                                     │
│ > ⚠ BROUILLON NON CERTIFIÉ — validation É.A. requis│
│                                                     │
│ ## 1. Identification du bien                        │
│ | Dossier | D-PILOTE-RES-001 |                     │
│ | Adresse | 123, rue Exemple |                     │
│ ...                                                 │
│                                                     │
│ ## 2. Conclusion de valeur...                       │
│ [contenu WYSIWYG éditable]                          │
│                                                     │
│─────────────────────────────────────────────────────│
│ [Régénérer — Forme abrégée]  [Forme complète →]    │  ← footer
└─────────────────────────────────────────────────────┘
```

- État `isEdited`: true dès première modification → bouton Sauvegarder s'active
- `isSaving`: spinner pendant POST
- Après save réussi : toast "Rapport sauvegardé" (2s) + `isEdited` reset
- "Forme complète" → confirm dialog "La régénération remplacera le contenu actuel. Continuer ?" → génération LLM

---

## Tests

| Classe | Vérifie |
|--------|---------|
| `TestBuildRapportPromptV2_IncludesCommanditaire` | commanditaire.nom présent dans prompt |
| `TestBuildRapportPromptV2_FormatAbrege` | "Rapport abrégé" dans prompt si format='abrege' |
| `TestBuildRapportPromptV2_FormatComplet` | "narratif complet" dans prompt si format='complet' |
| `TestSaveRapport_WritesFile` | POST /app/report → fichier session mis à jour |
| `TestGenerateRapport_FallbackNoCle` | POST /app/report/generate sans OPENAI_API_KEY → deterministic fallback retourné |

---

## Failure modes et mitigations

| Mode | Sévérité | Mitigation |
|------|----------|-----------|
| Round-trip markdown (MD→HTML→TipTap→HTML→MD) perd du formatage | Minor | Markdown standard survit ; cas limites (HTML inline custom) : non-goal V0 |
| Prompt trop long (contexte GPT) | Minor | Comparables limités à 5, AMU à 500 chars dans `_build_rapport_prompt_v2` |
| `report.preview` vide (session sans LLM) | Non-issue | `_generate_rapport_deterministic` toujours disponible en fallback |
| Save sur session inexistante | Minor | Backend valide session avant écriture → 404 clair |
| TipTap table extension conflit avec table markdown | Minor | Utiliser `turndown-plugin-gfm` pour GFM tables round-trip |

---

## Dépendances

- `report.preview` déjà dans AppState (limite 16KB — suffisant pour forme abrégée ~3000 mots)
- `RapportPanel` déjà câblé sur AppState — ajouter `reportText` au state local
- Pipeline runtime inchangé
