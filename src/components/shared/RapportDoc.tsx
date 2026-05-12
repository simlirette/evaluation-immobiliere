import type { Comparable, Adjustment, FactChip } from '@/types'

interface Props {
  address?: string
  valeur?: string | null
  comparables: Comparable[]
  adjustments: Adjustment[]
  factChips: FactChip[]
  valuationValues: Record<string, number>
  complianceStatus: string
  blockingFailures: string[]
  warnings: string[]
  onClose: () => void
}

const APPROACH_LABELS: Record<string, string> = {
  approche_comparative: 'Approche comparative',
  approche_cout: 'Approche par le coût',
  approche_revenu: 'Approche par le revenu',
}

function fmtPrice(v: number) {
  return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(v)
}

function fmtDate(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <div className="text-[10px] uppercase tracking-[.1em] text-[#b5b2ac] mb-2 pb-1.5 border-b border-black/[.06]">
        {title}
      </div>
      {children}
    </div>
  )
}

export default function RapportDoc({
  address,
  valeur,
  comparables,
  adjustments,
  factChips,
  valuationValues,
  complianceStatus,
  blockingFailures,
  warnings,
  onClose,
}: Props) {
  const today = new Date().toLocaleDateString('fr-CA', { year: 'numeric', month: 'long', day: 'numeric' })
  const approaches = Object.entries(valuationValues).filter(([, v]) => v > 0)

  return (
    <div className="flex flex-col flex-1 relative overflow-hidden">
      <div className="absolute top-3 right-8 z-10">
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-[7px] flex items-center justify-center bg-transparent border-none cursor-pointer text-[#b5b2ac] hover:text-[#1a1916] hover:bg-black/[.06] transition-colors"
          title="Fermer"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M20 4L13 11M17 11H13V7M4 20L11 13M7 13H11V17"/>
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-10 scroll-fade">
        <div
          className="px-7 py-6 rounded-[14px] text-[13px] leading-[1.75] border border-black/[.06]"
          style={{ background: 'rgba(255,255,255,.55)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8)' }}
        >
          {/* En-tête */}
          <div className="mb-5 pb-4 border-b border-black/[.07]">
            <div
              className="text-[18px] font-medium text-[#1a1916] mb-0.5 tracking-[.01em]"
              style={{ fontFamily: 'var(--font-serif)' }}
            >
              BROUILLON DE RAPPORT D&rsquo;&Eacute;VALUATION
            </div>
            <div className="text-[11px] text-[#8a8780]">
              Brouillon non certifi&eacute; &mdash; validation et signature par un &eacute;valuateur agr&eacute;&eacute; hors syst&egrave;me requises avant diffusion.
            </div>
          </div>

          {/* Avertissement IA */}
          <div className="mb-5 px-3 py-2 rounded-[8px] bg-amber-50/80 border border-amber-200/60 text-[11px] text-amber-800">
            Ce brouillon est produit par un assistant IA. Il ne constitue pas une certification de valeur
            et ne remplace pas l&rsquo;opinion professionnelle d&rsquo;un &eacute;valuateur agr&eacute;&eacute;.
          </div>

          {/* Identification */}
          <Section title="1. Identification">
            <div className="grid grid-cols-2 gap-2 text-[12px]">
              <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
                <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac] mb-0.5">Bien &eacute;valu&eacute;</div>
                <div className="text-[#1a1916]">{address || '—'}</div>
              </div>
              <div className="rounded-[8px] bg-black/[.03] px-3 py-2">
                <div className="text-[10px] uppercase tracking-[.07em] text-[#b5b2ac] mb-0.5">Date du brouillon</div>
                <div className="text-[#1a1916]">{today}</div>
              </div>
            </div>
            {factChips.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {factChips.map((chip, i) => (
                  <span
                    key={i}
                    className={`text-[11px] px-2.5 py-1 rounded-full ${
                      chip.highlight
                        ? 'bg-[#1f7a5c]/10 text-[#1f7a5c] border border-[#1f7a5c]/20'
                        : 'bg-black/[.04] text-[#5a5854]'
                    }`}
                  >
                    {chip.label}
                  </span>
                ))}
              </div>
            )}
          </Section>

          {/* Conclusion */}
          <Section title="2. Conclusion de valeur propos&eacute;e">
            <div className="rounded-[10px] bg-[#1f7a5c]/[.06] border border-[#1f7a5c]/20 px-4 py-3">
              <div className="text-[10px] uppercase tracking-[.07em] text-[#1f7a5c]/70 mb-0.5">Valeur march&eacute; estim&eacute;e</div>
              <div
                className="text-[22px] font-semibold text-[#1a1916] tracking-tight"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                {valeur || '—'}
              </div>
              <div className="text-[11px] text-[#8a8780] mt-0.5">
                Statut conformit&eacute;&nbsp;: <span className="text-[#1a1916]">{complianceStatus || '—'}</span>
              </div>
            </div>
          </Section>

          {/* Approches */}
          {approaches.length > 0 && (
            <Section title="3. Approches de valeur">
              <div className="rounded-[8px] overflow-hidden border border-black/[.06]">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="bg-black/[.025]">
                      <th className="text-left px-3 py-2 font-medium text-[#5a5854]">M&eacute;thode</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Valeur indiqu&eacute;e</th>
                    </tr>
                  </thead>
                  <tbody>
                    {approaches.map(([key, val], i) => (
                      <tr key={key} className={i % 2 === 0 ? '' : 'bg-black/[.018]'}>
                        <td className="px-3 py-2 text-[#1a1916]">{APPROACH_LABELS[key] ?? key}</td>
                        <td className="px-3 py-2 text-right text-[#1a1916] font-medium tabular-nums">{fmtPrice(val)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Comparables */}
          {comparables.length > 0 && (
            <Section title="4. Soutien du march&eacute; — comparables retenus">
              <div className="rounded-[8px] overflow-hidden border border-black/[.06]">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="bg-black/[.025]">
                      <th className="text-left px-3 py-2 font-medium text-[#5a5854]">Comparable</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Prix de vente</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Date</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparables.map((c, i) => (
                      <tr key={c.id} className={i % 2 === 0 ? '' : 'bg-black/[.018]'}>
                        <td className="px-3 py-2 text-[#1a1916]">{c.address || c.id}</td>
                        <td className="px-3 py-2 text-right font-medium tabular-nums text-[#1a1916]">{fmtPrice(c.sale_price)}</td>
                        <td className="px-3 py-2 text-right text-[#5a5854] whitespace-nowrap">{fmtDate(c.sale_date)}</td>
                        <td className="px-3 py-2 text-right text-[#5a5854]">{c.meta || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Ajustements */}
          {adjustments.length > 0 && (
            <Section title="5. Ajustements appliqu&eacute;s">
              <div className="rounded-[8px] overflow-hidden border border-black/[.06]">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="bg-black/[.025]">
                      <th className="text-left px-3 py-2 font-medium text-[#5a5854]">Comparable</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Prix vente</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Adj. surface</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Adj. ann&eacute;e</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Adj. &eacute;tat</th>
                      <th className="text-right px-3 py-2 font-medium text-[#5a5854]">Ajust&eacute;</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adjustments.map((a, i) => (
                      <tr key={a.id} className={i % 2 === 0 ? '' : 'bg-black/[.018]'}>
                        <td className="px-3 py-2 text-[#1a1916]">{a.comparableLabel}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-[#5a5854]">{fmtPrice(a.salePrice)}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-[#5a5854]">{a.surface_adj > 0 ? '+' : ''}{fmtPrice(a.surface_adj)}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-[#5a5854]">{a.year_adj > 0 ? '+' : ''}{fmtPrice(a.year_adj)}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-[#5a5854]">{a.condition_adj > 0 ? '+' : ''}{fmtPrice(a.condition_adj)}</td>
                        <td className="px-3 py-2 text-right tabular-nums font-medium text-[#1a1916]">{fmtPrice(a.adjusted)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Conformité */}
          <Section title="6. Conformit&eacute; et avertissements">
            {blockingFailures.length > 0 ? (
              <div className="rounded-[8px] bg-red-50/80 border border-red-200/60 px-3 py-2 mb-2">
                <div className="text-[11px] font-medium text-red-700 mb-1">
                  {blockingFailures.length} blocage{blockingFailures.length > 1 ? 's' : ''}
                </div>
                <ul className="text-[11px] text-red-600 list-disc list-inside space-y-0.5">
                  {blockingFailures.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            ) : (
              <div className="rounded-[8px] bg-emerald-50/80 border border-emerald-200/60 px-3 py-2 mb-2 text-[11px] text-emerald-800">
                Aucun blocage de conformit&eacute; d&eacute;tect&eacute;.
              </div>
            )}
            {warnings.length > 0 && (
              <div className="rounded-[8px] bg-amber-50/60 border border-amber-200/50 px-3 py-2 text-[11px] text-amber-800">
                <div className="font-medium mb-1">{warnings.length} avertissement{warnings.length > 1 ? 's' : ''}</div>
                <ul className="list-disc list-inside space-y-0.5">
                  {warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}
          </Section>

          {/* Mention légale */}
          <div className="pt-3 border-t border-black/[.06] text-[10px] text-[#b5b2ac] leading-relaxed">
            Ce document est un brouillon produit par un assistant IA &agrave; titre d&rsquo;aide &agrave; la r&eacute;daction.
            Il ne constitue pas un rapport d&rsquo;&eacute;valuation certifi&eacute; au sens des normes professionnelles applicables
            et ne peut &ecirc;tre utilis&eacute; &agrave; des fins de transaction, de financement ou de litige sans validation
            et signature d&rsquo;un &eacute;valuateur agr&eacute;&eacute; autoris&eacute;.
          </div>
        </div>
      </div>
    </div>
  )
}
