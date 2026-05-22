import type { Adjustment, Comparable, Document, Dossier, Enrichment, FactChip } from '@/types'

const BFF_BASE = '/api/runtime'

export interface CertifiabilityGate {
  ok: boolean
  status?: string
  blocking_errors?: string[]
  blocking_messages?: string[]
  blocking_errors_count?: number
  actual_review_decision?: string
  integrity_ok?: boolean
  compliance_status?: string
  compliance_blocking_failures_count?: number
  comparative_input_count?: number
  comparative_value?: number | null
  report_available?: boolean
}

export interface AppState {
  schema_version: string
  status: string
  active_session_id: string
  dossiers: Dossier[]
  active: null | {
    dossier: Dossier
    documents: Document[]
    fact_chips: FactChip[]
    commanditaire: {
      nom: string
      organisation: string
      fin_evaluation: string
    } | null
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
      certifiability_gate?: CertifiabilityGate
    }
    workflow: {
      status: string
      can_validate_review: boolean
      can_generate_package: boolean
      steps: Array<{ id: string; label: string; status: string; complete: boolean }>
      certifiability_gate?: CertifiabilityGate
      package_gate?: CertifiabilityGate
      blocking_messages?: string[]
    }
    pipeline_progress: {
      steps: string[]
      completed: string[]
      running: string | null
      waiting_checkpoint: number | null
    } | null
    pipeline_error?: string | null
    ingestion_error?: string | null
    assistant: {
      agents?: Array<{ agent: string; label: string; status: string; focus: string }>
      transcript?: { messages_count?: number; latest_agent_label?: string }
    }
    package: {
      status: string
      manifest?: Record<string, unknown>
      files?: string[]
      gate?: CertifiabilityGate
    }
    enrichment: Enrichment | null
  }
}

export interface CreateRuntimeDossierInput {
  address: string
  property_type: string
  neighborhood: string
  mandat_type?: string
  date_reference?: string
  superficie_habitable?: number | null
  superficie_terrain?: number | null
  annee_construction?: number | null
  nb_chambres?: number | null
  commanditaire?: {
    nom: string
    organisation: string
    fin_evaluation: string
  }
  comparables?: import('@/types').ComparableInput[]
  // S7 — lettre de mandat
  honoraires?: string
  date_livraison?: string
  nom_evaluateur?: string
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
  const payload = await runtimeJson<{ state: AppState }>('/app/create', {
    method: 'POST',
    body: JSON.stringify({
      address: input.address,
      property_type: input.property_type,
      neighborhood: input.neighborhood,
      ...(input.mandat_type ? { mandat_type: input.mandat_type } : {}),
      ...(input.date_reference ? { date_reference: input.date_reference } : {}),
      ...(input.superficie_habitable != null ? { superficie_habitable: input.superficie_habitable } : {}),
      ...(input.superficie_terrain != null ? { superficie_terrain: input.superficie_terrain } : {}),
      ...(input.annee_construction != null ? { annee_construction: input.annee_construction } : {}),
      ...(input.nb_chambres != null ? { nb_chambres: input.nb_chambres } : {}),
      ...(input.commanditaire ? { commanditaire: input.commanditaire } : {}),
      ...(input.comparables && input.comparables.length > 0 ? { comparables: input.comparables } : {}),
      ...(input.honoraires ? { honoraires: input.honoraires } : {}),
      ...(input.date_livraison ? { date_livraison: input.date_livraison } : {}),
      ...(input.nom_evaluateur ? { nom_evaluateur: input.nom_evaluateur } : {}),
    }),
  })
  const dossier = payload.state.active?.dossier
  if (!dossier) throw new Error('Aucun dossier runtime cree')
  return dossier
}

export function renameRuntimeDossier(sessionId: string, address: string): Promise<void> {
  return runtimeJson('/app/rename', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, address }),
  }).then(() => undefined)
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
const UPLOAD_EXTENSIONS_BY_TYPE: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
}

function assertUploadFilename(file: File) {
  if (file.name.includes('/') || file.name.includes('\\')) {
    throw new Error('Nom de fichier invalide.')
  }
  const lower = file.name.toLowerCase()
  const allowed = UPLOAD_EXTENSIONS_BY_TYPE[file.type] ?? []
  if (!allowed.some(ext => lower.endsWith(ext))) {
    throw new Error('Extension de fichier incompatible avec le type déclaré.')
  }
}

async function assertUploadSignature(file: File) {
  const head = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  if (head.length === 0) throw new Error('Fichier vide.')
  if (file.type === 'application/pdf') {
    const pdf = [0x25, 0x50, 0x44, 0x46, 0x2d]
    if (!pdf.every((byte, i) => head[i] === byte)) throw new Error('Fichier PDF invalide.')
  } else if (file.type === 'image/jpeg') {
    if (head[0] !== 0xff || head[1] !== 0xd8) throw new Error('Image JPEG invalide.')
  } else if (file.type === 'image/png') {
    const png = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]
    if (!png.every((byte, i) => head[i] === byte)) throw new Error('Image PNG invalide.')
  }
}

export async function uploadRuntimeDocument(sessionId: string, file: File): Promise<Document> {
  if (!UPLOAD_ALLOWED_TYPES.has(file.type)) {
    throw new Error('Type non autorisé. PDF, JPG ou PNG uniquement.')
  }
  assertUploadFilename(file)
  if (file.size > UPLOAD_MAX_BYTES) {
    throw new Error('Fichier trop volumineux (maximum 10 Mo).')
  }
  await assertUploadSignature(file)

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

export interface HistoryEntry {
  role: 'user' | 'assistant'
  content: string
}

export async function streamRuntimeMessage(
  sessionId: string,
  message: string,
  agent: string,
  onToken: (token: string) => void,
  history?: HistoryEntry[],
): Promise<RuntimeMessageResponse> {
  const response = await fetch(`${BFF_BASE}/app/message/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message, agent, history: history ?? [] }),
    cache: 'no-store',
  })

  if (!response.ok) {
    let detail = ''
    try {
      const payload = await response.json()
      detail = payload?.error ? `: ${payload.error}` : ''
    } catch { detail = '' }
    throw new Error(`Runtime API ${response.status}${detail}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result: RuntimeMessageResponse | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const event = JSON.parse(line.slice(6)) as Record<string, unknown>
        if (typeof event.token === 'string') {
          onToken(event.token)
        } else if (event.done && event.message) {
          result = { message: event.message, state: event.state } as RuntimeMessageResponse
        }
      } catch { /* ignore malformed lines */ }
    }
  }

  if (!result) throw new Error('Stream terminé sans événement done')
  return result
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

export async function downloadRuntimePackage(sessionId: string, dossierId: string): Promise<void> {
  const res = await fetch(`/api/runtime/app/package/download?session_id=${encodeURIComponent(sessionId)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Erreur réseau' }))
    throw new Error((err as { error?: string }).error ?? 'Téléchargement échoué')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `paquet-${dossierId}.zip`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
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

export interface TranscriptExchange {
  user: string
  agent: string
  agent_label: string
  answer: string
  created_at_utc: string
}

export async function fetchRuntimeTranscript(sessionId: string, agent?: string): Promise<TranscriptExchange[]> {
  const agentParam = agent ? `&agent=${encodeURIComponent(agent)}` : ''
  const result = await runtimeJson<{ exchanges: TranscriptExchange[]; count: number }>(
    `/app/transcript?session_id=${encodeURIComponent(sessionId)}${agentParam}`
  )
  return result.exchanges
}

export async function saveRuntimeAdjustments(sessionId: string, adjustments: Adjustment[]): Promise<void> {
  await runtimeJson<{ ok: boolean; count: number }>('/app/adjustments', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, adjustments }),
  })
}

export async function saveRuntimeFactOverrides(
  sessionId: string,
  overrides: { surface_pi2?: number | null; zone?: string; date_reference?: string }
): Promise<void> {
  await runtimeJson<{ ok: boolean }>('/app/facts', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, ...overrides }),
  })
}

export async function saveRuntimeComparables(sessionId: string, comparables: import('@/types').Comparable[]): Promise<void> {
  await runtimeJson<{ ok: boolean; count: number }>('/app/comparables', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, comparables }),
  })
}

// ── S5 — Checkpoint 1 review ─────────────────────────────────────────────────

export interface IntakeField {
  key: string
  label: string
  value: string | null
  missing: boolean
  required: boolean
}

export interface IntakeFacts {
  session_id: string
  dossier_id: string
  fields: IntakeField[]
  total: number
  missing_count: number
  required_missing: string[]
  ready_to_confirm: boolean
}

export function fetchCheckpointFacts(sessionId: string): Promise<IntakeFacts> {
  return runtimeJson<IntakeFacts>(`/app/facts?session_id=${encodeURIComponent(sessionId)}`)
}

export async function confirmCheckpoint(
  sessionId: string,
  checkpoint: number,
  evaluatorId?: string,
): Promise<void> {
  await runtimeJson<unknown>('/app/checkpoint/confirm', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      checkpoint,
      ...(evaluatorId ? { _evaluator_id: evaluatorId } : {}),
    }),
  })
}

export async function resumeCheckpoint(
  sessionId: string,
  checkpoint: number,
): Promise<void> {
  await runtimeJson<unknown>('/app/checkpoint/resume', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, checkpoint }),
  })
}

export async function exportRapport(
  sessionId: string,
  format: 'docx' | 'html' | 'pdf'
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
  if (format === 'docx' || format === 'pdf') {
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

export interface ValuationApproachTrace {
  approach: string
  label: string
  method: string
  value: number | null
  input_count: number
  base_value: number | null
  adjustment_total: number | null
  weights: number[]
  policy: string[]
  selected_comparables: Array<{
    comparable_id: string
    prix_vente: number | null
    score: number | null
    date_vente: string
    source_id: string
  }>
}

export interface ValuationTrace {
  session_id: string
  approaches: ValuationApproachTrace[]
  hypotheses: Array<{ hypothese?: string; [key: string]: unknown }>
}

export async function fetchValuationTrace(sessionId: string): Promise<ValuationTrace | null> {
  try {
    return await runtimeJson<ValuationTrace>(`/app/trace?session_id=${encodeURIComponent(sessionId)}`)
  } catch {
    return null
  }
}

// ── S6 — Checkpoint 2 — Import JLR + sélection comparables ──────────────────

export interface ComparableCandidate {
  id: string
  adresse: string
  prix_vente: number
  date_vente: string
  surface_habitable: number | null
  surface_terrain: number | null
  nb_chambres: number | null
  nb_pieces: number | null
  type_bien: string | null
  source_id: string
  distance_km: number | null
  score: number
  score_details: {
    components: Record<string, number>
    rationale: string[]
    score: number
  }
}

export interface ComparableCandidatesResult {
  session_id: string
  candidates: ComparableCandidate[]
  total: number
  subject_address: string | null
}

export function fetchComparableCandidates(sessionId: string): Promise<ComparableCandidatesResult> {
  return runtimeJson<ComparableCandidatesResult>(
    `/app/comparables/candidates?session_id=${encodeURIComponent(sessionId)}`
  )
}

export async function uploadJlrCsv(sessionId: string, file: File): Promise<ComparableCandidatesResult> {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    throw new Error('Format non supporté. Fichier CSV uniquement.')
  }
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('Fichier trop volumineux (maximum 5 Mo).')
  }

  const content_b64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1])
    }
    reader.onerror = () => reject(new Error('Lecture du fichier échouée.'))
    reader.readAsDataURL(file)
  })

  return runtimeJson<ComparableCandidatesResult>('/app/jlr/upload', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, filename: file.name, content_b64 }),
  })
}

export async function confirmComparables(
  sessionId: string,
  selectedIds: string[],
  checkpoint: number,
): Promise<void> {
  await runtimeJson<{ ok: boolean }>('/app/checkpoint/comparables', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, selected_ids: selectedIds }),
  })
}

// ── S7 — Lettre de mandat ─────────────────────────────────────────────────────

export async function downloadLettreMandat(sessionId: string): Promise<void> {
  const result = await runtimeJson<{
    dossier_id: string
    format: string
    content_b64?: string
    filename: string
  }>('/app/mandat/lettre', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, format: 'pdf' }),
  })

  if (!result.content_b64) throw new Error('PDF non généré')
  const bytes = Uint8Array.from(atob(result.content_b64), c => c.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = result.filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
