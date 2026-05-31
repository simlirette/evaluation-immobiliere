'use client'

import type { SourceCoverage, SourceDiagnostic } from '@/types'

// Status color mapping
const STATUS_STYLE: Record<SourceDiagnostic['status'], { dot: string; text: string }> = {
  ok:      { dot: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-400' },
  partial: { dot: 'bg-amber-400',   text: 'text-amber-700 dark:text-amber-400' },
  empty:   { dot: 'bg-amber-400',   text: 'text-amber-700 dark:text-amber-400' },
  skipped: { dot: 'bg-[#b5b2ac]',   text: 'text-[#8a8780]' },
  failed:  { dot: 'bg-red-500',     text: 'text-red-700 dark:text-red-400' },
  missing: { dot: 'bg-red-400',     text: 'text-red-600 dark:text-red-400' },
}

const COVERAGE_TONE: Record<SourceCoverage['status'], string> = {
  ok:          'border-emerald-200/60 bg-emerald-50/40 dark:border-emerald-800/40 dark:bg-emerald-950/10',
  partial:     'border-amber-200/60 bg-amber-50/40 dark:border-amber-800/40 dark:bg-amber-950/10',
  degraded:    'border-amber-300/70 bg-amber-50/60 dark:border-amber-700/50 dark:bg-amber-950/20',
  unavailable: 'border-red-200/60 bg-red-50/40 dark:border-red-800/40 dark:bg-red-950/10',
  unknown:     'border-black/[.07] bg-black/[.02] dark:border-white/[.07] dark:bg-white/[.02]',
}

const COVERAGE_LABEL: Record<SourceCoverage['status'], string> = {
  ok:          'Sources disponibles',
  partial:     'Sources partiellement disponibles',
  degraded:    'Sources dégradées',
  unavailable: 'Sources indisponibles',
  unknown:     'Sources non vérifiées',
}

function DiagRow({ d }: { d: SourceDiagnostic }) {
  const style = STATUS_STYLE[d.status] ?? STATUS_STYLE.missing
  return (
    <div className="flex items-start gap-2 py-1.5">
      <span className={`mt-1.5 flex-shrink-0 w-1.5 h-1.5 rounded-full ${style.dot}`} aria-hidden />
      <div className="min-w-0">
        <span className={`text-[11px] font-semibold uppercase tracking-wide ${style.text}`}>
          {d.source}
        </span>
        {d.stage && (
          <span className="ml-1.5 text-[10px] text-[#b5b2ac] uppercase">{d.stage}</span>
        )}
        <p className="text-[12px] text-[#5a5854] dark:text-[#c8c4bc] leading-snug mt-0.5">
          {d.message}
        </p>
      </div>
    </div>
  )
}

interface Props {
  coverage: SourceCoverage
  /** When true, only shows problem sources (failed/empty/partial/missing) */
  problemsOnly?: boolean
  /** Compact variant for inline use */
  compact?: boolean
}

export default function SourceDiagnosticPanel({ coverage, problemsOnly = true, compact = false }: Props) {
  if (coverage.status === 'unknown' && coverage.diagnostics.length === 0) return null

  const shownDiags = problemsOnly
    ? coverage.diagnostics.filter(d => ['failed', 'empty', 'missing', 'partial'].includes(d.status))
    : coverage.diagnostics

  const tone = COVERAGE_TONE[coverage.status] ?? COVERAGE_TONE.unknown
  const label = COVERAGE_LABEL[coverage.status] ?? 'Sources'
  const hasFailed = coverage.failed_count > 0 || coverage.missing_count > 0

  if (compact) {
    return (
      <div className={`rounded-[8px] border px-3 py-2 ${tone}`}>
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] uppercase tracking-widest text-[#8a8780]">{label}</span>
          <span className="text-[11px] font-medium text-[#5a5854] dark:text-[#c8c4bc]">
            {coverage.ok_count}/{coverage.expected_sources.length}
          </span>
        </div>
        {shownDiags.slice(0, 3).map((d, i) => (
          <div key={`${d.source}-${i}`} className="mt-1 text-[12px] text-[#5a5854] dark:text-[#c8c4bc] leading-snug">
            <span className="font-semibold">{d.source}</span>
            <span className="opacity-70"> — {d.message}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`rounded-[10px] border px-4 py-3 ${tone}`}>
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-1">
        <div className="flex items-center gap-2">
          {hasFailed && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0"
              aria-hidden>
              <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.5"
                className="text-amber-600 dark:text-amber-400"/>
              <line x1="7" y1="4" x2="7" y2="8" stroke="currentColor" strokeWidth="1.5"
                strokeLinecap="round" className="text-amber-600 dark:text-amber-400"/>
              <circle cx="7" cy="10.5" r="0.75" fill="currentColor"
                className="text-amber-600 dark:text-amber-400"/>
            </svg>
          )}
          <span className="text-[12px] font-medium text-[#3a3835] dark:text-[#e0ddd8]">{label}</span>
        </div>
        <span className="text-[11px] text-[#8a8780]">
          {coverage.ok_count}/{coverage.expected_sources.length} opérationnelles
        </span>
      </div>

      {/* Diagnostic rows */}
      {shownDiags.length > 0 ? (
        <div className="divide-y divide-black/[.04] dark:divide-white/[.05]">
          {shownDiags.map((d, i) => (
            <DiagRow key={`${d.source}-${d.stage}-${i}`} d={d} />
          ))}
        </div>
      ) : (
        <p className="text-[12px] text-[#8a8780] mt-1">Aucun détail disponible.</p>
      )}

      {/* Hint for empty pool */}
      {hasFailed && (
        <p className="mt-2 text-[11px] text-[#8a8780] leading-snug border-t border-black/[.05] dark:border-white/[.06] pt-2">
          Importez un export CSV JLR pour compléter le pool de comparables.
        </p>
      )}
    </div>
  )
}
