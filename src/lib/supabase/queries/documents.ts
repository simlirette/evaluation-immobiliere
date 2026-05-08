import { fetchRuntimeDocuments, uploadRuntimeDocument } from '@/lib/runtime-api'
import type { Document } from '@/types'

export async function fetchDocuments(dossierId: string): Promise<Document[]> {
  return fetchRuntimeDocuments(dossierId)
}

export async function uploadDocument(dossierId: string, file: File): Promise<Document> {
  return uploadRuntimeDocument(dossierId, file)
}
