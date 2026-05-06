import { createClient } from '@/lib/supabase/client'
import type { DbDocument } from '@/types/db'
import type { Document } from '@/types'

function formatSize(bytes: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function toUiDocument(row: DbDocument): Document {
  const filename = row.storage_path.split('/').pop() ?? row.storage_path
  return {
    id: row.id,
    name: row.display_name,
    filename,
    sizeLabel: formatSize(row.size_bytes),
  }
}

export async function fetchDocuments(dossierId: string): Promise<Document[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('documents')
    .select('*')
    .eq('dossier_id', dossierId)
    .order('uploaded_at', { ascending: true })

  if (error) throw error
  return (data ?? []).map(toUiDocument)
}

export async function uploadDocument(dossierId: string, file: File): Promise<Document> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  const path = `${user.id}/${dossierId}/${Date.now()}-${file.name}`

  const { error: uploadError } = await supabase.storage
    .from('dossier-documents')
    .upload(path, file)

  if (uploadError) throw uploadError

  const { data, error } = await supabase
    .from('documents')
    .insert({
      dossier_id: dossierId,
      display_name: file.name,
      storage_path: path,
      size_bytes: file.size,
      uploaded_by: user.id,
    })
    .select()
    .single()

  if (error) throw error
  return toUiDocument(data as DbDocument)
}
