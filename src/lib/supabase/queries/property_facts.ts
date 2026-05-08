import { fetchRuntimeFacts } from '@/lib/runtime-api'
import type { FactChip } from '@/types'

export async function fetchPropertyFacts(dossierId: string): Promise<FactChip[]> {
  return fetchRuntimeFacts(dossierId)
}
