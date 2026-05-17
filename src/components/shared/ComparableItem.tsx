'use client'

import { useState } from 'react'
import type { Comparable } from '@/types'
import { computePricePerM2, formatPricePerM2 } from '@/lib/comparable-utils'
import { validateComparableDate } from '@/lib/validate-comparable-date'
import { formatComparableAge } from '@/lib/format-comparable-age'

const QUALITY_COLORS: Record<string, string> = {
  excellent: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  bon: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
  acceptable: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  faible: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
}

const COMPLETENESS_COLORS: Record<string, string> = {
  complet: 'text-emerald-600 dark:text-emerald-400',
  partiel: 'text-amber-600 dark:text-amber-400',
  incomplet: 'text-red-500',
}

export default function ComparableItem({ comp, qualityLabel, completenessGrade, missingFields }: {
  comp: Comparable
  qualityLabel?: string
  completenessGrade?: 'complet' | 'partiel' | 'incomplet'
  missingFields?: string[]
}) {
  const [expanded, setExpanded] = useState(false)
  const perM2 = computePricePerM2(comp.sale_price, comp.hab_m2)
  const dateValidation = validateComparableDate(comp.sale_date)

  const details: Array<{ label: string; value: string }> = []
  if (comp.hab_m2) details.push({ label: 'Surface hab.', value: `${comp.hab_m2} m²` })
  if (comp.terrain_m2) details.push({ label: 'Terrain', value: `${comp.terrain_m2} m²` })
  if (comp.year_built) details.push({ label: 'Année construction', value: String(comp.year_built) })
  if (comp.renovated_year) details.push({ label: 'Rénové', value: String(comp.renovated_year) })
  if (comp.garage_type) details.push({ label: 'Stationnement', value: comp.garage_type })
  if (perM2) details.push({ label: 'Prix/m²', value: formatPricePerM2(perM2) })

  return (
    <div
      className="rounded-[11px] border border-black/[.055] transition-colors"
      style={{ background: 'rgba(0,0,0,.04)' }}
    >
      <div
        className="grid items-center gap-2.5 px-3.5 py-[11px] cursor-pointer hover:bg-black/[.03] rounded-[11px]"
        style={{ gridTemplateColumns: '20px 1fr auto' }}
        onClick={() => details.length > 0 && setExpanded(e => !e)}
        role={details.length > 0 ? 'button' : undefined}
        tabIndex={details.length > 0 ? 0 : undefined}
        onKeyDown={e => e.key === 'Enter' && details.length > 0 && setExpanded(x => !x)}
        aria-expanded={details.length > 0 ? expanded : undefined}
      >
        <div className="text-[10px] text-[#b5b2ac] font-medium text-center relative">
          {comp.rank}
          {dateValidation.stale && (
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-amber-400" title={dateValidation.warning ?? ''} />
          )}
        </div>
        <div className="min-w-0">
          <div className="text-[13px] text-[#1a1916]">{comp.address}</div>
          <div className="text-[11px] text-[#8a8780] mt-0.5">{comp.meta}</div>
        </div>
        <div className="text-right flex items-center gap-2">
          <div>
            <div className="flex items-center justify-end gap-1.5">
              <div className="text-[13px] font-medium text-[#1a1916]">{comp.price}</div>
              {qualityLabel && (
                <span className={`text-[9px] font-medium rounded-full px-1.5 py-0.5 ${QUALITY_COLORS[qualityLabel] ?? 'bg-black/[.05] text-[#8a8780]'}`}>
                  {qualityLabel}
                </span>
              )}
            </div>
            <div className="text-[11px] text-[#8a8780] mt-0.5">
              {comp.date}
              <span className={`ml-1.5 ${dateValidation.stale ? 'text-amber-600' : 'text-[#b5b2ac]'}`}>
                · {formatComparableAge(dateValidation.ageMonths)}
              </span>
            </div>
          </div>
          {details.length > 0 && (
            <svg
              width="12" height="12" fill="none" stroke="#b5b2ac" viewBox="0 0 24 24"
              className={`flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
            </svg>
          )}
        </div>
      </div>

      {expanded && details.length > 0 && (
        <div className="px-3.5 pb-3 pt-0.5 border-t border-black/[.05]">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {details.map(d => (
              <div key={d.label} className="flex justify-between items-baseline text-[11px]">
                <span className="text-[#8a8780]">{d.label}</span>
                <span className="text-[#1a1916] font-medium tabular-nums">{d.value}</span>
              </div>
            ))}
          </div>
          {dateValidation.warning && (
            <div className="mt-2 text-[10px] text-amber-700 bg-amber-50/80 border border-amber-200/60 rounded-[6px] px-2.5 py-1.5 leading-relaxed">
              {dateValidation.warning}
            </div>
          )}
          {completenessGrade && completenessGrade !== 'complet' && missingFields && missingFields.length > 0 && (
            <div className={`mt-1.5 text-[10px] ${COMPLETENESS_COLORS[completenessGrade]} leading-relaxed`}>
              Données manquantes&nbsp;: {missingFields.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
