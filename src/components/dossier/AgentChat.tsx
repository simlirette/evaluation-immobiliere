'use client'

import { useState } from 'react'
import type { TabId } from '@/types'

const STAGE_SUGGESTIONS: Record<TabId, string[]> = {
  dossier:  ['Enrichir les données', 'Vérifier les infos', 'Résumer le mandat'],
  marche:   ['Trouver des comparables', 'Analyser les ajustements', 'Valider la grille'],
  analyse:  ['Peser les approches', 'Justifier la pondération', 'Vérifier la cohérence'],
  synthese: ['Rédiger la conclusion', 'Vérifier la conformité', 'Préparer la signature'],
  rapport:  ['Générer le rapport', 'Vérifier les sections', 'Exporter en PDF'],
}

const STAGE_PLACEHOLDERS: Record<TabId, string> = {
  dossier:  'Demandez à l\'agent d\'enrichir le dossier…',
  marche:   'Demandez des comparables ou des ajustements…',
  analyse:  'Demandez une analyse des approches…',
  synthese: 'Demandez de rédiger la conclusion…',
  rapport:  'Demandez de générer ou vérifier le rapport…',
}

interface Props {
  activeTab: TabId
  sidebarOpen?: boolean
}

export default function AgentChat({ activeTab, sidebarOpen = false }: Props) {
  const [input, setInput] = useState('')
  const suggestions = STAGE_SUGGESTIONS[activeTab] ?? []
  const placeholder = STAGE_PLACEHOLDERS[activeTab] ?? 'Demandez à l\'agent…'

  function handleSend() {
    if (!input.trim()) return
    setInput('')
    // TODO: wire to agent API
  }

  return (
    <div className={`agent-chat-wrap ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="agent-chat-gradient" />
      <div className="agent-chat-inner">
        <div className="agent-chat-box">
          {/* Suggestions */}
          <div
            className="flex items-center gap-2 px-4 py-2.5 overflow-x-auto"
            style={{ borderBottom: '1px solid var(--rule-soft)' }}
          >
            <svg
              width="14" height="14" viewBox="0 0 14 14" fill="none"
              aria-hidden="true"
              style={{ color: 'var(--ochre)', flexShrink: 0 }}
            >
              <path
                d="M7 1l1.5 4h4l-3.2 2.3 1.2 4L7 9l-3.5 2.3 1.2-4L1.5 5h4z"
                stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"
              />
            </svg>
            {suggestions.map(s => (
              <button
                key={s}
                onClick={() => setInput(s)}
                className="flex-shrink-0 text-[12.5px] px-3 py-1 border-none cursor-pointer transition-colors"
                style={{
                  borderRadius: 'var(--r-pill)',
                  background: 'var(--paper-2)',
                  color: 'var(--ink-3)',
                  fontFamily: 'var(--font-sans)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-3)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--paper-2)')}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input row */}
          <div className="flex items-center gap-2 px-3 py-2.5">
            <button
              className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full border-none bg-transparent cursor-pointer transition-colors"
              aria-label="Joindre un fichier"
              style={{ color: 'var(--ink-faint)' }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--paper-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path
                  d="M13 7l-5.5 5.5a3.5 3.5 0 01-5-5l6-6a2 2 0 013 3L5 11a.5.5 0 01-.7-.7l5.5-5.5"
                  stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"
                />
              </svg>
            </button>

            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={placeholder}
              className="flex-1 text-[14px] bg-transparent border-none focus:outline-none"
              style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}
            />

            <button
              onClick={handleSend}
              disabled={!input.trim()}
              aria-label="Envoyer"
              className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full border-none cursor-pointer transition-colors"
              style={{
                background: input.trim() ? 'var(--ink)' : 'var(--paper-2)',
                color: input.trim() ? 'var(--paper-hi)' : 'var(--ink-faint)',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path
                  d="M2 7h10M8 3l4 4-4 4"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
