'use client'

import { useEffect, useState, useCallback } from 'react'
import { loadVersions, renameVersion, type RapportVersion } from '@/lib/rapport-versions'

interface Props {
  sessionId: string
  onRestore: (content: string) => void
}

function timeAgo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "À l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `il y a ${hrs}h`
  return new Date(isoDate).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })
}

export default function RapportVersionHistory({ sessionId, onRestore }: Props) {
  const [versions, setVersions] = useState<RapportVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const v = await loadVersions(sessionId)
      setVersions(v)
    } catch {
      // Supabase non configuré ou erreur réseau — afficher vide
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => { load() }, [load])

  async function handleRename(id: string) {
    if (!renameValue.trim()) {
      setRenamingId(null)
      return
    }
    const newLabel = renameValue.trim()
    // Optimistic update
    setVersions(prev => prev.map(v => v.id === id ? { ...v, label: newLabel } : v))
    setRenamingId(null)
    try {
      await renameVersion(id, newLabel)
    } catch {
      // Revert on failure
      load()
    }
  }

  if (loading) {
    return <div className="px-4 py-3 text-[11px] text-[#b5b2ac]">Chargement…</div>
  }

  if (versions.length === 0) {
    return <div className="px-4 py-3 text-[11px] text-[#b5b2ac]">Aucune version sauvegardée.</div>
  }

  return (
    <div className="flex flex-col">
      {versions.map(v => (
        <div
          key={v.id}
          className="flex items-center gap-2 px-4 py-2 hover:bg-black/[.03] group border-b border-black/[.04] last:border-0"
        >
          <div className="flex flex-col flex-1 min-w-0">
            {renamingId === v.id ? (
              <input
                autoFocus
                value={renameValue}
                onChange={e => setRenameValue(e.target.value)}
                onBlur={() => handleRename(v.id)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleRename(v.id)
                  if (e.key === 'Escape') setRenamingId(null)
                }}
                className="text-[12px] text-[#1a1916] bg-transparent border-b border-[#334155] outline-none w-full pb-0.5"
              />
            ) : (
              <span className="text-[12px] text-[#1a1916] truncate">{v.label}</span>
            )}
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-[10px] text-[#b5b2ac]">{timeAgo(v.created_at)}</span>
              {v.is_initial && (
                <span className="text-[9px] bg-[#1f7a5c]/10 text-[#1f7a5c] rounded px-1 py-0.5 font-medium">
                  initiale
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
            <button
              type="button"
              onClick={() => { setRenamingId(v.id); setRenameValue(v.label) }}
              className="text-[10px] text-[#b5b2ac] hover:text-[#5a5854] px-1.5 py-1 rounded"
              title="Renommer"
            >
              ✎
            </button>
            <button
              type="button"
              onClick={() => onRestore(v.content)}
              className="text-[10px] bg-[#334155] text-white rounded-full px-2.5 py-1 hover:bg-[#1e293b] transition-colors"
            >
              Restaurer
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
