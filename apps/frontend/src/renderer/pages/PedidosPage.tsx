import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DateInput } from '@/components/ui/date-input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState, ErrorState } from '@/components/feedback-state'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { FormActions } from '@/components/forms/FormActions'
import { FormSection } from '@/components/forms/FormSection'
import { api } from '@/lib/api'
import { formatDateBR, formatRequestType } from '@/lib/format'
import { toast } from 'sonner'

type Preference = { request_id: string; employee_id: string; request_date: string; request_type: string; decision: string }

const createPreferenceSchema = z.object({
  employee_id: z
    .string()
    .trim()
    .min(2, 'Informe o colaborador com pelo menos 2 caracteres.'),
  request_date: z.string().min(1, 'Informe a data desejada.'),
  request_type: z.enum(['FOLGA_ON_DATE', 'SHIFT_CHANGE_ON_DATE', 'AVOID_SUNDAY_DATE']),
})

type CreatePreferenceForm = z.infer<typeof createPreferenceSchema>

export function PedidosPage() {
  const [preferences, setPreferences] = useState<Preference[]>([])
  const [error, setError] = useState<string | null>(null)
  const form = useForm<CreatePreferenceForm>({
    resolver: zodResolver(createPreferenceSchema),
    defaultValues: { employee_id: '', request_date: '', request_type: 'FOLGA_ON_DATE' },
  })

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
      toast.success('Pedido aprovado com sucesso.')
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro')
      toast.error('Não foi possível aprovar o pedido.')
    }
  }

  const handleReject = async (id: string) => {
    try {
      await api.preferences.updateDecision(id, { decision: 'REJECTED' })
      toast.success('Pedido rejeitado com sucesso.')
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro')
      toast.error('Não foi possível rejeitar o pedido.')
    }
  }

  const handleCreate = async (values: CreatePreferenceForm) => {
    try {
      await api.preferences.create({
        request_id: crypto.randomUUID(),
        employee_id: values.employee_id.toUpperCase(),
        request_date: values.request_date,
        request_type: values.request_type,
      })
      form.reset({ employee_id: '', request_date: '', request_type: 'FOLGA_ON_DATE' })
      toast.success('Pedido criado com sucesso.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro')
      toast.error('Não foi possível criar o pedido.')
    }
  }

  const pendentes = preferences.filter((p) => p.decision === 'PENDING')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Pedidos</h1>
      {error && <ErrorState message={error} />}
      <Tabs defaultValue="pendentes">
        <TabsList>
          <TabsTrigger value="pendentes">Pendentes ({pendentes.length})</TabsTrigger>
          <TabsTrigger value="novo">Novo pedido</TabsTrigger>
        </TabsList>
        <TabsContent value="pendentes">
          <div className="space-y-4">
            {pendentes.length === 0 ? (
              <EmptyState message="Nenhum pedido pendente no momento." />
            ) : (
              pendentes.map((p) => (
                <Card key={p.request_id}>
                  <CardHeader>
                    <CardTitle>{p.employee_id} — {formatRequestType(p.request_type)}</CardTitle>
                    <CardDescription>{formatDateBR(p.request_date)}</CardDescription>
                    <CardAction>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleApprove(p.request_id)}>Aprovar</Button>
                        <Button size="sm" variant="destructive" onClick={() => handleReject(p.request_id)}>Rejeitar</Button>
                      </div>
                    </CardAction>
                  </CardHeader>
                </Card>
              ))
            )}
          </div>
        </TabsContent>
        <TabsContent value="novo">
          <Card>
            <CardHeader>
              <CardTitle>Novo pedido</CardTitle>
              <CardDescription>Registre pedidos de folga, troca de turno ou restrição de domingo.</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form id="preference-form" onSubmit={form.handleSubmit(handleCreate)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="employee_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Colaborador</FormLabel>
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
                    control={form.control}
                    name="request_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Data desejada</FormLabel>
                          <FormControl>
                            <DateInput {...field} />
                          </FormControl>
                        </FormSection>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="request_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormSection>
                          <FormLabel>Tipo de pedido</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="FOLGA_ON_DATE">Folga na data</SelectItem>
                              <SelectItem value="SHIFT_CHANGE_ON_DATE">Troca de turno</SelectItem>
                              <SelectItem value="AVOID_SUNDAY_DATE">Evitar domingo</SelectItem>
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
              <FormActions formId="preference-form" isSubmitting={form.formState.isSubmitting} submitLabel="Criar pedido" />
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
