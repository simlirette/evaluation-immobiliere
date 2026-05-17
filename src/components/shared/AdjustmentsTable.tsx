import type { Adjustment } from '@/types'
import { summarizeAdjustments } from '@/lib/summarize-adjustments'
import { computeNetAdjustment } from '@/lib/compute-net-adjustment'
import { computeGrossAdjustment } from '@/lib/compute-gross-adjustment'
import { computeMedianIndicatedValue } from '@/lib/compute-median-indicated-value'
import { detectOutlierComparables } from '@/lib/detect-outlier-comparables'
import { computeReconciledValue } from '@/lib/compute-reconciled-value'
import { formatCAD, fmtNum, formatPct } from '@/lib/format-number'

function formatAdj(value: number): string {
  if (value === 0) return '-'
  const abs = fmtNum(Math.abs(value), 0)
  return value > 0 ? `+${abs}` : `-${abs}`
}

function formatPrice(value: number): string {
  if (value === 0) return '-'
  return formatCAD(value)
}

function AdjCell({ value }: { value: number }) {
  const str = formatAdj(value)
  return (
    <td className={`px-2.5 py-[9px] border-b border-black/[.04] text-right whitespace-nowrap ${
      value > 0 ? 'text-[#228866]' : value < 0 ? 'text-[#c0392b]' : 'text-[#1a1916]'
    }`}>
      {str}
    </td>
  )
}

export default function AdjustmentsTable({ rows }: { rows: Adjustment[] }) {
  const summary = summarizeAdjustments(rows)
  const median = computeMedianIndicatedValue(rows)
  const reconciled = computeReconciledValue(rows)
  const outliers = detectOutlierComparables(rows)
  const outlierMap = new Map(outliers.map(o => [o.id, o]))
  return (
    <div className="mt-2.5 overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {['Comparable', 'Prix vente', 'Surface', 'Temps', 'Condition', 'Garage', 'Net adj.', 'Prix ajusté'].map(h => (
              <th key={h}
                className={`px-2.5 py-[7px] text-[10px] font-medium text-[#b5b2ac] uppercase tracking-[.06em] border-b border-black/[.07] ${h === 'Comparable' ? 'text-left' : 'text-right'}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const { net, netPct, absPct } = computeNetAdjustment(row)
            const { grossPct } = computeGrossAdjustment(row)
            const netColor = absPct >= 25 ? 'text-[#c0392b]' : absPct >= 15 ? 'text-amber-600' : 'text-[#6a6763]'
            const grossColor = grossPct >= 40 ? 'text-[#c0392b]' : grossPct >= 25 ? 'text-amber-600' : 'text-[#b5b2ac]'
            const outlier = outlierMap.get(row.id)
            return (
              <tr key={i}>
                <td className="px-2.5 py-[9px] border-b border-black/[.04] text-[12px] text-[#8a8780] text-left">{row.comparableLabel}</td>
                <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right">{formatPrice(row.salePrice)}</td>
                <AdjCell value={row.surface_adj} />
                <AdjCell value={row.year_adj} />
                <AdjCell value={row.condition_adj} />
                <AdjCell value={row.garage_adj} />
                <td className={`px-2.5 py-[9px] border-b border-black/[.04] text-right whitespace-nowrap text-[11px] ${netColor}`}>
                  {net !== 0 ? `${net > 0 ? '+' : ''}${fmtNum(net, 0)} (${formatPct(netPct, 1)})` : '-'}
                  {grossPct > 0 && (
                    <div className={`text-[10px] leading-tight ${grossColor}`}>
                      brut {formatPct(grossPct, 1)}
                    </div>
                  )}
                </td>
                <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right font-medium">
                  {formatPrice(row.adjusted)}
                  {outlier?.isOutlier && (
                    <div className="text-[10px] font-normal text-amber-600 leading-tight" title="Valeur indiquée atypique (écart > 15 % vs médiane)">
                      {outlier.deviationFromMedianPct > 0 ? '+' : ''}{fmtNum(outlier.deviationFromMedianPct, 1)} % vs méd.
                    </div>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
        {summary && rows.length > 1 && (
          <tfoot>
            <tr className="bg-black/[.025]">
              <td className="px-2.5 py-[8px] text-[10px] text-[#8a8780] uppercase tracking-[.06em] text-left" colSpan={7}>
                Moyenne ({rows.length} comp.) — écart {formatPrice(summary.spread)}
              </td>
              <td className="px-2.5 py-[8px] text-right font-semibold text-[12px] text-[#1a1916]">
                {formatPrice(summary.avg)}
              </td>
            </tr>
            {median !== null && (
              <tr className="bg-black/[.015]">
                <td className="px-2.5 py-[7px] text-[10px] text-[#8a8780] uppercase tracking-[.06em] text-left" colSpan={7}>
                  Médiane
                </td>
                <td className="px-2.5 py-[7px] text-right font-medium text-[12px] text-[#1a1916]">
                  {formatPrice(median)}
                </td>
              </tr>
            )}
            {reconciled && rows.length > 1 && (
              <tr className="bg-black/[.008]">
                <td className="px-2.5 py-[7px] text-[10px] text-[#8a8780] uppercase tracking-[.06em] text-left" colSpan={7}>
                  Réconcilié <span className="normal-case text-[9px] text-[#b5b2ac]">(pondéré — adj. brut)</span>
                </td>
                <td className="px-2.5 py-[7px] text-right font-medium text-[12px] text-[#1a1916]">
                  {formatPrice(reconciled.value)}
                  <div className="text-[9px] font-normal text-[#b5b2ac] leading-tight">{reconciled.confidence}</div>
                </td>
              </tr>
            )}
          </tfoot>
        )}
      </table>
    </div>
  )
}
