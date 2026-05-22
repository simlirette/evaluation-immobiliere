'use server'

import { createClient } from '@/lib/supabase/server'
import { createClient as createAdminClient } from '@supabase/supabase-js'

export type InviteResult =
  | { ok: true; email: string }
  | { ok: false; error: string }

export async function inviteEvaluateur(formData: FormData): Promise<InviteResult> {
  const email = (formData.get('email') as string | null)?.trim().toLowerCase() ?? ''

  if (!email || !email.includes('@')) {
    return { ok: false, error: 'Adresse e-mail invalide.' }
  }

  // Vérifier que l'appelant est bureau_admin
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { ok: false, error: 'Non authentifié.' }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single()

  if (!profile || profile.role !== 'bureau_admin') {
    return { ok: false, error: 'Accès refusé — rôle bureau_admin requis.' }
  }

  // inviteUserByEmail requiert la service role key (jamais exposée côté client)
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL

  if (!serviceRoleKey || !supabaseUrl) {
    return { ok: false, error: 'Service role key non configurée — invitation impossible.' }
  }

  const admin = createAdminClient(supabaseUrl, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  })

  const { error } = await admin.auth.admin.inviteUserByEmail(email, {
    data: { role: 'evaluateur' },
    redirectTo: `${supabaseUrl.replace('supabase.co', 'supabase.co')}/auth/callback`,
  })

  if (error) {
    return { ok: false, error: error.message }
  }

  return { ok: true, email }
}
