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

  if (error) {
    return (
      <div className="rounded-[10px] px-4 py-3 bg-red-50/80 border border-red-200/60 mb-3">
        <div className="text-[12px] font-medium text-red-700 mb-1">
          {workflowStatus === 'TIMEOUT' ? 'Expiration du pipeline' : 'Extraction PDF incomplete'}
        </div>
        <div className="text-[11px] text-red-600">{error}</div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-[11px] bg-red-700 text-white rounded-full px-3 py-1 hover:bg-red-800 transition-colors"
          >
            Reessayer
          </button>
        )}
      </div>
    )
  }

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
