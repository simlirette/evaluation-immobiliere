import {
  createRuntimeDossier,
  deleteRuntimeDossier,
  fetchRuntimeDossier,
  fetchRuntimeDossiers,
  type CreateRuntimeDossierInput,
} from '@/lib/runtime-api'
import type { Dossier } from '@/types'

export type CreateDossierInput = CreateRuntimeDossierInput

export async function fetchDossiers(): Promise<Dossier[]> {
  return fetchRuntimeDossiers()
}

export async function fetchDossier(slug: string): Promise<Dossier | null> {
  return fetchRuntimeDossier(slug)
}

export async function createDossier(input: CreateDossierInput): Promise<Dossier> {
  return createRuntimeDossier(input)
}

export async function deleteDossier(id: string): Promise<void> {
  return deleteRuntimeDossier(id)
}
