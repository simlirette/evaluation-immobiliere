import { fetchRuntimeAdjustments } from '@/lib/runtime-api'
import type { Adjustment } from '@/types'

export async function fetchAdjustments(dossierId: string): Promise<Adjustment[]> {
  return fetchRuntimeAdjustments(dossierId)
}
