import { createClient } from '@/lib/supabase/client'

export async function togglePin(dossierId: string, currentlyPinned: boolean): Promise<void> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return

  if (currentlyPinned) {
    await supabase
      .from('user_dossier_pins')
      .delete()
      .match({ user_id: user.id, dossier_id: dossierId })
  } else {
    await supabase
      .from('user_dossier_pins')
      .insert({ user_id: user.id, dossier_id: dossierId })
  }
}
