# Batch 7 — Saisie manuelle des comparables

## Scope

Permettre à l'évaluateur agréé de saisir manuellement ses comparables candidats (Phase 2 OEAQ) avant le lancement du pipeline. Le `comps-market` agent (step 4) sélectionne les meilleurs 3–5 et rédige les justifications (Phase 4 OEAQ).

**In scope :**
- Step 3 dans le wizard `DossierPanel.NewDossierForm` — grille de saisie des comparables
- Passage des comparables frontend → backend via POST `/app/demo`
- Injection dans `case["comparables"]` avant exécution du pipeline
- Warning doux si 0 comparables avant launch (CONF002)

**Non-goals :**
- Calcul automatique de distance (pas de coordonnées GPS en V0)
- Persistance Supabase des comparables input (case dict uniquement)
- Édition des comparables après lancement du pipeline
- Export / impression de la grille
- Fetch automatique Centris ou autre source (V0 = saisie manuelle)

---

## Architecture

### Flux de données

```
DossierPanel (step 3)
  └─ ComparableInput[] state
       └─ createRuntimeDossier({ ..., comparables: [...] })
            └─ POST /app/demo { comparables: [...] }
                 └─ app_start_demo() → runtime_body["comparables"]
                      └─ start_runtime() → case["comparables"] = mapped_list
                           └─ runtime.py:_artifact_payload("comps-market", "comparables_proposes.json")
                                └─ search_comparables(case["comparables"], max_items=5, ...)
```

### Données

**Type frontend `ComparableInput` (nouveau dans `src/types/index.ts`) :**

```ts
export interface ComparableInput {
  id: string                   // UUID client-side (React key)
  adresse: string
  date_vente: string           // ISO: "2024-06-15"
  prix_vente: number
  source_id: string            // ex: "CENTRIS-12345678" | "RF-2024-ABC"
  source_type: 'mls_centris' | 'registre_foncier' | 'dlc' | 'autre'
  type_propriete: string
  surface_hab: number | null   // m²
  surface_terrain: number | null  // m²
  annee_construction: number | null
  nb_logements: number | null
  conditions_vente: 'normale' | 'liee' | 'autre'
  notes: string
}
```

**Mapping backend → format `case["comparables"]` (dans `api.py:start_runtime()`) :**

```python
def _map_comparable_input(row: dict) -> dict:
    surface_hab = row.get("surface_hab")
    return {
        "comparable_id": str(row.get("source_id") or row.get("id") or ""),
        "adresse": str(row.get("adresse") or ""),
        "date_vente": str(row.get("date_vente") or ""),
        "prix_vente": float(row.get("prix_vente") or 0),
        "source_id": str(row.get("source_id") or ""),
        "source_type": str(row.get("source_type") or "autre"),
        "surface": {"value": float(surface_hab), "unit": "m²"} if surface_hab else {},
        "surface_terrain": float(row["surface_terrain"]) if row.get("surface_terrain") else None,
        "annee_construction": int(row["annee_construction"]) if row.get("annee_construction") else None,
        "nb_logements": int(row["nb_logements"]) if row.get("nb_logements") else None,
        "conditions_vente": str(row.get("conditions_vente") or "normale"),
        "notes": str(row.get("notes") or ""),
        "confidence": 0.80,
    }
```

**Règle de merge dans `start_runtime()` :** les comparables du body ont priorité sur les comparables fixture si fournis (`body_comps or case.get("comparables", [])`).

---

## Modifications fichiers

| Fichier | Type | Description |
|---------|------|-------------|
| `src/types/index.ts` | Modify | Ajouter `ComparableInput` |
| `src/lib/runtime-api.ts` | Modify | Étendre `CreateRuntimeDossierInput` + passer comparables dans POST |
| `src/components/panels/DossierPanel.tsx` | Modify | Ajouter step 3 + `ComparableInputCard` inline |
| `backend/api.py` | Modify | `app_start_demo()` + `start_runtime()` — injection comparables |
| `backend/tests/test_pure.py` | Modify | Tests injection comparables |

**Aucun changement :** `runtime.py`, `tools.py`, PIPELINE YAML, Supabase schemas.

---

## UX — Step 3 (comparables)

Le wizard existant 2 étapes → 3 étapes :
- Step 1 : Bien sujet (address, type, secteur)
- Step 2 : Commanditaire (nom, org, fin_évaluation)
- **Step 3 : Comparables candidats** (nouveau)

**Step 3 layout :**
```
┌─────────────────────────────────────────────────────┐
│ Comparables candidats                               │
│ Identifiez 5 à 10 ventes similaires (Phase 2 OEAQ) │
│                                                     │
│ [card comparable 1 — collapsed: adresse + prix]     │
│ [card comparable 2 — collapsed]                     │
│ ...                                                 │
│                                                     │
│ [ + Ajouter un comparable ]                         │
│                                                     │
│ ⚠ 0 comparable — le rapport sera A_REVOIR (CONF002) │  ← warning doux si vide
│                                                     │
│ [ ← Retour ]           [ Lancer l'évaluation → ]   │
└─────────────────────────────────────────────────────┘
```

**Chaque card comparable :**
- **Collapsed** : `{adresse} · {prix_vente}$`
- **Expanded** (11 champs OEAQ) :
  - Adresse (texte)
  - Date de vente (date input)
  - Prix de vente ($, numérique)
  - Source ID (texte — ex: "CENTRIS-12345678")
  - Source type (select: Centris/MLS | Registre foncier | DLC | Autre)
  - Type de propriété (texte)
  - Superficie habitable m² (numérique)
  - Superficie terrain m² (numérique)
  - Année de construction (numérique)
  - Nb logements (numérique, optionnel)
  - Conditions de vente (select: normale | liée | autre)
  - Notes (texte libre)
  - [Supprimer ce comparable]

---

## Failure modes et mitigations

| Mode | Sévérité | Mitigation |
|------|----------|-----------|
| 0 comparables → CONF002 blocking | Minor | Warning doux en UI avant launch; pipeline complète mais A_REVOIR |
| source_id vide → CONF003 + pénalité score -0.40 | Minor | Inline hint "requis pour traçabilité OEAQ" sur le champ |
| Comparables body écrasent comparables fixture | Non-issue | `body_comps or case.get("comparables", [])` — body a priorité, sinon fixture |
| prix_vente = 0 (oubli) | Minor | Validation: warning si prix_vente ≤ 0 avant soumission |

---

## Tests

| Classe | Vérifie |
|--------|---------|
| `TestStartRuntime_ComparablesInjected` | body avec comparables → case["comparables"] correctement mappé |
| `TestStartRuntime_ComparablesMerge` | body avec comparables → écrase fixture comparables |
| `TestStartRuntime_NoComparables` | body sans comparables → case["comparables"] vient de fixture |
| `TestMapComparableInput_Full` | tous les champs mappés correctement (surface dict, confidence 0.80) |
| `TestMapComparableInput_NullOptionals` | surface_hab=None → surface={}, annee=None → None |

---

## Dépendances

- Aucune nouvelle dépendance Python ou npm
- `tools.py:search_comparables` déjà câblé — aucune modification
- `runtime.py:_artifact_payload` déjà câblé — aucune modification
