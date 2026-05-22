import { createClient } from '@/lib/supabase/server'

export type UserRole = 'bureau_admin' | 'evaluateur'

export interface Profile {
  id: string
  role: UserRole
  display_name: string | null
}

/**
 * Fetch the authenticated user's profile (role + display_name).
 * Returns null when Supabase is not configured or the user is unauthenticated.
 */
export async function getMyProfile(): Promise<Profile | null> {
  try {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return null

    const { data, error } = await supabase
      .from('profiles')
      .select('id, role, display_name')
      .eq('id', user.id)
      .single()

    if (error || !data) return null
    return data as Profile
  } catch {
    return null
  }
}
