import { createClient } from '@/lib/supabase/client'
import type { DbComparable } from '@/types/db'
import type { Comparable } from '@/types'

function buildMeta(row: DbComparable): string {
  const parts: string[] = []
  if (row.hab_m2) parts.push(`${row.hab_m2} m² hab.`)
  if (row.terrain_m2) parts.push(`${row.terrain_m2} m² terrain`)
  if (row.year_built) parts.push(String(row.year_built))
  if (row.renovated_year) parts.push(`Rénové ${row.renovated_year}`)
  if (row.garage_type) parts.push(`Garage ${row.garage_type}`)
  return parts.join(' · ')
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  })
    .format(n)
    .replace('CA', '')
    .trim()
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-CA', { month: 'short', year: 'numeric' })
}

function toUiComparable(row: DbComparable): Comparable {
  return {
    id: row.id,
    rank: row.rank,
    address: row.address,
    hab_m2: row.hab_m2,
    terrain_m2: row.terrain_m2,
    year_built: row.year_built,
    renovated_year: row.renovated_year,
    garage_type: row.garage_type,
    sale_price: row.sale_price,
    sale_date: row.sale_date,
    meta: buildMeta(row),
    price: formatPrice(row.sale_price),
    date: formatDate(row.sale_date),
  }
}

export async function fetchComparables(dossierId: string): Promise<Comparable[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('comparables')
    .select('*')
    .eq('dossier_id', dossierId)
    .order('sort_order', { ascending: true })

  if (error) throw error
  return (data ?? []).map(row => toUiComparable(row as DbComparable))
}
