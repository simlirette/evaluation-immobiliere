import { createClient } from '@/lib/supabase/client'

export interface RapportVersion {
  id: string
  session_id: string
  dossier_id: string
  content: string
  format: string
  label: string
  is_initial: boolean
  created_at: string
}

/**
 * Insère une nouvelle version dans Supabase.
 * Lance si Supabase inaccessible — l'appelant doit try/catch.
 */
export async function saveVersion(
  sessionId: string,
  dossierId: string,
  content: string,
  format: string,
  label: string,
  isInitial: boolean
): Promise<void> {
  const supabase = createClient()
  const { error } = await supabase.from('rapport_versions').insert({
    session_id: sessionId,
    dossier_id: dossierId,
    content,
    format,
    label,
    is_initial: isInitial,
  })
  if (error) throw new Error(`saveVersion: ${error.message}`)
}

/**
 * Charge les 6 versions les plus récentes pour une session.
 * Triées DESC par created_at.
 */
export async function loadVersions(sessionId: string): Promise<RapportVersion[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('rapport_versions')
    .select('*')
    .eq('session_id', sessionId)
    .order('created_at', { ascending: false })
    .limit(6)
  if (error) throw new Error(`loadVersions: ${error.message}`)
  return (data ?? []) as RapportVersion[]
}

/**
 * Renomme une version existante.
 */
export async function renameVersion(id: string, label: string): Promise<void> {
  const supabase = createClient()
  const { error } = await supabase
    .from('rapport_versions')
    .update({ label })
    .eq('id', id)
  if (error) throw new Error(`renameVersion: ${error.message}`)
}
