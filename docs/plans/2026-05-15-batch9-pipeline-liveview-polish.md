# Batch 9 — Pipeline live view + UX polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher la progression réelle du pipeline step-by-step, rendre le panel rapport redimensionnable, et polisher le chargement et les états de complétion.

**Architecture:** Hook `usePipelinePolling` poll `/app/state` toutes les 2s et expose `{steps, workflowStatus, error}` — zéro changement backend. `DragHandle` composant gère le resize via `mousemove`/`mouseup` natifs, `leftWidth` state dans `RapportPanel` persisté en `localStorage`. `PanelSkeleton` remplace les 3 dots de `PanelLoader`. Badge vert sur tab Rapport via prop `reportReady` dans `TabBar`, signalé par `DossierPanel.onPipelineComplete → page.tsx`.

**Tech Stack:** Next.js/TypeScript/Tailwind — aucun nouveau package npm.

**Assumptions:**
- Assumes `workflow.status === 'ASSISTANCE_DOSSIER_ACTIVE'` quand pipeline terminé normalement (pattern `?? 'ASSISTANCE_DOSSIER_ACTIVE'` dans `RapportPanel` confirme cette valeur) — will NOT work si le backend utilise une valeur différente. Implementer doit vérifier dans `backend/engine/runtime.py` avant de coder TERMINAL_STATUSES.
- Assumes `workflow.steps` est `Array<{id, label, status, complete}>` — confirmé dans `RapportPanel` (batch 8a).
- Assumes `localStorage` disponible côté client — tous les composants modifiés sont `'use client'`, pas de SSR issue.
- Assumes `app.active?.workflow.steps` est toujours défini quand `app.active` existe — pattern établi en batch 8a.

---

## File Structure

| Fichier | Action | Responsabilité |
|---------|--------|----------------|
| `src/hooks/usePipelinePolling.ts` | Créer | Polling `/app/state` + timeout 90s + auto-stop terminal |
| `src/components/shared/PipelineProgress.tsx` | Créer | Affichage ✓/⟳/○ par étape + bannière erreur FAILED/TIMEOUT |
| `src/components/shared/DragHandle.tsx` | Créer | Handle resize 8px, mousemove/mouseup sur `document` |
| `src/components/shared/PanelSkeleton.tsx` | Créer | Blocs `animate-pulse` Tailwind |
| `src/components/shared/PanelLoader.tsx` | Modifier | Délègue à `PanelSkeleton` (supprime les 3 dots custom) |
| `src/components/panels/DossierPanel.tsx` | Modifier | `isRunning` + `usePipelinePolling` + `PipelineProgress` + `onPipelineComplete` prop |
| `src/components/panels/RapportPanel.tsx` | Modifier | `leftWidth` state + `DragHandle` + `localStorage` persist |
| `src/components/layout/TabBar.tsx` | Modifier | Prop `reportReady?: boolean` → badge vert ● sur tab Rapport |
| `src/app/dossier/[id]/page.tsx` | Modifier | State `reportReady` + passe `onPipelineComplete` à `DossierPanel` + `reportReady` à `TabBar` |

---

## Wave Plan
- **Wave 1:** Task 1 (usePipelinePolling) + Task 4 (DragHandle) + Task 6 (PanelSkeleton + PanelLoader) — nouveaux fichiers disjoints
- **Wave 2:** Task 2 (PipelineProgress, après Task 1) + Task 5 (RapportPanel resize, après Task 4)
- **Wave 3:** Task 3 (DossierPanel + TabBar + page.tsx, après Tasks 1+2)
- **Wave 4:** Task 7 (vérification finale)

---

### Task 1: Hook usePipelinePolling

**Files:**
- Create: `src/hooks/usePipelinePolling.ts`

**Security flag:** `none`

**Does NOT cover:** Polling sur les panels Marché/Analyse (uniquement DossierPanel). Retry automatique sur erreur réseau (continue de retenter toutes les 2s).

- [ ] **Step 1: Create src/hooks/usePipelinePolling.ts**

```typescript
import { useEffect, useRef, useState, useCallback } from 'react'
import { fetchAppState } from '@/lib/runtime-api'

export interface PipelineStep {
  id: string
  label: string
  status: string
  complete: boolean
}

export interface PollResult {
  steps: PipelineStep[]
  workflowStatus: string
  error: string | null
  isPolling: boolean
}

// Statuts qui indiquent que le pipeline est terminé.
// ⚠ Vérifier dans backend/engine/runtime.py que ces valeurs correspondent.
export const PIPELINE_TERMINAL_STATUSES = new Set([
  'ASSISTANCE_DOSSIER_ACTIVE',
  'READY',
  'FAILED',
])

const POLL_INTERVAL_MS = 2000
const TIMEOUT_MS = 90_000

export function usePipelinePolling(
  dossierId: string | null,
  enabled: boolean
): PollResult {
  const [steps, setSteps] = useState<PipelineStep[]>([])
  const [workflowStatus, setWorkflowStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const startTimeRef = useRef<number | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsPolling(false)
  }, [])

  useEffect(() => {
    if (!dossierId || !enabled) return

    startTimeRef.current = Date.now()
    setIsPolling(true)

    const poll = async () => {
      if (
        startTimeRef.current !== null &&
        Date.now() - startTimeRef.current > TIMEOUT_MS
      ) {
        stopPolling()
        setWorkflowStatus('TIMEOUT')
        setError('Expiration — vérifier le backend (90s sans réponse)')
        return
      }
      try {
        const app = await fetchAppState(dossierId)
        const status: string = (app.active?.workflow.status as string | null) ?? ''
        const newSteps = (app.active?.workflow.steps ?? []) as PipelineStep[]
        setSteps(newSteps)
        setWorkflowStatus(status)
        setError(null)
        const allDone = newSteps.length > 0 && newSteps.every(s => s.complete)
        if (PIPELINE_TERMINAL_STATUSES.has(status) || allDone) {
          stopPolling()
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erreur réseau')
        // Ne pas arrêter le polling sur erreur réseau — retry au prochain tick
      }
    }

    poll()
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS)

    return stopPolling
  }, [dossierId, enabled, stopPolling])

  return { steps, workflowStatus, error, isPolling }
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/hooks/usePipelinePolling.ts && git commit -m "feat(batch9): usePipelinePolling hook — poll /app/state every 2s, auto-stop on terminal"
```

---

### Task 2: PipelineProgress component

**Files:**
- Create: `src/components/shared/PipelineProgress.tsx`

**Security flag:** `none`

**Does NOT cover:** Affichage des logs détaillés par étape (contenu LLM). Retry automatique (onRetry callback délégué à l'appelant).

- [ ] **Step 1: Create src/components/shared/PipelineProgress.tsx**

```typescript
'use client'

import type { PipelineStep } from '@/hooks/usePipelinePolling'
import { PIPELINE_TERMINAL_STATUSES } from '@/hooks/usePipelinePolling'

interface Props {
  steps: PipelineStep[]
  workflowStatus: string
  error: string | null
  onRetry?: () => void
}

export default function PipelineProgress({ steps, workflowStatus, error, onRetry }: Props) {
  const allDone = steps.length > 0 && steps.every(s => s.complete)

  // Pipeline terminé normalement — composant invisible
  if ((PIPELINE_TERMINAL_STATUSES.has(workflowStatus) && workflowStatus !== 'FAILED') || allDone) {
    return null
  }

  // Erreur ou timeout
  if (workflowStatus === 'FAILED' || workflowStatus === 'TIMEOUT') {
    return (
      <div className="rounded-[10px] px-4 py-3 bg-red-50/80 border border-red-200/60 mb-3">
        <div className="text-[12px] font-medium text-red-700 mb-1">
          {workflowStatus === 'TIMEOUT' ? 'Expiration du pipeline' : 'Pipeline échoué'}
        </div>
        <div className="text-[11px] text-red-600">{error ?? 'Vérifier le backend.'}</div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-[11px] bg-red-700 text-white rounded-full px-3 py-1 hover:bg-red-800 transition-colors"
          >
            Réessayer
          </button>
        )}
      </div>
    )
  }

  const currentIdx = steps.findIndex(s => !s.complete)
  const completedCount = steps.filter(s => s.complete).length

  return (
    <div className="rounded-[10px] bg-black/[.025] border border-black/[.06] px-4 py-3 mb-3">
      {steps.length === 0 ? (
        <div className="flex items-center gap-2 text-[12px] text-[#8a8780]">
          <span className="inline-block w-3 h-3 rounded-full border-2 border-[#334155] border-t-transparent animate-spin flex-shrink-0" />
          Démarrage du pipeline…
        </div>
      ) : (
        <>
          <div className="text-[11px] text-[#b5b2ac] mb-2.5">
            Étape {completedCount + 1}/{steps.length}
            {currentIdx >= 0 && ` — ${steps[currentIdx].label}`}
          </div>
          <div className="flex flex-col gap-1.5">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-center gap-2">
                {step.complete ? (
                  <span className="text-[11px] text-[#1f7a5c] w-3 text-center flex-shrink-0">✓</span>
                ) : i === currentIdx ? (
                  <span className="inline-block w-3 h-3 rounded-full border-2 border-[#334155] border-t-transparent animate-spin flex-shrink-0" />
                ) : (
                  <span className="text-[11px] text-[#b5b2ac] w-3 text-center flex-shrink-0">○</span>
                )}
                <span
                  className={`text-[12px] ${
                    step.complete
                      ? 'text-[#8a8780]'
                      : i === currentIdx
                      ? 'text-[#1a1916] font-medium'
                      : 'text-[#b5b2ac]'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/PipelineProgress.tsx && git commit -m "feat(batch9): PipelineProgress component — step list, spinner, error banner"
```

---

### Task 3: DossierPanel wiring + TabBar badge + page.tsx

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`
- Modify: `src/components/layout/TabBar.tsx`
- Modify: `src/app/dossier/[id]/page.tsx`

**Security flag:** `none`

**Does NOT cover:** Polling sur l'onglet DossierPanel si l'utilisateur a navigué vers un autre onglet (DossierPanel est démonté, le badge s'affiche lors du retour sur l'onglet Dossier). Badge sur les tabs Marché / Analyse.

- [ ] **Step 1: Read DossierPanel.tsx**

Lire `src/components/panels/DossierPanel.tsx` en entier pour vérifier la structure exacte avant modification.

- [ ] **Step 2: Update DossierPanel.tsx**

**2a. Ajouter imports** après les imports existants :
```typescript
import PipelineProgress from '@/components/shared/PipelineProgress'
import { usePipelinePolling, PIPELINE_TERMINAL_STATUSES } from '@/hooks/usePipelinePolling'
import type { PipelineStep } from '@/hooks/usePipelinePolling'
```

**2b. Mettre à jour l'interface Props** (ajouter `onPipelineComplete`) :
```typescript
interface Props {
  isNew: boolean
  dossierId: string | null
  onPipelineComplete?: () => void
}
```

**2c. Mettre à jour la destructuration de `DossierPanel`** :
```typescript
export default function DossierPanel({ isNew, dossierId, onPipelineComplete }: Props) {
```

**2d. Ajouter les states pour le polling** — après les `useState` existants (après `conflit`) :
```typescript
  const [isRunning, setIsRunning] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
```

**2e. Câbler `usePipelinePolling`** — après les states :
```typescript
  const {
    steps: pipelineSteps,
    workflowStatus: liveStatus,
    error: pipelineError,
  } = usePipelinePolling(dossierId, isRunning)
```

**2f. Mettre à jour l'`useEffect` de chargement** — remplacer le bloc `useEffect` existant (qui a `[dossierId]` comme dépendance) par :
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
      setConflitData(appState.active?.conflit ?? null)
      setLoading(false)
      // Démarrer le polling uniquement si le pipeline tourne encore
      if (!isNew) {
        const status = (appState.active?.workflow.status as string | null) ?? ''
        const existingSteps = (appState.active?.workflow.steps ?? []) as PipelineStep[]
        const allDone = existingSteps.length > 0 && existingSteps.every(s => s.complete)
        if (!PIPELINE_TERMINAL_STATUSES.has(status) && !allDone) {
          setIsRunning(true)
        }
      }
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dossierId, refreshKey])
```

**2g. Ajouter l'`useEffect` de surveillance du polling** — après l'useEffect de chargement :
```typescript
  useEffect(() => {
    if (!isRunning) return
    const allDone = pipelineSteps.length > 0 && pipelineSteps.every(s => s.complete)
    if (PIPELINE_TERMINAL_STATUSES.has(liveStatus) || allDone) {
      setIsRunning(false)
      onPipelineComplete?.()
      setRefreshKey(k => k + 1)
    }
  }, [liveStatus, pipelineSteps, isRunning, onPipelineComplete])
```

**2h. Ajouter `<PipelineProgress>` dans le JSX** — dans la `div` avec `w-full max-w-[640px]`, avant le bloc `{conflit?.detecte && ...}` :
```tsx
        {isRunning && (
          <PipelineProgress
            steps={pipelineSteps}
            workflowStatus={liveStatus}
            error={pipelineError}
          />
        )}
```

- [ ] **Step 3: Update TabBar.tsx**

**3a. Mettre à jour l'interface Props** :
```typescript
interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  hidden: boolean
  reportReady?: boolean
}
```

**3b. Mettre à jour la destructuration** :
```typescript
export default function TabBar({ activeTab, onTabChange, hidden, reportReady }: Props) {
```

**3c. Mettre à jour le rendu du bouton** — remplacer le contenu du bouton dans le `.map(tab => ...)` :
```tsx
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            data-active={activeTab === tab.id}
            className={`relative z-[1] px-[8px] sm:px-[22px] py-[7px] rounded-full text-[12px] sm:text-[13px] cursor-pointer whitespace-nowrap transition-colors duration-200 select-none bg-transparent border-none font-sans focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#334155] focus-visible:ring-offset-1 ${
              activeTab === tab.id ? 'text-[#1a1916] font-medium' : 'text-[#8a8780] hover:text-[#1a1916]'
            }`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
            {tab.id === 'rapport' && reportReady && (
              <span className="absolute top-[6px] right-[4px] sm:right-[14px] w-1.5 h-1.5 rounded-full bg-[#1f7a5c]" />
            )}
          </button>
```

- [ ] **Step 4: Update page.tsx (DossierShellInner)**

**4a. Ajouter `reportReady` state** — après les `useState` existants :
```typescript
  const [reportReady, setReportReady] = useState(false)
```

**4b. Ajouter l'`useEffect` de reset badge** — après les `useEffect` existants :
```typescript
  useEffect(() => {
    if (activeTab === 'rapport') setReportReady(false)
  }, [activeTab])
```

**4c. Passer `reportReady` à `TabBar`** — ajouter la prop :
```tsx
        <TabBar
          activeTab={activeTab}
          onTabChange={setTab}
          hidden={showMesDossiers}
          reportReady={reportReady}
        />
```

**4d. Passer `onPipelineComplete` à `DossierPanel`** :
```tsx
            {activeTab === 'dossier'  && <DossierPanel isNew={isNew} dossierId={dossierId} onPipelineComplete={() => setReportReady(true)} />}
```

- [ ] **Step 5: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/panels/DossierPanel.tsx src/components/layout/TabBar.tsx src/app/dossier/[id]/page.tsx && git commit -m "feat(batch9): pipeline live progress in DossierPanel + Rapport tab badge on completion"
```

---

### Task 4: DragHandle component

**Files:**
- Create: `src/components/shared/DragHandle.tsx`

**Security flag:** `none`

**Does NOT cover:** Touch/mobile resize (souris uniquement). Persistance de la largeur (responsabilité de RapportPanel).

- [ ] **Step 1: Create src/components/shared/DragHandle.tsx**

```typescript
'use client'

interface Props {
  onDrag: (delta: number) => void
  onDragEnd?: () => void
}

export default function DragHandle({ onDrag, onDragEnd }: Props) {
  function handleMouseDown(e: React.MouseEvent) {
    e.preventDefault()

    function handleMouseMove(me: MouseEvent) {
      onDrag(me.movementX)
    }

    function handleMouseUp() {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      onDragEnd?.()
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  return (
    <div
      onMouseDown={handleMouseDown}
      className="flex-shrink-0 w-2 cursor-col-resize relative group select-none"
      title="Glisser pour redimensionner"
      role="separator"
      aria-orientation="vertical"
    >
      <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[3px] rounded-full bg-transparent group-hover:bg-black/[.10] transition-colors duration-150" />
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/DragHandle.tsx && git commit -m "feat(batch9): DragHandle component — col-resize, mousemove/mouseup on document"
```

---

### Task 5: RapportPanel resizable split

**Files:**
- Modify: `src/components/panels/RapportPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Resize vertical. Persistance cross-dossier (même clé localStorage pour tous les dossiers — comportement intentionnel V0).

- [ ] **Step 1: Read RapportPanel.tsx**

Lire `src/components/panels/RapportPanel.tsx` pour identifier :
- La ligne `const [split, setSplit] = useState(false)`
- Le bloc JSX `<div className={... split ? 'flex-[0_0_400px] ...`

- [ ] **Step 2: Update RapportPanel.tsx**

**2a. Ajouter import** en haut du fichier :
```typescript
import DragHandle from '@/components/shared/DragHandle'
```

**2b. Ajouter le state `leftWidth`** après `const [split, setSplit] = useState(false)` :
```typescript
  const [leftWidth, setLeftWidth] = useState<number>(() => {
    if (typeof window === 'undefined') return 400
    return Number(localStorage.getItem('rapport-panel-width') ?? '400') || 400
  })
```

**2c. Ajouter les handlers de drag** après les handlers existants (après `handleRestoreVersion`) :
```typescript
  function handleDrag(delta: number) {
    setLeftWidth(w => {
      const min = 280
      const max = Math.floor(window.innerWidth * 0.8)
      return Math.max(min, Math.min(max, w + delta))
    })
  }

  function handleDragEnd() {
    setLeftWidth(w => {
      localStorage.setItem('rapport-panel-width', String(w))
      return w
    })
  }
```

**2d. Mettre à jour le JSX du split view** — trouver la ligne :
```tsx
      <div className={`flex flex-col ${split ? 'flex-[0_0_400px] border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}>
```

La remplacer par :
```tsx
      <div
        className={`flex flex-col ${split ? 'border-r border-black/[.07] overflow-hidden' : 'w-full items-center justify-end'}`}
        style={split ? { flexBasis: `${leftWidth}px`, flexGrow: 0, flexShrink: 0 } : undefined}
      >
```

**2e. Ajouter `<DragHandle>` entre les deux panes** — trouver le bloc `{split && (<RapportDoc .../>)}` et le remplacer par :
```tsx
      {split && (
        <>
          <DragHandle onDrag={handleDrag} onDragEnd={handleDragEnd} />
          <RapportDoc
            address={dossierAddress}
            valeur={state.conclusion}
            comparables={state.comparables}
            adjustments={state.adjustments}
            factChips={state.factChips}
            valuationValues={state.valuationValues}
            complianceStatus={state.complianceStatus}
            blockingFailures={state.blockingFailures}
            warnings={state.warnings}
            onClose={() => setSplit(false)}
            reportText={state.reportText}
            onSave={handleSaveReport}
            onGenerate={handleGenerateReport}
            sessionId={dossierId ?? ''}
            dossierId={state.realDossierId}
            onSaveVersion={handleSaveVersion}
          />
        </>
      )}
```

- [ ] **Step 3: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -15
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/panels/RapportPanel.tsx && git commit -m "feat(batch9): resizable RapportPanel split — DragHandle + localStorage persist"
```

---

### Task 6: PanelSkeleton + PanelLoader update

**Files:**
- Create: `src/components/shared/PanelSkeleton.tsx`
- Modify: `src/components/shared/PanelLoader.tsx`

**Security flag:** `none`

**Does NOT cover:** Skeletons spécifiques par panel (même skeleton générique pour tous). Animation différente selon le contenu attendu.

- [ ] **Step 1: Create src/components/shared/PanelSkeleton.tsx**

```typescript
export default function PanelSkeleton() {
  return (
    <div className="flex flex-col flex-1 px-6 pt-6 pb-9 gap-3 max-w-[640px] mx-auto w-full">
      <div className="h-3 w-2/3 rounded-full bg-black/[.06] animate-pulse" />
      <div className="h-3 w-1/2 rounded-full bg-black/[.06] animate-pulse" />
      <div className="mt-2 h-[72px] rounded-[12px] bg-black/[.04] animate-pulse" />
      <div className="h-3 w-3/4 rounded-full bg-black/[.06] animate-pulse" />
      <div className="h-3 w-2/5 rounded-full bg-black/[.06] animate-pulse" />
      <div className="mt-1 h-[48px] rounded-[12px] bg-black/[.04] animate-pulse" />
      <div className="h-3 w-1/2 rounded-full bg-black/[.06] animate-pulse" />
    </div>
  )
}
```

- [ ] **Step 2: Update PanelLoader.tsx**

Remplacer le contenu entier de `src/components/shared/PanelLoader.tsx` par :
```typescript
import PanelSkeleton from './PanelSkeleton'

export default function PanelLoader() {
  return <PanelSkeleton />
}
```

- [ ] **Step 3: Verify TypeScript**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 4: Build check**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -15
```

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
cd C:\Users\simon\eval-immo && git add src/components/shared/PanelSkeleton.tsx src/components/shared/PanelLoader.tsx && git commit -m "feat(batch9): PanelSkeleton animate-pulse replaces 3-dot PanelLoader"
```

---

### Task 7: Vérification finale

**Files:**
- Update: `state.md`

**Security flag:** `none`

- [ ] **Step 1: Backend tests (unchanged)**

```bash
cd C:\Users\simon\eval-immo\backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -5
```

Expected: **115 PASS, 0 failures** (aucun changement backend).

- [ ] **Step 2: TypeScript check**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -10
```

Expected: No errors.

- [ ] **Step 3: Build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

Expected: Build succeeds, 0 TypeScript errors.

- [ ] **Step 4: Smoke test — usePipelinePolling logic**

```bash
cd C:\Users\simon\eval-immo && node -e "
// Test PIPELINE_TERMINAL_STATUSES export
const { PIPELINE_TERMINAL_STATUSES } = require('./src/hooks/usePipelinePolling.ts')
" 2>&1 | head -3
```

Si l'import échoue (tsx/ts non supporté par node natif) — vérifier la compilation uniquement via tsc. Ce step est optionnel.

- [ ] **Step 5: Update state.md**

Mettre à jour `state.md` :
- `Current Goal` → `Batch 9 DONE. Prêt pour test end-to-end pipeline É.A.`
- `Plan Status` → ajouter `- Batch 9 (pipeline live view + UX polish): DONE ✓`
- `Open Issues` → ajouter `- Pipeline à tester end-to-end avec dossier réel avant démo É.A.`

- [ ] **Step 6: Commit**

```bash
cd C:\Users\simon\eval-immo && git add state.md && git commit -m "chore(batch9): mark complete, 115 tests, pipeline live view + resize + skeleton live"
```

---

## Self-Review

**1. Spec coverage :**
- ✅ Pipeline live view step-by-step — `usePipelinePolling` + `PipelineProgress` + DossierPanel wiring (Tasks 1+2+3)
- ✅ Spinner "Étape N/7 — {label}" — dans `PipelineProgress` (Task 2)
- ✅ Rapport panel redimensionnable — `DragHandle` + `leftWidth` + `localStorage` (Tasks 4+5)
- ✅ Skeleton loaders — `PanelSkeleton` remplace `PanelLoader` (Task 6)
- ✅ État d'erreur explicite pipeline — bannière rouge FAILED/TIMEOUT dans `PipelineProgress` (Task 2)
- ✅ Badge vert tab Rapport — `reportReady` prop dans `TabBar`, câblé via `onPipelineComplete` (Task 3)
- ✅ Badge se réinitialise au clic sur tab Rapport — `useEffect([activeTab])` dans page.tsx (Task 3)

**2. Placeholder scan :** Aucun TBD/TODO. Step 4 de Task 7 (smoke test node) est explicitement marqué optionnel — sanction claire.

**3. Type consistency :**
- `PipelineStep {id, label, status, complete}` — défini Task 1, utilisé Tasks 2+3 ✅
- `PollResult {steps, workflowStatus, error, isPolling}` — défini Task 1, destructuré Task 3 ✅
- `PIPELINE_TERMINAL_STATUSES` — exporté Task 1, importé Tasks 2+3 ✅
- `onPipelineComplete?: () => void` — ajouté Task 3 Props, passé Task 3 page.tsx ✅
- `reportReady?: boolean` — ajouté Task 3 TabBar Props, passé Task 3 page.tsx ✅
- `onDrag(delta: number)` / `onDragEnd?()` — défini Task 4, appelé Task 5 ✅

**4. Scope-reduction scan :** Aucune réduction de scope détectée. "Optionnel" dans Task 7 Step 4 est explicitement le smoke test node — accepté car TypeScript compile déjà en Step 2.
