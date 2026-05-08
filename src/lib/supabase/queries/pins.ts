import { toggleRuntimePin } from '@/lib/runtime-api'

export async function togglePin(dossierId: string, currentlyPinned: boolean): Promise<void> {
  return toggleRuntimePin(dossierId, currentlyPinned)
}
