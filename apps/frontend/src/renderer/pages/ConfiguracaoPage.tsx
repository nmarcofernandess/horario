import { useState, useEffect, useMemo } from 'react'
import { z } from 'zod'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DateInput } from '@/components/ui/date-input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { ErrorState } from '@/components/feedback-state'
import { ShiftSection } from '@/components/configuracao/ShiftSection'
import { TemplateSection } from '@/components/configuracao/TemplateSection'
import { RotationSection } from '@/components/configuracao/RotationSection'
import { ExceptionSection } from '@/components/configuracao/ExceptionSection'
import { DemandSection } from '@/components/configuracao/DemandSection'
import { useShifts } from '@/hooks/useShifts'
import { useTemplate } from '@/hooks/useTemplate'
import { useRotation } from '@/hooks/useRotation'
import { useExceptions } from '@/hooks/useExceptions'
import { useDemand } from '@/hooks/useDemand'
import { api } from '@/lib/api'
import { toast } from 'sonner'

const WEEKDAYS = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'] as const

type Shift = { shift_code: string; sector_id: string; minutes: number; day_scope: string }
type Exception = { sector_id: string; employee_id: string; exception_date: string; exception_type: string; note: string | null }
type DemandSlot = { sector_id: string; work_date: string; slot_start: string; min_required: number }
type Employee = { employee_id: string; name: string }
type RotationRow = { scale_index: number; employee_id: string; sunday_date: string; folga_date: string | null }

const shiftSchema = z.object({
  shift_code: z.string().trim().min(2, 'Código do turno é obrigatório.'),
  minutes: z.number().int().min(0, 'Duração deve ser maior ou igual a 0.'),
  day_scope: z.string().min(1, 'Tipo do turno é obrigatório.'),
})

const rotationSchema = z.object({
  scale_index: z.number().int().min(1, 'Posição deve ser maior ou igual a 1.'),
  employee_id: z.string().trim().min(1, 'Selecione o colaborador.'),
  sunday_date: z.string().min(1, 'Informe o domingo.'),
  folga_date: z.string().optional(),
})

const exceptionSchema = z.object({
  employee_id: z.string().trim().min(1, 'Selecione o colaborador.'),
  exception_date: z.string().min(1, 'Informe a data da exceção.'),
  exception_type: z.string().min(1, 'Informe o tipo da exceção.'),
  note: z.string().optional(),
})

const demandSchema = z.object({
  work_date: z.string().min(1, 'Informe a data da demanda.'),
  slot_start: z.string().min(1, 'Informe o horário do slot.'),
  min_required: z.number().int().min(1, 'Mínimo de pessoas deve ser >= 1.'),
})
type GovernanceConfig = {
  accepted_dom_folgas_markers: string[]
  marker_semantics: Record<string, string>
  collective_agreement_id: string
  sunday_holiday_legal_validated: boolean
  legal_validation_note?: string
  pending_items: string[]
  release_checklist: Array<{
    item_id: string
    title: string
    done: boolean
    detail?: string
  }>
}
type RuntimeModeConfig = {
  mode: 'NORMAL' | 'ESTRITO'
  updated_at?: string
  updated_by_role?: string
  source: string
}
type GovernanceAuditEvent = {
  event_id: number
  created_at: string
  operation: string
  mode: string
  actor_role: string
  actor_name?: string
  reason?: string
  warnings: string[]
  sector_id?: string
  period_start?: string
  period_end?: string
}

function formatDateTimeBR(dateTime: string) {
  const parsed = new Date(dateTime)
  if (Number.isNaN(parsed.getTime())) return dateTime
  return parsed.toLocaleString('pt-BR')
}

function formatMinutes(m: number) {
  const h = Math.floor(m / 60)
  const min = m % 60
  return min ? `${h}h ${min}min` : `${h}h`
}

function formatDayScope(s: string) {
  const map: Record<string, string> = { WEEKDAY: 'Dia útil', SUNDAY: 'Domingo' }
  return map[s] || s
}

export function ConfiguracaoPage() {
  const {
    shifts,
    newShift,
    setNewShift,
    editingShiftCode,
    loadShifts: loadShiftsRaw,
    resetShiftForm,
    startEditShift,
  } = useShifts()
  const {
    loadTemplate: loadTemplateRaw,
    getTemplateCell,
    handleTemplateCellChange,
    clearTemplateForEmployee,
    clearTemplateAllLocal,
  } = useTemplate()
  const {
    rotationRows,
    setRotationRows,
    newRotation,
    setNewRotation,
    editingRotationIndex,
    setEditingRotationIndex,
    loadRotation: loadRotationRaw,
    startEditRotation,
  } = useRotation()
  const {
    exceptions,
    newExc,
    setNewExc,
    editingExceptionKey,
    setEditingExceptionKey,
    loadExceptions: loadExceptionsRaw,
    startEditException,
  } = useExceptions()
  const {
    demandSlots,
    newDemand,
    setNewDemand,
    editingDemandKey,
    setEditingDemandKey,
    loadDemand: loadDemandRaw,
    startEditDemand,
  } = useDemand()
  const [employees, setEmployees] = useState<Employee[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [governance, setGovernance] = useState<GovernanceConfig | null>(null)
  const [runtimeMode, setRuntimeMode] = useState<RuntimeModeConfig | null>(null)
  const [runtimeActorRole, setRuntimeActorRole] = useState<'ADMIN' | 'OPERADOR'>('ADMIN')
  const [auditEvents, setAuditEvents] = useState<GovernanceAuditEvent[]>([])
  const [auditOperationFilter, setAuditOperationFilter] = useState<'ALL' | 'GENERATE' | 'SIMULATE'>('ALL')
  const [auditModeFilter, setAuditModeFilter] = useState<'ALL' | 'NORMAL' | 'ESTRITO'>('ALL')
  type ConfirmDialog =
    | { type: 'clearTemplate' }
    | { type: 'deleteShift'; shiftCode: string }
    | { type: 'deleteException'; ex: Exception }
    | { type: 'deleteDemand'; d: DemandSlot }
    | { type: 'deleteRotation'; index: number }
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialog | null>(null)

  const loadShifts = async () => {
    try {
      await loadShiftsRaw()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar turnos')
    }
  }

  const loadExceptions = async () => {
    try {
      await loadExceptionsRaw()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar exceções')
    }
  }

  const loadDemand = async () => {
    try {
      await loadDemandRaw()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar demanda')
    }
  }

  const loadEmployees = async () => {
    try {
      const e = await api.employees.list()
      setEmployees(e)
    } catch {
      setEmployees([])
    }
  }

  const loadTemplate = async () => {
    try {
      await loadTemplateRaw()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar mosaico')
    }
  }

  const loadRotation = async () => {
    try {
      await loadRotationRaw()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar rodízio')
    }
  }

  const loadGovernance = async () => {
    try {
      const data = await api.config.getGovernance()
      setGovernance(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar governança')
    }
  }

  const loadRuntimeMode = async () => {
    try {
      const data = await api.config.getRuntimeMode()
      setRuntimeMode(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar modo de execução')
    }
  }

  const loadGovernanceAudit = async () => {
    try {
      const rows = await api.config.listGovernanceAudit(30)
      setAuditEvents(rows)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar auditoria de governança')
    }
  }

  useEffect(() => {
    loadShifts()
    loadEmployees()
    loadExceptions()
    loadDemand()
    loadTemplate()
    loadRotation()
    loadGovernance()
    loadRuntimeMode()
    loadGovernanceAudit()
  }, [])

  const handleSaveRuntimeMode = async () => {
    if (!runtimeMode) return
    setLoading(true)
    setError(null)
    try {
      const updated = await api.config.updateRuntimeMode({
        mode: runtimeMode.mode,
        actor_role: runtimeActorRole,
      })
      setRuntimeMode(updated)
      await loadGovernanceAudit()
      toast.success('Modo de execução atualizado.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar modo de execução')
      toast.error('Não foi possível atualizar o modo de execução.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveGovernance = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!governance) return
    setLoading(true)
    setError(null)
    try {
      const updated = await api.config.updateGovernance({
        marker_semantics: governance.marker_semantics,
        collective_agreement_id: governance.collective_agreement_id,
        sunday_holiday_legal_validated: governance.sunday_holiday_legal_validated,
        legal_validation_note: governance.legal_validation_note || '',
      })
      setGovernance(updated)
      toast.success('Governança salva com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar governança')
      toast.error('Não foi possível salvar a governança.')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyGovernanceDefaults = async () => {
    setLoading(true)
    setError(null)
    try {
      const updated = await api.config.applyGovernanceDefaults()
      setGovernance(updated)
      toast.success('Defaults de governança aplicados.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao aplicar padrão de governança')
      toast.error('Não foi possível aplicar o padrão de governança.')
    } finally {
      setLoading(false)
    }
  }

  const handleReloadGovernance = async () => {
    setLoading(true)
    setError(null)
    try {
      await loadGovernance()
      await loadRuntimeMode()
      await loadGovernanceAudit()
      toast.success('Governança recarregada.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao recarregar governança')
      toast.error('Não foi possível recarregar a governança.')
    } finally {
      setLoading(false)
    }
  }

  const clearTemplateAll = () => {
    setConfirmDialog({ type: 'clearTemplate' })
  }

  const doClearTemplateAll = () => {
    clearTemplateAllLocal()
    setConfirmDialog(null)
  }

  const handleSaveTemplate = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = employees.flatMap((emp) =>
        WEEKDAYS.map((day) => {
          const shiftCode = getTemplateCell(emp.employee_id, day)
          const shift = shifts.find((s) => s.shift_code === shiftCode)
          return {
            employee_id: emp.employee_id,
            day_key: day,
            shift_code: shiftCode || 'FOLGA',
            minutes: shift?.minutes ?? 0,
          }
        })
      ).filter((s) => s.shift_code && s.shift_code !== 'FOLGA')
      await api.weekDayTemplate.save(data)
      await loadTemplate()
      toast.success('Mosaico salvo com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
      toast.error('Não foi possível salvar o mosaico.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddRotation = () => {
    const parsed = rotationSchema.safeParse(newRotation)
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || 'Dados de rodízio inválidos.')
      return
    }
    if (editingRotationIndex != null) {
      setRotationRows((prev) =>
        prev.map((row, idx) =>
          idx === editingRotationIndex
            ? {
                scale_index: newRotation.scale_index,
                employee_id: newRotation.employee_id,
                sunday_date: newRotation.sunday_date,
                folga_date: newRotation.folga_date || null,
              }
            : row
        )
      )
      setEditingRotationIndex(null)
    } else {
      setRotationRows((prev) => [
        ...prev,
        {
          scale_index: newRotation.scale_index,
          employee_id: newRotation.employee_id,
          sunday_date: newRotation.sunday_date,
          folga_date: newRotation.folga_date || null,
        },
      ])
    }
    setNewRotation((p) => ({ ...p, employee_id: '', sunday_date: '', folga_date: '', scale_index: Math.max(1, p.scale_index + 1) }))
  }

  const handleSaveRotation = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.sundayRotation.save(rotationRows)
      await loadRotation()
      toast.success('Rodízio salvo com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
      toast.error('Não foi possível salvar o rodízio.')
    } finally {
      setLoading(false)
    }
  }

  const handleEditRotation = (row: RotationRow, index: number) => {
    startEditRotation(row, index)
  }

  const handleDeleteRotation = (index: number) => {
    setConfirmDialog({ type: 'deleteRotation', index })
  }

  const doDeleteRotation = (index: number) => {
    setRotationRows((prev) => prev.filter((_, i) => i !== index))
    if (editingRotationIndex === index) {
      setEditingRotationIndex(null)
      setNewRotation({ scale_index: 1, employee_id: '', sunday_date: '', folga_date: '' })
    }
    setConfirmDialog(null)
  }

  const handleAddException = async (e: React.FormEvent) => {
    e.preventDefault()
    const parsed = exceptionSchema.safeParse(newExc)
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || 'Dados de exceção inválidos.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (editingExceptionKey) {
        const [original_employee_id, original_exception_date, original_exception_type] = editingExceptionKey.split('|')
        await api.exceptions.update({
          original_employee_id,
          original_exception_date,
          original_exception_type,
          employee_id: newExc.employee_id,
          exception_date: newExc.exception_date,
          exception_type: newExc.exception_type,
          note: newExc.note || undefined,
        })
      } else {
        await api.exceptions.create({
          employee_id: newExc.employee_id,
          exception_date: newExc.exception_date,
          exception_type: newExc.exception_type,
          note: newExc.note || undefined,
        })
      }
      setNewExc({ employee_id: '', exception_date: '', exception_type: 'VACATION', note: '' })
      setEditingExceptionKey(null)
      await loadExceptions()
      toast.success('Exceção salva com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar exceção')
      toast.error('Não foi possível salvar a exceção.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddDemand = async (e: React.FormEvent) => {
    e.preventDefault()
    const minRequired = parseInt(newDemand.min_required, 10) || 1
    const parsed = demandSchema.safeParse({
      work_date: newDemand.work_date,
      slot_start: newDemand.slot_start,
      min_required: minRequired,
    })
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || 'Dados de demanda inválidos.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (editingDemandKey) {
        const [original_work_date, original_slot_start] = editingDemandKey.split('|')
        await api.demandProfile.update({
          original_work_date,
          original_slot_start,
          work_date: newDemand.work_date,
          slot_start: newDemand.slot_start,
          min_required: minRequired,
        })
      } else {
        await api.demandProfile.create({
          work_date: newDemand.work_date,
          slot_start: newDemand.slot_start,
          min_required: minRequired,
        })
      }
      setNewDemand({ work_date: '', slot_start: '08:00', min_required: '1' })
      setEditingDemandKey(null)
      await loadDemand()
      toast.success('Demanda salva com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar demanda')
      toast.error('Não foi possível salvar a demanda.')
    } finally {
      setLoading(false)
    }
  }

  const handleEditException = (ex: Exception) => {
    startEditException(ex)
  }

  const handleDeleteException = (ex: Exception) => {
    setConfirmDialog({ type: 'deleteException', ex })
  }

  const doDeleteException = async (ex: Exception) => {
    setLoading(true)
    setError(null)
    setConfirmDialog(null)
    try {
      await api.exceptions.remove({
        employee_id: ex.employee_id,
        exception_date: ex.exception_date,
        exception_type: ex.exception_type,
      })
      if (editingExceptionKey === `${ex.employee_id}|${ex.exception_date}|${ex.exception_type}`) {
        setEditingExceptionKey(null)
        setNewExc({ employee_id: '', exception_date: '', exception_type: 'VACATION', note: '' })
      }
      await loadExceptions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao remover exceção')
    } finally {
      setLoading(false)
    }
  }

  const handleEditDemand = (d: DemandSlot) => {
    startEditDemand(d)
  }

  const handleDeleteDemand = (d: DemandSlot) => {
    setConfirmDialog({ type: 'deleteDemand', d })
  }

  const doDeleteDemand = async (d: DemandSlot) => {
    setLoading(true)
    setError(null)
    setConfirmDialog(null)
    try {
      await api.demandProfile.remove({ work_date: d.work_date, slot_start: d.slot_start })
      if (editingDemandKey === `${d.work_date}|${d.slot_start}`) {
        setEditingDemandKey(null)
        setNewDemand({ work_date: '', slot_start: '08:00', min_required: '1' })
      }
      await loadDemand()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao remover demanda')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveShift = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newShift.shift_code && !editingShiftCode) return
    const minutes = parseInt(newShift.minutes, 10) || 0
    const parsed = shiftSchema.safeParse({
      shift_code: newShift.shift_code || editingShiftCode || '',
      minutes,
      day_scope: newShift.day_scope,
    })
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || 'Dados de turno inválidos.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      if (editingShiftCode) {
        await api.shifts.update(editingShiftCode, { minutes, day_scope: newShift.day_scope })
      } else {
        await api.shifts.create({
          shift_code: newShift.shift_code.trim(),
          minutes,
          day_scope: newShift.day_scope,
        })
      }
      resetShiftForm()
      await loadShifts()
      toast.success('Turno salvo com sucesso.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar turno')
      toast.error('Não foi possível salvar o turno.')
    } finally {
      setLoading(false)
    }
  }

  const handleEditShift = (shift: Shift) => {
    startEditShift(shift)
  }

  const handleDeleteShift = (shiftCode: string) => {
    setConfirmDialog({ type: 'deleteShift', shiftCode })
  }

  const doDeleteShift = async (shiftCode: string) => {
    setLoading(true)
    setError(null)
    setConfirmDialog(null)
    try {
      await api.shifts.remove(shiftCode)
      if (editingShiftCode === shiftCode) resetShiftForm()
      await loadShifts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao remover turno')
    } finally {
      setLoading(false)
    }
  }

  const getConfirmContent = () => {
    if (!confirmDialog) return null
    switch (confirmDialog.type) {
      case 'clearTemplate':
        return { title: 'Limpar mosaico', description: 'Limpar todo o mosaico atual?', onConfirm: () => doClearTemplateAll() }
      case 'deleteShift':
        return { title: 'Remover turno', description: `Remover turno ${confirmDialog.shiftCode}?`, onConfirm: () => doDeleteShift(confirmDialog.shiftCode) }
      case 'deleteException':
        return { title: 'Remover exceção', description: 'Remover esta exceção?', onConfirm: () => doDeleteException(confirmDialog.ex) }
      case 'deleteDemand':
        return { title: 'Remover demanda', description: 'Remover este slot de demanda?', onConfirm: () => doDeleteDemand(confirmDialog.d) }
      case 'deleteRotation':
        return { title: 'Remover rodízio', description: 'Remover esta entrada do rodízio?', onConfirm: () => doDeleteRotation(confirmDialog.index) }
    }
  }

  const confirmContent = getConfirmContent()
  const releaseTotal = governance?.release_checklist.length || 0
  const releaseDone = governance?.release_checklist.filter((item) => item.done).length || 0
  const governanceReady = !!governance && governance.pending_items.length === 0 && releaseTotal > 0 && releaseDone === releaseTotal
  const filteredAuditEvents = useMemo(
    () =>
      auditEvents.filter((event) => {
        const opOk = auditOperationFilter === 'ALL' || event.operation === auditOperationFilter
        const modeOk = auditModeFilter === 'ALL' || event.mode === auditModeFilter
        return opOk && modeOk
      }),
    [auditEvents, auditModeFilter, auditOperationFilter],
  )

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Configuração</h1>
      {error && <ErrorState message={error} />}
      <AlertDialog open={!!confirmDialog} onOpenChange={(open) => !open && setConfirmDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmContent?.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmContent?.description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirmContent?.onConfirm}>
              Confirmar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <Tabs defaultValue="turnos">
        <TabsList>
          <TabsTrigger value="turnos">Turnos</TabsTrigger>
          <TabsTrigger value="mosaico">Mosaico</TabsTrigger>
          <TabsTrigger value="rodizio">Rodízio</TabsTrigger>
          <TabsTrigger value="excecoes">Férias e ausências</TabsTrigger>
          <TabsTrigger value="demand">Demanda por horário</TabsTrigger>
          <TabsTrigger value="governanca">Governança</TabsTrigger>
        </TabsList>
        <TabsContent value="turnos" className="mt-4">
        <ShiftSection>
          <Card>
            <CardHeader>
              <CardTitle>Turnos</CardTitle>
              <CardDescription>Horários de cada turno (manhã, tarde, domingo).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleSaveShift} className="flex flex-wrap gap-4 items-end p-4 border rounded-lg bg-muted/30">
                <div className="space-y-2">
                  <Label htmlFor="shift-code">Código</Label>
                  <Input
                    id="shift-code"
                    value={newShift.shift_code}
                    onChange={(e) => setNewShift({ ...newShift, shift_code: e.target.value.toUpperCase() })}
                    placeholder="CAI1"
                    className="w-[120px]"
                    disabled={!!editingShiftCode}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="shift-minutes">Duração (min)</Label>
                  <Input
                    id="shift-minutes"
                    type="number"
                    min={0}
                    value={newShift.minutes}
                    onChange={(e) => setNewShift({ ...newShift, minutes: e.target.value })}
                    className="w-[120px]"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="shift-day-scope">Tipo</Label>
                  <Select value={newShift.day_scope} onValueChange={(v) => setNewShift({ ...newShift, day_scope: v })}>
                    <SelectTrigger id="shift-day-scope" className="w-[160px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="WEEKDAY">Dia útil</SelectItem>
                      <SelectItem value="SUNDAY">Domingo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Salvando…' : editingShiftCode ? 'Salvar edição' : 'Adicionar'}
                </Button>
                {editingShiftCode && (
                  <Button type="button" variant="outline" onClick={resetShiftForm}>
                    Cancelar edição
                  </Button>
                )}
              </form>
              <Table>
                <TableCaption>Catálogo de turnos ativos para o setor selecionado.</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Duração</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {shifts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-muted-foreground">
                        Nenhum turno cadastrado. Adicione acima.
                      </TableCell>
                    </TableRow>
                  ) : (
                    shifts.map((s) => (
                      <TableRow key={s.shift_code}>
                        <TableCell>{s.shift_code}</TableCell>
                        <TableCell>{formatMinutes(s.minutes)}</TableCell>
                        <TableCell>{formatDayScope(s.day_scope)}</TableCell>
                        <TableCell className="space-x-2">
                          <Button size="sm" variant="outline" onClick={() => handleEditShift(s)}>
                            Editar
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDeleteShift(s.shift_code)}>
                            Remover
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </ShiftSection>
        </TabsContent>
        <TabsContent value="mosaico" className="mt-4">
        <TemplateSection>
          <Card>
            <CardHeader>
              <CardTitle>Mosaico</CardTitle>
              <CardDescription>Modelo padrão de turnos por dia da semana (SEG–SAB).</CardDescription>
              <CardAction>
                <Button variant="outline" size="sm" onClick={clearTemplateAll}>
                  Limpar todo mosaico (local)
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableCaption>Matriz semanal de turnos base por colaborador.</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[140px]">Colaborador</TableHead>
                      {WEEKDAYS.map((d) => (
                        <TableHead key={d}>{d}</TableHead>
                      ))}
                      <TableHead>Ações</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {employees.map((emp) => (
                      <TableRow key={emp.employee_id}>
                        <TableCell className="font-medium">{emp.name}</TableCell>
                        {WEEKDAYS.map((day) => (
                          <TableCell key={day}>
                            <Select
                              value={getTemplateCell(emp.employee_id, day) || 'empty'}
                              onValueChange={(v) => handleTemplateCellChange(emp.employee_id, day, v === 'empty' ? '' : v, shifts)}
                            >
                              <SelectTrigger className="h-8 w-[100px]">
                                <SelectValue placeholder="—" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="empty">—</SelectItem>
                                {shifts.filter((s) => s.day_scope === 'WEEKDAY' || s.day_scope === 'ANY').map((s) => (
                                  <SelectItem key={s.shift_code} value={s.shift_code}>
                                    {s.shift_code}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                        ))}
                        <TableCell>
                          <Button size="sm" variant="outline" onClick={() => clearTemplateForEmployee(emp.employee_id)}>
                            Limpar linha
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Button onClick={handleSaveTemplate} disabled={loading} className="mt-4">
                {loading ? 'Salvando…' : 'Salvar mosaico'}
              </Button>
            </CardContent>
          </Card>
        </TemplateSection>
        </TabsContent>
        <TabsContent value="rodizio" className="mt-4">
        <RotationSection>
          <Card>
            <CardHeader>
              <CardTitle>Rodízio de domingos</CardTitle>
              <CardDescription>Ordem de quem trabalha aos domingos e como compensa folga.</CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleAddRotation()
                }}
                className="flex flex-wrap gap-4 items-end p-4 border rounded-lg bg-muted/30 mb-4"
              >
                <div className="space-y-2">
                  <Label htmlFor="rotation-index">Posição</Label>
                  <Input
                    id="rotation-index"
                    type="number"
                    min={1}
                    value={newRotation.scale_index}
                    onChange={(e) => setNewRotation({ ...newRotation, scale_index: parseInt(e.target.value, 10) || 1 })}
                    className="w-[80px]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rotation-employee">Colaborador</Label>
                  <Select value={newRotation.employee_id} onValueChange={(v) => setNewRotation({ ...newRotation, employee_id: v })} required>
                    <SelectTrigger id="rotation-employee" className="w-[180px]">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map((e) => (
                        <SelectItem key={e.employee_id} value={e.employee_id}>
                          {e.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rotation-sunday">Domingo</Label>
                  <DateInput
                    id="rotation-sunday"
                    value={newRotation.sunday_date}
                    onChange={(e) => setNewRotation({ ...newRotation, sunday_date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rotation-folga">Folga</Label>
                  <DateInput
                    id="rotation-folga"
                    value={newRotation.folga_date}
                    onChange={(e) => setNewRotation({ ...newRotation, folga_date: e.target.value })}
                  />
                </div>
                <Button type="submit">{editingRotationIndex != null ? 'Salvar edição' : 'Adicionar'}</Button>
                {editingRotationIndex != null && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditingRotationIndex(null)
                      setNewRotation({ scale_index: 1, employee_id: '', sunday_date: '', folga_date: '' })
                    }}
                  >
                    Cancelar edição
                  </Button>
                )}
              </form>
              <Table>
                <TableCaption>Entradas do rodízio de domingos e folgas associadas.</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Posição</TableHead>
                    <TableHead>Colaborador</TableHead>
                    <TableHead>Domingo</TableHead>
                    <TableHead>Folga</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rotationRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-muted-foreground">
                        Nenhum rodízio cadastrado ainda.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rotationRows.map((r, i) => (
                      <TableRow key={`${r.scale_index}-${r.employee_id}-${i}`}>
                        <TableCell>{r.scale_index}</TableCell>
                        <TableCell>{employees.find((e) => e.employee_id === r.employee_id)?.name || r.employee_id}</TableCell>
                        <TableCell>{r.sunday_date}</TableCell>
                        <TableCell>{r.folga_date || '—'}</TableCell>
                        <TableCell className="space-x-2">
                          <Button size="sm" variant="outline" onClick={() => handleEditRotation(r, i)}>
                            Editar
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDeleteRotation(i)}>
                            Remover
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
              <Button onClick={handleSaveRotation} disabled={loading} className="mt-4">
                {loading ? 'Salvando…' : 'Salvar rodízio'}
              </Button>
            </CardContent>
          </Card>
        </RotationSection>
        </TabsContent>
        <TabsContent value="excecoes" className="mt-4">
        <ExceptionSection>
          <Card>
            <CardHeader>
              <CardTitle>Férias e ausências</CardTitle>
              <CardDescription>Datas em que o colaborador não pode trabalhar — férias, atestados, trocas.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleAddException} className="flex flex-wrap gap-4 items-end p-4 border rounded-lg bg-muted/30">
                <div className="space-y-2">
                  <Label htmlFor="exception-employee">Colaborador</Label>
                  <Select value={newExc.employee_id} onValueChange={(v) => setNewExc({ ...newExc, employee_id: v })} required>
                    <SelectTrigger id="exception-employee" className="w-[180px]">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map((e) => (
                        <SelectItem key={e.employee_id} value={e.employee_id}>
                          {e.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exception-date">Data</Label>
                  <DateInput
                    id="exception-date"
                    value={newExc.exception_date}
                    onChange={(e) => setNewExc({ ...newExc, exception_date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exception-type">Tipo</Label>
                  <Select value={newExc.exception_type} onValueChange={(v) => setNewExc({ ...newExc, exception_type: v })}>
                    <SelectTrigger id="exception-type" className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="VACATION">Férias</SelectItem>
                      <SelectItem value="MEDICAL_LEAVE">Atestado</SelectItem>
                      <SelectItem value="SWAP">Troca</SelectItem>
                      <SelectItem value="BLOCK">Bloqueio</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exception-note">Observação</Label>
                  <Input
                    id="exception-note"
                    placeholder="Opcional"
                    value={newExc.note}
                    onChange={(e) => setNewExc({ ...newExc, note: e.target.value })}
                    className="w-[180px]"
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Salvando…' : editingExceptionKey ? 'Salvar edição' : 'Adicionar'}
                </Button>
                {editingExceptionKey && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditingExceptionKey(null)
                      setNewExc({ employee_id: '', exception_date: '', exception_type: 'VACATION', note: '' })
                    }}
                  >
                    Cancelar edição
                  </Button>
                )}
              </form>
              <Table>
                <TableCaption>Exceções operacionais cadastradas para o período.</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Colaborador</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Observação</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {exceptions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-muted-foreground">
                        Nenhuma exceção. Adicione acima.
                      </TableCell>
                    </TableRow>
                  ) : (
                    exceptions.map((ex, i) => (
                      <TableRow key={`${ex.employee_id}-${ex.exception_date}-${i}`}>
                        <TableCell>{employees.find((e) => e.employee_id === ex.employee_id)?.name || ex.employee_id}</TableCell>
                        <TableCell>{ex.exception_date}</TableCell>
                        <TableCell>{ex.exception_type === 'VACATION' ? 'Férias' : ex.exception_type === 'MEDICAL_LEAVE' ? 'Atestado' : ex.exception_type}</TableCell>
                        <TableCell>{ex.note || '—'}</TableCell>
                        <TableCell className="space-x-2">
                          <Button size="sm" variant="outline" onClick={() => handleEditException(ex)}>
                            Editar
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDeleteException(ex)}>
                            Remover
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </ExceptionSection>
        </TabsContent>
        <TabsContent value="demand" className="mt-4">
        <DemandSection>
          <Card>
            <CardHeader>
              <CardTitle>Demanda por horário</CardTitle>
              <CardDescription>Quantidade de pessoas necessárias em cada período do dia.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleAddDemand} className="flex flex-wrap gap-4 items-end p-4 border rounded-lg bg-muted/30">
                <div className="space-y-2">
                  <Label htmlFor="demand-date">Data</Label>
                  <DateInput
                    id="demand-date"
                    value={newDemand.work_date}
                    onChange={(e) => setNewDemand({ ...newDemand, work_date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="demand-slot">Horário (slot)</Label>
                  <Select value={newDemand.slot_start} onValueChange={(v) => setNewDemand({ ...newDemand, slot_start: v })}>
                    <SelectTrigger id="demand-slot" className="w-[120px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00'].map((t) => (
                        <SelectItem key={t} value={t}>
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="demand-min-required">Mín. pessoas</Label>
                  <Input
                    id="demand-min-required"
                    type="number"
                    min={1}
                    value={newDemand.min_required}
                    onChange={(e) => setNewDemand({ ...newDemand, min_required: e.target.value })}
                    className="w-[100px]"
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Salvando…' : editingDemandKey ? 'Salvar edição' : 'Adicionar'}
                </Button>
                {editingDemandKey && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditingDemandKey(null)
                      setNewDemand({ work_date: '', slot_start: '08:00', min_required: '1' })
                    }}
                  >
                    Cancelar edição
                  </Button>
                )}
              </form>
              <Table>
                <TableCaption>Slots de demanda por data e horário.</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead>Horário</TableHead>
                    <TableHead>Mín. pessoas</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {demandSlots.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-muted-foreground">
                        Nenhum slot de demanda. Adicione acima.
                      </TableCell>
                    </TableRow>
                  ) : (
                    demandSlots.map((d, i) => (
                      <TableRow key={`${d.work_date}-${d.slot_start}-${i}`}>
                        <TableCell>{d.work_date}</TableCell>
                        <TableCell>{d.slot_start}</TableCell>
                        <TableCell>{d.min_required}</TableCell>
                        <TableCell className="space-x-2">
                          <Button size="sm" variant="outline" onClick={() => handleEditDemand(d)}>
                            Editar
                          </Button>
                          <Button size="sm" variant="destructive" onClick={() => handleDeleteDemand(d)}>
                            Remover
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </DemandSection>
        </TabsContent>
        <TabsContent value="governanca" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Governança operacional (jurídico e marcadores)</CardTitle>
              <CardDescription>
                Defina semântica dos marcadores 5/6 e registre validação legal de domingo/feriado.
              </CardDescription>
              <CardAction className="flex gap-2">
                <Button type="button" variant="outline" onClick={handleReloadGovernance} disabled={loading}>
                  Recarregar
                </Button>
                <Button type="button" variant="outline" onClick={handleApplyGovernanceDefaults} disabled={loading}>
                  Aplicar padrão (5/6)
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="space-y-4">
              {runtimeMode && (
                <div className="space-y-3 rounded-md border p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium">Modo de execução operacional</p>
                    <Badge variant={runtimeMode.mode === 'ESTRITO' ? 'destructive' : 'secondary'}>
                      {runtimeMode.mode}
                    </Badge>
                    <Badge variant="outline">Fonte: {runtimeMode.source}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-3 items-end">
                    <div className="space-y-2">
                      <Label htmlFor="runtime-mode">Modo</Label>
                      <Select
                        value={runtimeMode.mode}
                        onValueChange={(v) =>
                          setRuntimeMode((prev) => (prev ? { ...prev, mode: v as 'NORMAL' | 'ESTRITO' } : prev))
                        }
                      >
                        <SelectTrigger id="runtime-mode" className="w-[180px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORMAL">NORMAL</SelectItem>
                          <SelectItem value="ESTRITO">ESTRITO</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="runtime-actor-role">Papel da ação</Label>
                      <Select value={runtimeActorRole} onValueChange={(v) => setRuntimeActorRole(v as 'ADMIN' | 'OPERADOR')}>
                        <SelectTrigger id="runtime-actor-role" className="w-[180px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ADMIN">ADMIN</SelectItem>
                          <SelectItem value="OPERADOR">OPERADOR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button type="button" onClick={handleSaveRuntimeMode} disabled={loading}>
                      {loading ? 'Salvando...' : 'Salvar modo'}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Atualizado por {runtimeMode.updated_by_role || 'N/A'} em{' '}
                    {runtimeMode.updated_at ? formatDateTimeBR(runtimeMode.updated_at) : 'N/A'}.
                  </p>
                  {runtimeMode.mode === 'ESTRITO' && (
                    <p className="text-xs text-amber-700 dark:text-amber-300">
                      Em ESTRITO, avisos LEGAL_SOFT exigem justificativa para continuidade no fluxo de escala.
                    </p>
                  )}
                </div>
              )}

              {!governance ? (
                <p className="text-sm text-muted-foreground">Carregando governança…</p>
              ) : (
                <form onSubmit={handleSaveGovernance} className="space-y-4">
                  <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/30 p-3">
                    <Badge variant={governanceReady ? 'secondary' : 'destructive'}>
                      Checklist de liberação: {releaseDone}/{releaseTotal}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Em modo estrito, pendências desta seção podem bloquear gerar e simular escala.
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {governance.accepted_dom_folgas_markers.map((marker) => (
                      <div key={marker} className="space-y-2">
                        <Label htmlFor={`gov-marker-${marker}`}>Marcador {marker}</Label>
                        <Input
                          id={`gov-marker-${marker}`}
                          value={governance.marker_semantics[marker] || ''}
                          onChange={(e) =>
                            setGovernance((prev) =>
                              prev
                                ? {
                                    ...prev,
                                    marker_semantics: {
                                      ...prev.marker_semantics,
                                      [marker]: e.target.value.toUpperCase(),
                                    },
                                  }
                                : prev
                            )
                          }
                          placeholder="Ex.: COMPENSA_48H / ESCALA_6X1"
                        />
                      </div>
                    ))}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gov-cct-id">Identificador CCT vigente</Label>
                    <Input
                      id="gov-cct-id"
                      value={governance.collective_agreement_id}
                      onChange={(e) =>
                        setGovernance((prev) => (prev ? { ...prev, collective_agreement_id: e.target.value } : prev))
                      }
                      placeholder="Ex.: CCT_CAIXA_PR_2026_01"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gov-legal-validation">Validação jurídica domingo/feriado</Label>
                    <Select
                      value={governance.sunday_holiday_legal_validated ? 'YES' : 'NO'}
                      onValueChange={(v) =>
                        setGovernance((prev) =>
                          prev ? { ...prev, sunday_holiday_legal_validated: v === 'YES' } : prev
                        )
                      }
                    >
                      <SelectTrigger id="gov-legal-validation" className="w-[220px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NO">Pendente</SelectItem>
                        <SelectItem value="YES">Concluída</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gov-legal-note">Observação jurídica</Label>
                    <Input
                      id="gov-legal-note"
                      value={governance.legal_validation_note || ''}
                      onChange={(e) =>
                        setGovernance((prev) => (prev ? { ...prev, legal_validation_note: e.target.value } : prev))
                      }
                      placeholder="Base legal, parecer interno, observações…"
                    />
                  </div>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando…' : 'Salvar governança'}
                  </Button>
                </form>
              )}

              {governance && (
                <div className="space-y-2 rounded-md border p-3">
                  <p className="text-sm font-medium">Pendências abertas</p>
                  {governance.pending_items.length === 0 ? (
                    <Badge variant="secondary">Governança pronta</Badge>
                  ) : (
                    <ul className="text-sm list-disc pl-5 space-y-1 text-amber-700 dark:text-amber-300">
                      {governance.pending_items.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {governance && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Checklist de aceite final</p>
                  <Table>
                    <TableCaption>Status dos critérios obrigatórios para liberar execução em produção.</TableCaption>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Detalhe</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {governance.release_checklist.map((item) => (
                        <TableRow key={item.item_id}>
                          <TableCell>{item.title}</TableCell>
                          <TableCell>
                            <Badge variant={item.done ? 'secondary' : 'destructive'}>
                              {item.done ? 'Concluído' : 'Pendente'}
                            </Badge>
                          </TableCell>
                          <TableCell>{item.detail || '—'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              <div className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">Trilha de auditoria (risco legal em execução)</p>
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="space-y-1">
                      <Label htmlFor="audit-operation-filter" className="text-xs text-muted-foreground">Operação</Label>
                      <Select value={auditOperationFilter} onValueChange={(v) => setAuditOperationFilter(v as 'ALL' | 'GENERATE' | 'SIMULATE')}>
                        <SelectTrigger id="audit-operation-filter" className="w-[150px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ALL">Todas</SelectItem>
                          <SelectItem value="GENERATE">Gerar escala</SelectItem>
                          <SelectItem value="SIMULATE">Simular período</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="audit-mode-filter" className="text-xs text-muted-foreground">Modo</Label>
                      <Select value={auditModeFilter} onValueChange={(v) => setAuditModeFilter(v as 'ALL' | 'NORMAL' | 'ESTRITO')}>
                        <SelectTrigger id="audit-mode-filter" className="w-[140px] h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ALL">Todos</SelectItem>
                          <SelectItem value="NORMAL">NORMAL</SelectItem>
                          <SelectItem value="ESTRITO">ESTRITO</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button type="button" variant="outline" size="sm" onClick={loadGovernanceAudit} disabled={loading}>
                      Atualizar auditoria
                    </Button>
                  </div>
                </div>
                <Table>
                  <TableCaption>Eventos mais recentes de confirmação explícita em modo estrito.</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Data</TableHead>
                      <TableHead>Operação</TableHead>
                      <TableHead>Modo</TableHead>
                      <TableHead>Papel</TableHead>
                      <TableHead>Período</TableHead>
                      <TableHead>Warnings</TableHead>
                      <TableHead>Motivo</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredAuditEvents.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-muted-foreground">
                          Nenhum evento encontrado para os filtros selecionados.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredAuditEvents.map((event) => (
                        <TableRow key={event.event_id}>
                          <TableCell>{formatDateTimeBR(event.created_at)}</TableCell>
                          <TableCell>{event.operation}</TableCell>
                          <TableCell>{event.mode}</TableCell>
                          <TableCell>{event.actor_role}</TableCell>
                          <TableCell>
                            {event.period_start && event.period_end ? `${event.period_start} a ${event.period_end}` : '—'}
                          </TableCell>
                          <TableCell>{event.warnings.length}</TableCell>
                          <TableCell>{event.reason || '—'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
