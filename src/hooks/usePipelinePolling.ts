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
