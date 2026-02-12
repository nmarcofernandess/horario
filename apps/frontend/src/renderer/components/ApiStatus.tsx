import { useState, useEffect, useCallback } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

const POLL_INTERVAL_MS = 5000

export function ApiStatus() {
  const [online, setOnline] = useState<boolean | null>(null)
  const [checking, setChecking] = useState(false)

  const check = useCallback(async () => {
    setChecking(true)
    try {
      const ok = await api.health()
      setOnline(ok)
    } catch {
      setOnline(false)
    } finally {
      setChecking(false)
    }
  }, [])

  useEffect(() => {
    check()
    const id = setInterval(check, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [check])

  if (online === null) return null

  return (
    <div className="flex items-center gap-2 ml-auto">
      {online ? (
        <Badge variant="secondary" className="text-green-600 dark:text-green-400 border-green-300 dark:border-green-700">
          Conectado
        </Badge>
      ) : (
        <>
          <Badge variant="destructive">API offline</Badge>
          <Button variant="outline" size="sm" onClick={check} disabled={checking}>
            {checking ? 'Verificando…' : 'Reconectar'}
          </Button>
        </>
      )}
    </div>
  )
}
