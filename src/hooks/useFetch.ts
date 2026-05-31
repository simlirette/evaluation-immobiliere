'use client'
import { useEffect, useState, useCallback, useRef } from 'react'

export interface UseFetchResult<T> {
  data: T | null
  loading: boolean
  error: boolean
  reload: () => void
}

export function useFetch<T>(
  fn: () => Promise<T>,
  deps: unknown[]
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const mountedRef = useRef(true)

  const load = useCallback(() => {
    setLoading(true)
    setError(false)
    fn()
      .then((result) => { if (mountedRef.current) { setData(result); setLoading(false) } })
      .catch(() => { if (mountedRef.current) { setError(true); setLoading(false) } })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    mountedRef.current = true
    load()
    return () => { mountedRef.current = false }
  }, [load])

  return { data, loading, error, reload: load }
}
