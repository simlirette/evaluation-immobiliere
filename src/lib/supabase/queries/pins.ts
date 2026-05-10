import { createClient } from '@/lib/supabase/client'

export async function togglePin(dossierId: string, currentlyPinned: boolean): Promise<void> {
  // `dossierId` is the slug — look up the Supabase UUID first
  const supabase = createClient()

  const { data: row, error: fetchErr } = await supabase
    .from('dossiers')
    .select('id')
    .eq('slug', dossierId)
    .single()

  if (fetchErr || !row) {
    console.error('[togglePin] dossier not found:', dossierId)
    return
  }

  if (currentlyPinned) {
    await supabase.from('user_dossier_pins').delete().eq('dossier_id', row.id)
  } else {
    await supabase.from('user_dossier_pins').insert({ dossier_id: row.id })
  }
}
