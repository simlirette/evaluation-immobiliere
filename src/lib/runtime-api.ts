import type { Adjustment, Comparable, Document, Dossier, FactChip } from '@/types'

const BFF_BASE = '/api/runtime'

export interface AppState {
  schema_version: string
  status: string
  active_session_id: string
  dossiers: Dossier[]
  active: null | {
    dossier: Dossier
    documents: Document[]
    fact_chips: FactChip[]
    comparables: Comparable[]
    adjustments: Adjustment[]
    valuation: {
      values: Record<string, number>
      conclusion: { value?: number; status?: string }
      conclusion_label: string
      status: string
    }
    compliance: {
      status?: string
      blocking_failures?: string[]
      warnings?: string[]
    }
    report: {
      available: boolean
      preview: string
      title: string
      subtitle: string
    }
    workflow: {
      status: string
      can_validate_review: boolean
      can_generate_package: boolean
      steps: Array<{ id: string; label: string; status: string; complete: boolean }>
    }
    assistant: {
      agents?: Array<{ agent: string; label: string; status: string; focus: string }>
      transcript?: { messages_count?: number; latest_agent_label?: string }
    }
    package: {
      status: string
      manifest?: Record<string, unknown>
      files?: string[]
    }
  }
}

export interface CreateRuntimeDossierInput {
  address: string
  property_type: string
  neighborhood: string
}

interface RuntimeMessageResponse {
  message: {
    agent: string
    agent_label: string
    answer: string
  }
  state: AppState
}

async function runtimeJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BFF_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  })

  if (!response.ok) {
    let detail = ''
    try {
      const payload = await response.json()
      detail = payload?.error ? `: ${payload.error}` : ''
    } catch {
      detail = ''
    }
    throw new Error(`Runtime API ${response.status}${detail}`)
  }

  return response.json() as Promise<T>
}

export function fetchAppState(sessionId?: string | null): Promise<AppState> {
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''
  return runtimeJson<AppState>(`/app/state${query}`)
}

export async function fetchRuntimeDossiers(): Promise<Dossier[]> {
  const state = await fetchAppState()
  return state.dossiers ?? []
}

export async function fetchRuntimeDossier(sessionId: string): Promise<Dossier | null> {
  const state = await fetchAppState(sessionId)
  return state.active?.dossier ?? null
}

export async function createRuntimeDossier(input: CreateRuntimeDossierInput): Promise<Dossier> {
  const payload = await runtimeJson<{ state: AppState }>('/app/demo', {
    method: 'POST',
    body: JSON.stringify({
      fixture: 'case_pilote_residentiel_standard.json',
      display_name: input.address,
      property_type: input.property_type,
      neighborhood: input.neighborhood,
    }),
  })
  const dossier = payload.state.active?.dossier
  if (!dossier) throw new Error('Aucun dossier runtime cree')
  return dossier
}

export async function deleteRuntimeDossier(_sessionId: string): Promise<void> {
  // Les sessions runtime sont des traces auditables. On les masque cote UI plus tard,
  // mais on ne les supprime pas via l'interface locale.
}

export async function toggleRuntimePin(_sessionId: string, _pinned: boolean): Promise<void> {
  // Epingle purement locale non persistante pour l'instant.
}

export async function fetchRuntimeDocuments(sessionId: string): Promise<Document[]> {
  const state = await fetchAppState(sessionId)
  return state.active?.documents ?? []
}

export async function uploadRuntimeDocument(_sessionId: string, file: File): Promise<Document> {
  return {
    id: `local-${Date.now()}`,
    name: file.name,
    filename: file.name,
    sizeLabel: file.size ? `${Math.max(1, Math.round(file.size / 1024))} KB` : '',
  }
}

export async function fetchRuntimeFacts(sessionId: string): Promise<FactChip[]> {
  const state = await fetchAppState(sessionId)
  return state.active?.fact_chips ?? []
}

export async function fetchRuntimeComparables(sessionId: string): Promise<Comparable[]> {
  const state = await fetchAppState(sessionId)
  return state.active?.comparables ?? []
}

export async function fetchRuntimeAdjustments(sessionId: string): Promise<Adjustment[]> {
  const state = await fetchAppState(sessionId)
  return state.active?.adjustments ?? []
}

export async function fetchRuntimeReport(sessionId: string) {
  const state = await fetchAppState(sessionId)
  return state.active?.report ?? null
}

export async function fetchRuntimeWorkflow(sessionId: string) {
  const state = await fetchAppState(sessionId)
  return state.active?.workflow ?? null
}

export async function sendRuntimeMessage(
  sessionId: string,
  message: string,
  agent = 'auto',
): Promise<RuntimeMessageResponse> {
  return runtimeJson<RuntimeMessageResponse>('/app/message', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message, agent }),
  })
}

export async function validateRuntimeReview(sessionId: string): Promise<AppState> {
  const payload = await runtimeJson<{ state: AppState }>('/app/review/validate', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  })
  return payload.state
}

export async function generateRuntimePackage(sessionId: string): Promise<AppState> {
  const payload = await runtimeJson<{ state: AppState }>('/app/package', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  })
  return payload.state
}
