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
  waitingCheckpoint: number | null
}

// Statuts qui indiquent que le pipeline est terminé.
// ⚠ Vérifier dans backend/engine/runtime.py que ces valeurs correspondent.
export const PIPELINE_TERMINAL_STATUSES = new Set([
  'ASSISTANCE_DOSSIER_ACTIVE',
  'READY',
  'FAILED',
])

const STEP_LABELS: Record<string, string> = {
  'mandat-intake':   'Analyse du mandat',
  'data-facts':      'Extraction des faits',
  'amu-analyst':     'Analyse de marché',
  'comps-market':    'Sélection des comparables',
  'valuation-draft': 'Calcul de valeur',
  'compliance-qa':   'Conformité OEAQ',
  'redaction':       'Rédaction du rapport',
}

function progressToSteps(progress: { steps: string[]; completed: string[]; running: string | null }): PipelineStep[] {
  return progress.steps.map(id => ({
    id,
    label: STEP_LABELS[id] ?? id,
    status: progress.completed.includes(id) ? 'DONE' : id === progress.running ? 'EN_COURS' : 'EN_ATTENTE',
    complete: progress.completed.includes(id),
  }))
}

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
  const [waitingCheckpoint, setWaitingCheckpoint] = useState<number | null>(null)
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
        setWorkflowStatus(status)
        const runtimeError = app.active?.pipeline_error ?? app.active?.ingestion_error ?? null
        setError(runtimeError ? String(runtimeError) : null)

        // Use real-time agent step progress when available, fall back to workflow steps
        const progress = app.active?.pipeline_progress
        if (progress && progress.steps.length > 0) {
          const agentSteps = progressToSteps(progress)
          setSteps(agentSteps)
          const wcp = progress.waiting_checkpoint ?? null
          setWaitingCheckpoint(wcp)
          // Stop polling when segment completes (waiting for checkpoint confirmation)
          // or pipeline fully terminates
          const allAgentsDone = progress.completed.length === progress.steps.length
          if (wcp !== null || allAgentsDone || PIPELINE_TERMINAL_STATUSES.has(status) || runtimeError) {
            stopPolling()
          }
        } else {
          const workflowSteps = (app.active?.workflow.steps ?? []) as PipelineStep[]
          setSteps(workflowSteps)
          const allDone = workflowSteps.length > 0 && workflowSteps.every(s => s.complete)
          if (PIPELINE_TERMINAL_STATUSES.has(status) || allDone || runtimeError) {
            stopPolling()
          }
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

  return { steps, workflowStatus, error, isPolling, waitingCheckpoint }
}
