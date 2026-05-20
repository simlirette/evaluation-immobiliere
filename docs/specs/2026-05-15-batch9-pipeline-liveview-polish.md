# Batch 9 — Pipeline live view + UX polish

## Scope

**In scope :**
- Pipeline live view dans DossierPanel : pendant l'exécution, afficher chaque étape (✓/⟳/○) via polling `/app/state` toutes les 2s
- Rapport panel redimensionnable : drag handle entre colonne chat et RapportDoc dans le split view, largeur persistée en `localStorage`
- UX polish ciblé :
  - Skeleton loader lors du chargement initial de chaque panel
  - État d'erreur explicite quand le pipeline échoue (message d'erreur réel affiché)
  - Badge de complétion sur le tab "Rapport" une fois la rédaction terminée

**Non-goals :**
- Refonte backend / ajustements de prompts — Batch 10 après tests réels
- Données rôle d'évaluation foncière — Batch 10+
- Responsive mobile
- Logs détaillés par étape (contenu LLM visible pendant l'exécution)
- Drag resize sur les autres panels (Marche, Analyse)

---

## Architecture

### 1. Pipeline live view

#### Hook `usePipelinePolling`

```
src/hooks/usePipelinePolling.ts  (nouveau fichier)

usePipelinePolling(dossierId: string | null, enabled: boolean)
  → { steps, workflowStatus, error }

Comportement :
- Si enabled=false : aucun polling
- Si enabled=true : setInterval 2000ms → fetchAppState(dossierId)
- S'arrête automatiquement quand workflowStatus ∈ { READY, FAILED, ASSISTANCE_DOSSIER_ACTIVE }
- Timeout 90s → workflowStatus = 'TIMEOUT', message explicite
- cleanup : clearInterval dans useEffect return
```

`workflow.steps` existe déjà dans AppState : `{id, label, status, complete}`. Zéro changement backend.

#### Composant `<PipelineProgress>`

```
src/components/shared/PipelineProgress.tsx  (nouveau fichier)

Props : steps: Step[], status: string, error?: string

Affichage :
- Liste des étapes avec icône : ✓ (complete) / spinner animé CSS (en cours) / ○ (en attente)
- "Étape N/7 — {label actuel}…" en sous-titre
- Si status=FAILED ou TIMEOUT : bannière rouge avec message d'erreur
- Disparaît (retourne null) quand status=READY
```

#### Intégration DossierPanel

```
src/components/panels/DossierPanel.tsx  (modifié)

- Ajouter state isRunning (true entre le clic "Lancer" et status=READY/FAILED)
- Passer dossierId + isRunning à usePipelinePolling
- Afficher <PipelineProgress> pendant l'exécution, à la place du spinner actuel
```

### 2. Rapport panel redimensionnable

```
src/components/panels/RapportPanel.tsx  (modifié)

- Remplacer flex-[0_0_400px] par flex-[0_0_${leftWidth}px]
- Ajouter <DragHandle> entre les deux panes
- useState leftWidth, initialisé depuis localStorage('rapport-panel-width') ?? 400
- Clamp : min 280px, max 80% de window.innerWidth
- Persist dans localStorage à chaque drag end (onMouseUp)
```

```
src/components/shared/DragHandle.tsx  (nouveau fichier)

Props : onDrag(delta: number) → void

- div 8px large, cursor-col-resize, bg transparent hover:bg-black/[.06]
- onMouseDown → document.addEventListener mousemove + mouseup
- mousemove : appelle onDrag(e.movementX)
- mouseup : cleanup listeners
- Pas de librairie externe
```

### 3. UX polish

#### Skeleton loaders

Chaque panel (DossierPanel, MarchePanel, AnalysePanel, RapportPanel) retourne déjà `<PanelLoader />` pendant le chargement. Remplacer `PanelLoader` (spinner générique) par un `<PanelSkeleton>` avec blocs gris animés représentant la structure du contenu.

```
src/components/shared/PanelSkeleton.tsx  (nouveau fichier)

- animate-pulse (Tailwind)
- 3-4 blocs rectangulaires gris de hauteurs variées
- Remplace PanelLoader dans les 4 panels + DossiersPage
```

#### État d'erreur pipeline

Dans `<PipelineProgress>`, si `status === 'FAILED'` ou `workflowStatus` contient une erreur :
- Bannière rouge avec `error` message
- Bouton "Réessayer" → rappelle `handleLaunchPipeline()`

#### Badge tab "Rapport"

Dans `TabBar` ou le composant parent de navigation :
- Si `workflowStatus === 'READY'` ET l'onglet Rapport n'a pas encore été visité → badge vert "✓" sur le tab Rapport
- Badge disparaît au premier clic sur le tab

---

## Fichiers modifiés / créés

| Fichier | Action | Description |
|---------|--------|-------------|
| `src/hooks/usePipelinePolling.ts` | Créer | Hook polling `/app/state` toutes les 2s |
| `src/components/shared/PipelineProgress.tsx` | Créer | Affichage étapes ✓/⟳/○ + erreur |
| `src/components/shared/DragHandle.tsx` | Créer | Handle CSS resize, no lib |
| `src/components/shared/PanelSkeleton.tsx` | Créer | Skeleton animate-pulse, remplace PanelLoader |
| `src/components/panels/DossierPanel.tsx` | Modifier | isRunning state + usePipelinePolling + PipelineProgress |
| `src/components/panels/RapportPanel.tsx` | Modifier | leftWidth state + DragHandle + localStorage |
| `src/components/shared/PanelLoader.tsx` | Modifier (ou remplacer) | Utilise PanelSkeleton |
| Tab navigation (à identifier) | Modifier | Badge ✓ sur tab Rapport quand READY |

---

## Tests

Pas de nouveaux tests backend (zéro changement backend).

Tests frontend (TypeScript compile + smoke) :
- `npx tsc --noEmit` — 0 erreurs
- `npx next build` — build clean

Tests manuels recommandés après implémentation :
1. Lancer le pipeline sur un dossier réel → vérifier que les étapes s'affichent en temps réel
2. Forcer une erreur (backend éteint) → vérifier la bannière rouge
3. Drag le handle rapport → vérifier resize + persistence après reload
4. Ouvrir un panel → vérifier le skeleton avant le contenu réel

---

## Failure modes et mitigations

| Mode | Sévérité | Mitigation |
|------|----------|------------|
| Polling continue après navigation (memory leak) | Critique | `clearInterval` dans `useEffect` return — standard React |
| Pipeline bloqué à `RUNNING` si backend crash | Mineur | Timeout 90s → status `TIMEOUT`, message "Expiration — vérifier le backend" |
| Drag trop sensible / imperceptible | Mineur | Clamp min/max + zone 8px + curseur CSS `col-resize` |
| Badge tab non réinitialisé entre dossiers | Mineur | Reset badge au changement de `dossierId` |
