'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { streamRuntimeMessage, fetchRuntimeTranscript } from '@/lib/runtime-api'
import type { AppState, HistoryEntry } from '@/lib/runtime-api'

export interface ChatReply {
  agent: string
  agentLabel: string
  text: string
  userMessage?: string   // the question that prompted this reply
  streaming?: boolean
}

export function useAgentChat(sessionId: string | null, defaultAgent = 'auto') {
  const [replies, setReplies] = useState<ChatReply[]>([])
  const [asking, setAsking] = useState(false)
  const [lastState, setLastState] = useState<AppState | null>(null)
  const [transcriptLoaded, setTranscriptLoaded] = useState(false)
  // Stable ref to current replies for history building (avoids stale closure)
  const repliesRef = useRef<ChatReply[]>([])
  repliesRef.current = replies

  // Load persisted transcript on mount (restores history across tab switches)
  useEffect(() => {
    if (!sessionId || transcriptLoaded) return
    setTranscriptLoaded(true)
    fetchRuntimeTranscript(sessionId, defaultAgent === 'auto' ? undefined : defaultAgent)
      .then(exchanges => {
        if (exchanges.length === 0) return
        const restored: ChatReply[] = exchanges.map(ex => ({
          agent: ex.agent,
          agentLabel: ex.agent_label,
          text: ex.answer,
          userMessage: ex.user,
          streaming: false,
        }))
        setReplies(restored)
      })
      .catch(() => { /* transcript optional — silently ignore */ })
  }, [sessionId, defaultAgent, transcriptLoaded])

  const ask = useCallback(
    async (message: string, agent = defaultAgent) => {
      if (!sessionId || !message.trim() || asking) return
      setAsking(true)

      // Build history from completed (non-streaming) prior turns
      const history: HistoryEntry[] = []
      for (const r of repliesRef.current) {
        if (!r.streaming && r.text) {
          if (r.userMessage) history.push({ role: 'user', content: r.userMessage })
          history.push({ role: 'assistant', content: r.text })
        }
      }

      // Streaming placeholder appended immediately
      setReplies(prev => [...prev, { agent, agentLabel: '…', text: '', userMessage: message, streaming: true }])

      try {
        const response = await streamRuntimeMessage(
          sessionId,
          message,
          agent,
          (token) => {
            setReplies(prev => {
              const next = [...prev]
              const last = next[next.length - 1]
              if (last?.streaming) {
                next[next.length - 1] = { ...last, text: last.text + token }
              }
              return next
            })
          },
          history,
        )

        // Replace placeholder with final confirmed reply
        setReplies(prev => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.streaming) {
            next[next.length - 1] = {
              agent: response.message.agent,
              agentLabel: response.message.agent_label,
              text: response.message.answer,
              userMessage: message,
              streaming: false,
            }
          }
          return next
        })
        setLastState(response.state)
      } catch {
        setReplies(prev => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.streaming) {
            next[next.length - 1] = {
              ...last,
              text: last.text || 'Erreur — impossible de contacter le runtime.',
              streaming: false,
            }
          }
          return next
        })
      } finally {
        setAsking(false)
      }
    },
    [sessionId, defaultAgent, asking],
  )

  return { replies, asking, ask, lastState }
}
