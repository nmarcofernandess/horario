import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/lib/api'
import { formatDateBR, formatRequestType } from '@/lib/format'

type Preference = { request_id: string; employee_id: string; request_date: string; request_type: string; decision: string }

export function PedidosPage() {
  const [preferences, setPreferences] = useState<Preference[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newPref, setNewPref] = useState({ employee_id: '', request_date: '', request_type: 'FOLGA_ON_DATE' })

  const load = async () => {
    try {
      setError(null)
      const p = await api.preferences.list()
      setPreferences(p)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleApprove = async (id: string) => {
    try {
      await api.preferences.updateDecision(id, { decision: 'APPROVED' })
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro')
    }
  }

  const handleReject = async (id: string) => {
    try {
      await api.preferences.updateDecision(id, { decision: 'REJECTED' })
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro')
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPref.employee_id.trim() || !newPref.request_date) return
    setLoading(true)
    try {
      await api.preferences.create({
        request_id: crypto.randomUUID(),
        employee_id: newPref.employee_id,
        request_date: newPref.request_date,
        request_type: newPref.request_type,
      })
      setNewPref({ employee_id: '', request_date: '', request_type: 'FOLGA_ON_DATE' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }

  const pendentes = preferences.filter((p) => p.decision === 'PENDING')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Pedidos</h1>
      {error && <p className="text-destructive text-sm">{error}</p>}
      <Tabs defaultValue="pendentes">
        <TabsList>
          <TabsTrigger value="pendentes">Pendentes ({pendentes.length})</TabsTrigger>
          <TabsTrigger value="novo">Novo pedido</TabsTrigger>
        </TabsList>
        <TabsContent value="pendentes">
          <div className="space-y-4">
            {pendentes.length === 0 ? (
              <p className="text-muted-foreground">Nenhum pedido pendente no momento.</p>
            ) : (
              pendentes.map((p) => (
                <Card key={p.request_id}>
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <p><strong>{p.employee_id}</strong> — {formatRequestType(p.request_type)}</p>
                        <p className="text-sm text-muted-foreground">{formatDateBR(p.request_date)}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleApprove(p.request_id)}>Aprovar</Button>
                        <Button size="sm" variant="destructive" onClick={() => handleReject(p.request_id)}>Rejeitar</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
        <TabsContent value="novo">
          <Card>
            <CardHeader>
              <CardTitle>Novo pedido</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="text-sm block mb-1">Colaborador</label>
                  <Input placeholder="Ex: MARIA" value={newPref.employee_id} onChange={(e) => setNewPref({ ...newPref, employee_id: e.target.value.toUpperCase() })} />
                </div>
                <div>
                  <label className="text-sm block mb-1">Data desejada</label>
                  <Input type="date" value={newPref.request_date} onChange={(e) => setNewPref({ ...newPref, request_date: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm block mb-1">Tipo de pedido</label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    value={newPref.request_type}
                    onChange={(e) => setNewPref({ ...newPref, request_type: e.target.value })}
                  >
                    <option value="FOLGA_ON_DATE">Folga na data</option>
                    <option value="SHIFT_CHANGE_ON_DATE">Troca de turno</option>
                    <option value="AVOID_SUNDAY_DATE">Evitar domingo</option>
                  </select>
                </div>
                <Button type="submit" disabled={loading}>Criar pedido</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
