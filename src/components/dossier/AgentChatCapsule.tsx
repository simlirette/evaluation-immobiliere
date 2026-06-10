'use client'

/* Capsule agent — composer persistant du design handoff (dossier.jsx →
   AgentChat) branché sur le streaming réel (useAgentChat). Les réponses
   s'affichent dans un tiroir au-dessus de la capsule (extension fonctionnelle
   du design, qui ne prévoyait pas de zone de conversation). */

import { useState, useRef, useEffect } from 'react'
import { Icon } from '@/components/shared/Icon'
import TypingDots from '@/components/shared/TypingDots'
import { useAgentChat } from '@/hooks/useAgentChat'
import type { TabId } from '@/types'

const STAGE_PROMPTS: Record<TabId, string> = {
  dossier:  "Demander à l'agent — vérifier les caractéristiques, suggérer des documents manquants…",
  marche:   "Demander à l'agent — trouver d'autres comparables, ajuster pour superficie ou état…",
  analyse:  "Demander à l'agent — proposer une pondération, valider les approches…",
  synthese: "Demander à l'agent — rédiger le narratif, vérifier l'attestation…",
  rapport:  "Demander à l'agent — relire le rapport, suggérer des corrections…",
}

const STAGE_SUGGESTIONS: Record<TabId, string[]> = {
  dossier:  ['Photos manquantes ?', 'Vérifier le cadastre', 'Importer le rôle'],
  marche:   ['Élargir le rayon à 1,5 km', "Ajuster pour l'année", 'Comparables sur 24 mois'],
  analyse:  ['Pondération recommandée ?', 'Comparer aux ventes récentes', "Justifier l'écart coût/marché"],
  synthese: ['Rédiger un narratif', 'Vérifier la fourchette', "Préparer l'attestation"],
  rapport:  ['Aperçu PDF', 'Vérifier la mise en page', 'Annexes manquantes ?'],
}

const STAGE_AGENTS: Record<TabId, string> = {
  dossier:  'data-facts',
  marche:   'comps-market',
  analyse:  'valuation-draft',
  synthese: 'auto',
  rapport:  'redaction',
}

interface Props {
  dossierId: string | null
  stage: TabId
}

export default function AgentChatCapsule({ dossierId, stage }: Props) {
  const [value, setValue] = useState('')
  const [open, setOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const drawerRef = useRef<HTMLDivElement>(null)
  const { replies, asking, ask } = useAgentChat(dossierId, STAGE_AGENTS[stage])

  // Ouvre le tiroir seulement quand l'utilisateur envoie (asking) — pas au
  // mount quand le transcript historique est restauré.
  useEffect(() => {
    if (asking) setOpen(true)
  }, [asking])

  useEffect(() => {
    drawerRef.current?.scrollTo({ top: drawerRef.current.scrollHeight, behavior: 'smooth' })
  }, [replies, asking])

  function pick(s: string) {
    setValue(s)
    inputRef.current?.focus()
  }

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const text = value.trim()
    if (!text || asking) return
    setValue('')
    ask(text)
  }

  return (
    <div className="agent-chat-wrap">
      <div style={{ pointerEvents: 'auto', width: '100%', maxWidth: 760 }}>
        {open && (replies.length > 0 || asking) && (
          <div
            ref={drawerRef}
            style={{
              background: 'var(--paper-hi)',
              border: '1px solid var(--rule)',
              borderRadius: 'var(--r-lg)',
              boxShadow: 'var(--shadow-float)',
              padding: '14px 18px',
              marginBottom: 10,
              maxHeight: '40vh',
              overflowY: 'auto',
            }}
          >
            <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
              <span className="eyebrow">Agent</span>
              <button
                type="button"
                className="btn ghost btn-sm"
                onClick={() => setOpen(false)}
              >
                Réduire
              </button>
            </div>
            {replies.map((r, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                {r.userMessage && (
                  <div className="text-[13px] font-medium" style={{ color: 'var(--ink)', marginBottom: 4 }}>
                    {r.userMessage}
                  </div>
                )}
                <pre
                  className="whitespace-pre-wrap"
                  style={{ fontFamily: 'var(--sans)', fontSize: 13, lineHeight: 1.55, color: 'var(--ink-2)', margin: 0 }}
                >
                  {r.text}
                  {r.streaming && <span style={{ color: 'var(--ink-faint)' }} className="animate-pulse">▊</span>}
                </pre>
              </div>
            ))}
            {asking && replies.length === 0 && <TypingDots />}
          </div>
        )}

        <div className="agent-chat">
          <div className="agent-suggestions">
            <span className="agent-sparkle"><Icon.Sparkle/></span>
            {STAGE_SUGGESTIONS[stage].map((s, i) => (
              <button key={i} type="button" className="suggestion" onClick={() => pick(s)}>{s}</button>
            ))}
            {!open && replies.length > 0 && (
              <button
                type="button"
                className="suggestion"
                style={{ marginLeft: 'auto' }}
                onClick={() => setOpen(true)}
              >
                Conversation ({replies.length})
              </button>
            )}
          </div>
          <form className="agent-input" onSubmit={submit}>
            <button type="button" className="attach" aria-label="Joindre un fichier" title="Joindre une pièce jointe">
              <Icon.Paperclip/>
            </button>
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={e => setValue(e.target.value)}
              placeholder={STAGE_PROMPTS[stage]}
            />
            <button type="submit" className={`send ${value.trim() ? 'ready' : ''}`} aria-label="Envoyer" disabled={asking}>
              <Icon.Send/>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
