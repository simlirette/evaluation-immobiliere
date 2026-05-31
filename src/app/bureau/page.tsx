'use client'

import { useEffect, useState } from 'react'

interface BureauStats {
  total: number
  by_status: Record<string, number>
  by_evaluateur: Array<{ evaluateur_id: string; count: number; statuts: Record<string, number> }>
}

interface BureauUsage {
  llm_calls: number
  llm_tokens_in: number
  llm_tokens_out: number
  llm_cost_usd: number
  by_evaluateur: Array<{ evaluateur_id: string; llm_calls: number; llm_cost_usd: number }>
}

interface DashboardData {
  bureau_id: string
  sessions: Array<Record<string, unknown>>
  stats: BureauStats
  usage: BureauUsage
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex flex-col gap-1 px-4 py-3 rounded-[10px]"
      style={{ border: '1px solid var(--rule)', background: 'var(--paper-hi)' }}>
      <span className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--ink-mute)' }}>{label}</span>
      <span className="text-[20px] font-semibold" style={{ color: 'var(--ink)' }}>{value}</span>
      {sub && <span className="text-[11px]" style={{ color: 'var(--ink-faint)' }}>{sub}</span>}
    </div>
  )
}

export default function BureauDashboardPage() {
  const [bureauId, setBureauId] = useState('')
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load(id: string) {
    if (!id.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/runtime/bureau/dashboard?bureau_id=${encodeURIComponent(id)}&limit=50`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const stats = data?.stats
  const usage = data?.usage

  return (
    <div className="min-h-screen p-8" style={{ background: 'var(--paper)', color: 'var(--ink)' }}>
      <div className="max-w-[900px] mx-auto flex flex-col gap-6">

        {/* Header */}
        <div>
          <div className="eyebrow">Tableau de bord</div>
          <h1 className="text-[24px] font-semibold mt-1">Bureau directeur</h1>
        </div>

        {/* Bureau ID input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={bureauId}
            onChange={e => setBureauId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && load(bureauId)}
            placeholder="Bureau ID (ex. bureau-uuid-xxxx)"
            className="flex-1 rounded-[8px] px-3 py-2 text-[13px] focus:outline-none focus:ring-1"
            style={{ border: '1px solid var(--rule)', background: 'var(--paper)', color: 'var(--ink)' }}
          />
          <button
            onClick={() => load(bureauId)}
            disabled={loading}
            className="btn accent px-4 text-[13px] disabled:opacity-40"
          >
            {loading ? 'Chargement…' : 'Charger'}
          </button>
        </div>

        {error && (
          <p className="text-[13px]" style={{ color: 'var(--oxblood)' }}>{error}</p>
        )}

        {data && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatCard label="Dossiers" value={String(stats?.total ?? 0)} />
              <StatCard
                label="Complétés"
                value={String(stats?.by_status?.['PRET_REVISION_FINALE'] ?? 0)}
              />
              <StatCard
                label="Appels LLM"
                value={String(usage?.llm_calls ?? 0)}
                sub={`${usage?.llm_tokens_in ? Math.round((usage.llm_tokens_in + (usage.llm_tokens_out || 0)) / 1000) : 0}k tokens`}
              />
              <StatCard
                label="Coût LLM"
                value={`$${(usage?.llm_cost_usd ?? 0).toFixed(3)}`}
                sub="total bureau"
              />
            </div>

            {/* Par évaluateur */}
            {stats?.by_evaluateur && stats.by_evaluateur.length > 0 && (
              <div className="flex flex-col gap-2">
                <h2 className="text-[14px] font-semibold">Par évaluateur</h2>
                <div className="rounded-[10px] overflow-hidden" style={{ border: '1px solid var(--rule)' }}>
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr style={{ background: 'var(--paper-2)' }}>
                        <th className="text-left px-3 py-2 font-medium" style={{ color: 'var(--ink-mute)' }}>Évaluateur</th>
                        <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--ink-mute)' }}>Dossiers</th>
                        <th className="text-right px-3 py-2 font-medium" style={{ color: 'var(--ink-mute)' }}>Coût LLM</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.by_evaluateur.map((ev, i) => {
                        const evUsage = usage?.by_evaluateur?.find(u => u.evaluateur_id === ev.evaluateur_id)
                        return (
                          <tr key={i} style={{ borderTop: '1px solid var(--rule)' }}>
                            <td className="px-3 py-2 font-mono text-[11px]" style={{ color: 'var(--ink)' }}>
                              {ev.evaluateur_id.slice(0, 12)}…
                            </td>
                            <td className="text-right px-3 py-2">{ev.count}</td>
                            <td className="text-right px-3 py-2">${(evUsage?.llm_cost_usd ?? 0).toFixed(3)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Dossiers récents */}
            {data.sessions.length > 0 && (
              <div className="flex flex-col gap-2">
                <h2 className="text-[14px] font-semibold">Dossiers récents ({data.sessions.length})</h2>
                <div className="flex flex-col gap-1.5">
                  {data.sessions.slice(0, 10).map((s, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 rounded-[8px]"
                      style={{ border: '1px solid var(--rule)', background: 'var(--paper-hi)' }}>
                      <div>
                        <span className="text-[12px] font-medium">{String(s.dossier_id || s.session_id || '—')}</span>
                        <span className="ml-2 text-[11px]" style={{ color: 'var(--ink-mute)' }}>{String(s.address || '')}</span>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded-full"
                        style={{
                          background: String(s.status).includes('COMPLET') || String(s.status) === 'PRET_REVISION_FINALE'
                            ? 'rgba(74,107,84,.1)' : 'rgba(0,0,0,.04)',
                          color: String(s.status).includes('COMPLET') || String(s.status) === 'PRET_REVISION_FINALE'
                            ? 'var(--verdigris)' : 'var(--ink-mute)',
                        }}>
                        {String(s.status || '—').replace(/_/g, ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
