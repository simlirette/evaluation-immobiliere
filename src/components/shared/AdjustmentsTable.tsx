import type { Adjustment } from '@/types'

function isPositive(v: string) { return v.startsWith('+') }
function isNegative(v: string) { return v.startsWith('−') || v.startsWith('-') }

function AdjCell({ value }: { value: string }) {
  return (
    <td className={`px-2.5 py-[9px] border-b border-black/[.04] text-right whitespace-nowrap ${
      isPositive(value) ? 'text-[#228866]' : isNegative(value) ? 'text-[#c0392b]' : 'text-[#1a1916]'
    }`}>
      {value}
    </td>
  )
}

export default function AdjustmentsTable({ rows }: { rows: Adjustment[] }) {
  return (
    <div className="mt-2.5 overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {['Comparable','Prix vente','Surface','Année','Condition','Garage','Prix ajusté'].map(h => (
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
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-[12px] text-[#8a8780] text-left">{row.comparable}</td>
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right">{row.salePrice}</td>
              <AdjCell value={row.surface} />
              <AdjCell value={row.year} />
              <AdjCell value={row.condition} />
              <AdjCell value={row.garage} />
              <td className="px-2.5 py-[9px] border-b border-black/[.04] text-right font-medium">{row.adjusted}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
