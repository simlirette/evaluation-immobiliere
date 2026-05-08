import { fetchRuntimeComparables } from '@/lib/runtime-api'
import type { Comparable } from '@/types'

export async function fetchComparables(dossierId: string): Promise<Comparable[]> {
  return fetchRuntimeComparables(dossierId)
}
