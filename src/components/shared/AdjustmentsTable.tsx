import type { Adjustment } from '@/types'
import { summarizeAdjustments } from '@/lib/summarize-adjustments'
import { formatCAD, fmtNum } from '@/lib/format-number'

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
  return (
    <div className="mt-2.5 overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {['Comparable', 'Prix vente', 'Surface', 'Temps', 'Condition', 'Garage', 'Prix ajusté'].map(h => (
              <th key={h}
                className={`px-2.5 py-[7px] text-[10px] font-medium text-[#b5b2ac] uppercase tracking-[.06em] border-b border-black/[.07] ${h === 'Comparable' ? 'text-left' : 'text-right'}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-[12px] text-[#8a8780] text-left">{row.comparableLabel}</td>
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right">{formatPrice(row.salePrice)}</td>
              <AdjCell value={row.surface_adj} />
              <AdjCell value={row.year_adj} />
              <AdjCell value={row.condition_adj} />
              <AdjCell value={row.garage_adj} />
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right font-medium">{formatPrice(row.adjusted)}</td>
            </tr>
          ))}
        </tbody>
        {summary && rows.length > 1 && (
          <tfoot>
            <tr className="bg-black/[.025]">
              <td className="px-2.5 py-[8px] text-[10px] text-[#8a8780] uppercase tracking-[.06em] text-left" colSpan={6}>
                Moyenne ({rows.length} comp.) — écart {formatPrice(summary.spread)}
              </td>
              <td className="px-2.5 py-[8px] text-right font-semibold text-[12px] text-[#1a1916]">
                {formatPrice(summary.avg)}
              </td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  )
}
