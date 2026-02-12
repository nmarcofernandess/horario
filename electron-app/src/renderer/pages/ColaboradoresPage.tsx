import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { api } from '@/lib/api'
import { formatContract } from '@/lib/format'

type Employee = { employee_id: string; name: string; contract_code: string; sector_id: string; rank: number; active: boolean }
type Sector = { sector_id: string; name: string }

export function ColaboradoresPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [sectors, setSectors] = useState<Sector[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newEmp, setNewEmp] = useState({ employee_id: '', name: '', contract_code: 'H44_CAIXA', sector_id: 'CAIXA' })
  const [newSector, setNewSector] = useState({ sector_id: '', name: '' })

  const load = async () => {
    try {
      setError(null)
      const [e, s] = await Promise.all([api.employees.list(), api.sectors.list()])
      setEmployees(e)
      setSectors(s)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleAddEmployee = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newEmp.employee_id.trim() || !newEmp.name.trim()) return
    setLoading(true)
    try {
      await api.employees.create(newEmp)
      setNewEmp({ ...newEmp, employee_id: '', name: '' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }

  const handleAddSector = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSector.sector_id.trim() || !newSector.name.trim()) return
    setLoading(true)
    try {
      await api.sectors.create(newSector)
      setNewSector({ sector_id: '', name: '' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Colaboradores</h1>
      {error && <p className="text-destructive text-sm">{error}</p>}
      <Tabs defaultValue="colaboradores">
        <TabsList>
          <TabsTrigger value="colaboradores">Colaboradores</TabsTrigger>
          <TabsTrigger value="setores">Setores</TabsTrigger>
        </TabsList>
        <TabsContent value="colaboradores">
          <Card>
            <CardHeader>
              <CardTitle>Novo colaborador</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddEmployee} className="flex gap-4 flex-wrap items-end">
                <div>
                  <label className="text-sm block mb-1">Apelido ou código</label>
                  <Input placeholder="Ex: MARIA" value={newEmp.employee_id} onChange={(e) => setNewEmp({ ...newEmp, employee_id: e.target.value.toUpperCase() })} />
                </div>
                <div>
                  <label className="text-sm block mb-1">Nome completo</label>
                  <Input placeholder="Ex: Maria Silva" value={newEmp.name} onChange={(e) => setNewEmp({ ...newEmp, name: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm block mb-1">Contrato</label>
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    value={newEmp.contract_code}
                    onChange={(e) => setNewEmp({ ...newEmp, contract_code: e.target.value })}
                  >
                    <option value="H44_CAIXA">44h semanais</option>
                    <option value="H36_CAIXA">36h semanais</option>
                    <option value="H30_CAIXA">30h semanais</option>
                  </select>
                </div>
                <Button type="submit" disabled={loading}>Adicionar</Button>
              </form>
            </CardContent>
          </Card>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Lista ({employees.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Nome</TableHead>
                    <TableHead>Contrato</TableHead>
                    <TableHead>Setor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.map((emp) => (
                    <TableRow key={emp.employee_id}>
                      <TableCell>{emp.employee_id}</TableCell>
                      <TableCell>{emp.name}</TableCell>
                      <TableCell>{formatContract(emp.contract_code)}</TableCell>
                      <TableCell>{emp.sector_id}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="setores">
          <Card>
            <CardHeader>
              <CardTitle>Novo setor</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddSector} className="flex gap-4 flex-wrap items-end">
                <div>
                  <label className="text-sm block mb-1">Código do setor</label>
                  <Input placeholder="Ex: CAIXA" value={newSector.sector_id} onChange={(e) => setNewSector({ ...newSector, sector_id: e.target.value.toUpperCase() })} />
                </div>
                <div>
                  <label className="text-sm block mb-1">Nome do setor</label>
                  <Input placeholder="Ex: Caixa" value={newSector.name} onChange={(e) => setNewSector({ ...newSector, name: e.target.value })} />
                </div>
                <Button type="submit" disabled={loading}>Adicionar</Button>
              </form>
            </CardContent>
          </Card>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Setores ({sectors.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Nome</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sectors.map((s) => (
                    <TableRow key={s.sector_id}>
                      <TableCell>{s.sector_id}</TableCell>
                      <TableCell>{s.name}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
