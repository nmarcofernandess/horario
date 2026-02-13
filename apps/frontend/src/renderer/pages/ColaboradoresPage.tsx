import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ErrorState } from '@/components/feedback-state'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { FormActions } from '@/components/forms/FormActions'
import { FormSection } from '@/components/forms/FormSection'
import { api } from '@/lib/api'
import { formatContract } from '@/lib/format'
import { toast } from 'sonner'

type Employee = { employee_id: string; name: string; contract_code: string; sector_id: string; rank: number; active: boolean }
type Sector = { sector_id: string; name: string }

const createEmployeeSchema = z.object({
  employee_id: z.string().trim().min(2, 'Informe ao menos 2 caracteres.'),
  name: z.string().trim().min(3, 'Informe o nome completo.'),
  contract_code: z.enum(['H44_CAIXA', 'H36_CAIXA', 'H30_CAIXA']),
})

const createSectorSchema = z.object({
  sector_id: z.string().trim().min(2, 'Informe o código do setor.'),
  name: z.string().trim().min(2, 'Informe o nome do setor.'),
})

type CreateEmployeeForm = z.infer<typeof createEmployeeSchema>
type CreateSectorForm = z.infer<typeof createSectorSchema>

export function ColaboradoresPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [sectors, setSectors] = useState<Sector[]>([])
  const [error, setError] = useState<string | null>(null)
  const employeeForm = useForm<CreateEmployeeForm>({
    resolver: zodResolver(createEmployeeSchema),
    defaultValues: { employee_id: '', name: '', contract_code: 'H44_CAIXA' },
  })
  const sectorForm = useForm<CreateSectorForm>({
    resolver: zodResolver(createSectorSchema),
    defaultValues: { sector_id: '', name: '' },
  })

  const load = async () => {
    try {
      setError(null)
      const [e, s] = await Promise.all([api.employees.list(), api.sectors.list()])
      setEmployees(e)
      setSectors(s)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar')
      toast.error('Não foi possível carregar colaboradores e setores.')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleAddEmployee = async (values: CreateEmployeeForm) => {
    try {
      await api.employees.create({ ...values, employee_id: values.employee_id.toUpperCase(), sector_id: 'CAIXA' })
      employeeForm.reset({ employee_id: '', name: '', contract_code: values.contract_code })
      toast.success('Colaborador adicionado com sucesso.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
      toast.error('Não foi possível adicionar o colaborador.')
    }
  }

  const handleAddSector = async (values: CreateSectorForm) => {
    try {
      await api.sectors.create({ sector_id: values.sector_id.toUpperCase(), name: values.name })
      sectorForm.reset()
      toast.success('Setor adicionado com sucesso.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
      toast.error('Não foi possível adicionar o setor.')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Colaboradores</h1>
      {error && <ErrorState message={error} />}
      <Tabs defaultValue="colaboradores">
        <TabsList>
          <TabsTrigger value="colaboradores">Colaboradores</TabsTrigger>
          <TabsTrigger value="setores">Setores</TabsTrigger>
        </TabsList>
        <TabsContent value="colaboradores">
          <Card>
            <CardHeader>
              <CardTitle>Novo colaborador</CardTitle>
              <CardDescription>Cadastre identificador, nome e contrato para entrar no ciclo de escala.</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...employeeForm}>
                <form id="employee-form" onSubmit={employeeForm.handleSubmit(handleAddEmployee)} className="grid w-full gap-4 sm:grid-cols-2 md:grid-cols-3">
                  <FormField
                    control={employeeForm.control}
                    name="employee_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Apelido ou código</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="Ex: MARIA"
                              value={field.value}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                            />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={employeeForm.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Nome completo</FormLabel>
                          <FormControl>
                            <Input placeholder="Ex: Maria Silva" {...field} />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={employeeForm.control}
                    name="contract_code"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Contrato</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="H44_CAIXA">44h semanais</SelectItem>
                              <SelectItem value="H36_CAIXA">36h semanais</SelectItem>
                              <SelectItem value="H30_CAIXA">30h semanais</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </form>
              </Form>
            </CardContent>
            <CardFooter>
              <FormActions formId="employee-form" isSubmitting={employeeForm.formState.isSubmitting} submitLabel="Adicionar" />
            </CardFooter>
          </Card>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Lista ({employees.length})</CardTitle>
              <CardDescription>Colaboradores ativos do setor atual para revisão rápida.</CardDescription>
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
              <CardDescription>Crie setores adicionais para evolução multi-setor.</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...sectorForm}>
                <form id="sector-form" onSubmit={sectorForm.handleSubmit(handleAddSector)} className="grid w-full gap-4 sm:grid-cols-2">
                  <FormField
                    control={sectorForm.control}
                    name="sector_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Código do setor</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="Ex: CAIXA"
                              value={field.value}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                            />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={sectorForm.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Nome do setor</FormLabel>
                          <FormControl>
                            <Input placeholder="Ex: Caixa" {...field} />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </form>
              </Form>
            </CardContent>
            <CardFooter>
              <FormActions formId="sector-form" isSubmitting={sectorForm.formState.isSubmitting} submitLabel="Adicionar" />
            </CardFooter>
          </Card>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Setores ({sectors.length})</CardTitle>
              <CardDescription>Estrutura de setores disponíveis na instalação local.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableCaption>Setores disponíveis nesta instalação.</TableCaption>
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
                <TableFooter>
                  <TableRow>
                    <TableCell colSpan={2}>{sectors.length} setores cadastrados.</TableCell>
                  </TableRow>
                </TableFooter>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
