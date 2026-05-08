import type { Adjustment } from '@/types'

function formatAdj(value: number): string {
  if (value === 0) return '-'
  const abs = new Intl.NumberFormat('fr-CA').format(Math.abs(value))
  return value > 0 ? `+${abs}` : `-${abs}`
}

function formatPrice(value: number): string {
  if (value === 0) return '-'
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  }).format(value).replace('CA', '').trim()
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
  return (
    <div className="mt-2.5 overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {['Comparable', 'Prix vente', 'Source', 'Temps', 'Condition', 'Garage', 'Prix ajuste'].map(h => (
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
      </table>
    </div>
  )
}
