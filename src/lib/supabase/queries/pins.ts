import { createClient } from '@/lib/supabase/client'

export async function togglePin(dossierId: string, currentlyPinned: boolean): Promise<void> {
  // `dossierId` is the slug — look up the Supabase UUID first
  const supabase = createClient()
  const { data: { user }, error: userErr } = await supabase.auth.getUser()

  if (userErr || !user) {
    console.error('[togglePin] user not authenticated')
    return
  }

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
    await supabase
      .from('user_dossier_pins')
      .delete()
      .eq('dossier_id', row.id)
      .eq('user_id', user.id)
  } else {
    await supabase
      .from('user_dossier_pins')
      .insert({ dossier_id: row.id, user_id: user.id })
  }
}
