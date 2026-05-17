import type { Adjustment, Comparable, Document, Dossier, Enrichment, FactChip } from '@/types'

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
    mandat: {
      mandat_type: string
      format_rapport: string
      methodes_requises: string[]
      methode_preponderante: string
    } | null
    conflit: {
      detecte: boolean
      motif: string
    } | null
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
    enrichment: Enrichment | null
  }
}

export interface CreateRuntimeDossierInput {
  address: string
  property_type: string
  neighborhood: string
  commanditaire?: {
    nom: string
    organisation: string
    fin_evaluation: string
  }
  comparables?: import('@/types').ComparableInput[]
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
  // archived filtered server-side; pinned comes from backend record
  return (state.dossiers ?? [])
    .sort((a, b) => Number(b.pinned) - Number(a.pinned))
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
      ...(input.commanditaire ? { commanditaire: input.commanditaire } : {}),
      ...(input.comparables && input.comparables.length > 0 ? { comparables: input.comparables } : {}),
    }),
  })
  const dossier = payload.state.active?.dossier
  if (!dossier) throw new Error('Aucun dossier runtime cree')
  return dossier
}


export function deleteRuntimeDossier(sessionId: string): Promise<void> {
  return runtimeJson('/app/archive', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  }).then(() => undefined)
}

export function toggleRuntimePin(sessionId: string, currentlyPinned: boolean): Promise<void> {
  return runtimeJson('/app/pin', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, pinned: !currentlyPinned }),
  }).then(() => undefined)
}

export async function fetchRuntimeDocuments(sessionId: string): Promise<Document[]> {
  const state = await fetchAppState(sessionId)
  return state.active?.documents ?? []
}

const UPLOAD_MAX_BYTES = 10 * 1024 * 1024 // 10 MB
const UPLOAD_ALLOWED_TYPES = new Set(['application/pdf', 'image/jpeg', 'image/png'])

export async function uploadRuntimeDocument(sessionId: string, file: File): Promise<Document> {
  if (!UPLOAD_ALLOWED_TYPES.has(file.type)) {
    throw new Error('Type non autorisé. PDF, JPG ou PNG uniquement.')
  }
  if (file.size > UPLOAD_MAX_BYTES) {
    throw new Error('Fichier trop volumineux (maximum 10 Mo).')
  }

  const content_b64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1]) // strip data URL prefix
    }
    reader.onerror = () => reject(new Error('Lecture du fichier échouée.'))
    reader.readAsDataURL(file)
  })

  return runtimeJson<Document>('/app/upload', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      filename: file.name,
      mime_type: file.type,
      content_b64,
    }),
  })
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

export async function saveRapport(sessionId: string, content: string): Promise<void> {
  await runtimeJson<{ ok: boolean }>('/app/report', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, content }),
  })
}

export async function generateRapport(
  sessionId: string,
  format: 'abrege' | 'complet'
): Promise<string> {
  const result = await runtimeJson<{ ok: boolean; content: string }>('/app/report/generate', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, format }),
  })
  return result.content
}

export async function fetchRuntimeEnrichment(sessionId: string): Promise<Enrichment | null> {
  const state = await fetchAppState(sessionId)
  return state.active?.enrichment ?? null
}

export async function exportRapport(
  sessionId: string,
  format: 'docx' | 'html'
): Promise<{ filename: string; blob: Blob }> {
  const result = await runtimeJson<{
    ok: boolean
    content_type: string
    filename: string
    data: string
  }>('/app/report/export', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, format }),
  })

  let blob: Blob
  if (format === 'docx') {
    // data is base64 — decode to bytes
    const binary = atob(result.data)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    blob = new Blob([bytes], { type: result.content_type })
  } else {
    blob = new Blob([result.data], { type: result.content_type })
  }

  return { filename: result.filename, blob }
}
