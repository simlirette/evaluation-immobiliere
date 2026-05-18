'use client'

import { useState, useCallback } from 'react'
import { streamRuntimeMessage } from '@/lib/runtime-api'
import type { AppState } from '@/lib/runtime-api'

export interface ChatReply {
  agent: string
  agentLabel: string
  text: string
  streaming?: boolean
}

export function useAgentChat(sessionId: string | null, defaultAgent = 'auto') {
  const [replies, setReplies] = useState<ChatReply[]>([])
  const [asking, setAsking] = useState(false)
  const [lastState, setLastState] = useState<AppState | null>(null)

  const ask = useCallback(
    async (message: string, agent = defaultAgent) => {
      if (!sessionId || !message.trim() || asking) return
      setAsking(true)

      // Streaming placeholder appended immediately
      setReplies(prev => [...prev, { agent, agentLabel: '…', text: '', streaming: true }])

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
