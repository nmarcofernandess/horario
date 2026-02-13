import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DateInput } from '@/components/ui/date-input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { EmptyState, ErrorState } from '@/components/feedback-state'
import { api, ApiError } from '@/lib/api'
import { toast } from 'sonner'
import {
  formatDateBR,
  formatMinutes,
  formatStatus,
  formatShift,
  formatRule,
  formatSeverity,
  pluralize,
} from '@/lib/format'
import { Circle, ChevronDownIcon, CheckCircle2Icon, AlertTriangleIcon } from 'lucide-react'

const COPY = {
  preflightTitle: 'Validação operacional',
  preflightNotRun: 'A validação ainda não foi executada para este período.',
  preflightLoading: 'Validando regras e governança para o período selecionado...',
  preflightReady: 'Sem bloqueios. Execução liberada.',
  preflightAckRequired: 'Execução possível com justificativa obrigatória (risco legal/compliance).',
  preflightBlocked: 'Há bloqueio operacional ativo. Ajuste a configuração antes de executar.',
  preflightFailed: 'Não foi possível validar as condições de execução.',
  preflightBlockedToast: 'A operação foi bloqueada por inconsistência de configuração.',
  preflightRetryToast: 'Falha ao revalidar as condições de execução.',
  simulationBanner: 'Simulação do período.',
  ackTitle: 'Continuar com risco legal',
  ackDescription: 'Modo estrito exige justificativa para seguir quando houver pendência legal/compliance.',
  ackReasonHint: 'Mínimo recomendado: 10 caracteres',
  ackReasonInvalid: 'Informe um motivo válido para continuar com risco.',
} as const

type Assignment = {
  work_date: string
  employee_id: string
  employee_name?: string
  status: string
  shift_code?: string
  minutes: number
}

type WeeklySummaryRow = {
  window: 'MON_SUN' | 'SUN_SAT'
  week_start: string
  week_end: string
  employee_id: string
  employee_name?: string
  contract_code: string
  actual_minutes: number
  target_minutes: number
  delta_minutes: number
  status: 'OK' | 'OUT'
}

const statusBadgeVariants = cva(
  'inline-flex min-w-[4rem] items-center justify-center rounded px-2 py-0.5 text-center text-xs font-medium',
  {
    variants: {
      tone: {
        work: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
        sunday: 'bg-blue-500/15 text-blue-700 dark:text-blue-300',
        folga: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
        absence: 'bg-destructive/15 text-destructive',
        neutral: 'bg-muted text-muted-foreground',
      },
    },
    defaultVariants: {
      tone: 'neutral',
    },
  },
)

function CellStatus({ status, shiftCode }: { status: string; shiftCode?: string }) {
  const isDom = shiftCode === 'DOM_08_12_30' || shiftCode === 'H_DOM'
  const tone =
    status === 'WORK' ? (isDom ? 'sunday' : 'work') : status === 'FOLGA' ? 'folga' : status === 'ABSENCE' ? 'absence' : 'neutral'
  const label = status === 'WORK' && shiftCode ? formatShift(shiftCode) : formatStatus(status)
  return (
    <span className={cn(statusBadgeVariants({ tone }))}>
      {label}
    </span>
  )
}

export function EscalaPage() {
  const [periodStart, setPeriodStart] = useState('2026-02-08')
  const [periodEnd, setPeriodEnd] = useState('2026-03-31')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [violations, setViolations] = useState<Array<{ employee_id: string; employee_name?: string; rule_code: string; rule_label?: string; severity: string; detail: string }>>([])
  const [simAssignments, setSimAssignments] = useState<Assignment[]>([])
  const [simViolations, setSimViolations] = useState<Array<{ employee_id: string; employee_name?: string; rule_code: string; rule_label?: string; severity: string; detail: string }>>([])
  const [isSimulationView, setIsSimulationView] = useState(false)
  const [lastResult, setLastResult] = useState<{ assignments_count: number; violations_count: number } | null>(null)
  const [lastSimulation, setLastSimulation] = useState<{ assignments_count: number; violations_count: number } | null>(null)
  const [weeklyWindow, setWeeklyWindow] = useState<'MON_SUN' | 'SUN_SAT'>('MON_SUN')
  const [weeklyAnalysis, setWeeklyAnalysis] = useState<{
    policy_week_definition: 'MON_SUN' | 'SUN_SAT'
    tolerance_minutes: number
    summaries_mon_sun: WeeklySummaryRow[]
    summaries_sun_sat: WeeklySummaryRow[]
    external_dependencies_open: string[]
  } | null>(null)
  const [preflight, setPreflight] = useState<{
    mode: 'NORMAL' | 'ESTRITO'
    blockers: Array<{ code: string; message: string; recommended_action: string }>
    critical_warnings: Array<{ code: string; message: string; recommended_action: string }>
    can_proceed: boolean
    ack_required: boolean
  } | null>(null)
  const [ackDialogOpen, setAckDialogOpen] = useState(false)
  const [ackReason, setAckReason] = useState('')
  const [pendingOperation, setPendingOperation] = useState<'GENERATE' | 'SIMULATE' | null>(null)
  const [preflightLoading, setPreflightLoading] = useState(false)

  const loadData = async () => {
    try {
      setError(null)
      const [a, v] = await Promise.all([api.scale.getAssignments(), api.scale.getViolations()])
      setAssignments(a)
      setViolations(v)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar dados')
      toast.error('Não foi possível carregar os dados da escala.')
    }
  }

  const loadWeeklyAnalysis = async (mode: 'OFFICIAL' | 'SIMULATION') => {
    const summary = await api.scale.weeklyAnalysis({
      period_start: periodStart,
      period_end: periodEnd,
      sector_id: 'CAIXA',
      mode,
    })
    setWeeklyAnalysis(summary)
  }

  useEffect(() => {
    loadData()
    loadWeeklyAnalysis('OFFICIAL').catch(() => {
      // Mantém tela funcional se endpoint ainda estiver indisponível.
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount
  }, [])

  const PAGE_SIZE = 20
  const [tablePage, setTablePage] = useState(0)
  const activeAssignments = isSimulationView ? simAssignments : assignments
  const activeViolations = isSimulationView ? simViolations : violations
  const paginatedAssignments = useMemo(() => {
    const start = tablePage * PAGE_SIZE
    return activeAssignments.slice(start, start + PAGE_SIZE)
  }, [activeAssignments, tablePage])
  const totalPages = Math.ceil(activeAssignments.length / PAGE_SIZE) || 1
  const preflightSignal = useMemo(() => {
    if (preflightLoading) {
      return { label: 'VALIDANDO', variant: 'outline' as const, description: COPY.preflightLoading }
    }
    if (!preflight) {
      return { label: 'AGUARDANDO', variant: 'outline' as const, description: COPY.preflightNotRun }
    }
    if (preflight.blockers.length > 0 || !preflight.can_proceed) {
      return { label: 'BLOQUEADO', variant: 'destructive' as const, description: COPY.preflightBlocked }
    }
    if (preflight.ack_required) {
      return { label: 'RISCO LEGAL', variant: 'destructive' as const, description: COPY.preflightAckRequired }
    }
    return { label: 'LIBERADO', variant: 'secondary' as const, description: COPY.preflightReady }
  }, [preflight, preflightLoading])

  useEffect(() => {
    setTablePage((current) => Math.min(current, Math.max(0, totalPages - 1)))
  }, [totalPages])

  const { dates, employees, matrix, empNames } = useMemo(() => {
    const dates = [...new Set(assignments.map((a) => a.work_date))].sort()
    const empIds = [...new Set(assignments.map((a) => a.employee_id))].sort()
    const names: Record<string, string> = {}
    assignments.forEach((a) => {
      if (a.employee_name) names[a.employee_id] = a.employee_name
    })
    const map = new Map<string, Map<string, { status: string; shiftCode?: string }>>()
    assignments.forEach((a) => {
      if (!map.has(a.work_date)) map.set(a.work_date, new Map())
      map.get(a.work_date)!.set(a.employee_id, { status: a.status, shiftCode: a.shift_code })
    })
    return {
      dates,
      employees: empIds,
      matrix: map,
      empNames: names,
    }
  }, [assignments])

  const runOperation = async (
    operation: 'GENERATE' | 'SIMULATE',
    riskAck?: { actor_role: string; reason: string }
  ) => {
    setLoading(true)
    setError(null)
    try {
      setTablePage(0)
      if (operation === 'GENERATE') {
        const result = await api.scale.generate({
          period_start: periodStart,
          period_end: periodEnd,
          sector_id: 'CAIXA',
          risk_ack: riskAck,
        })
        setLastResult({ assignments_count: result.assignments_count, violations_count: result.violations_count })
        await loadData()
        await loadWeeklyAnalysis('OFFICIAL')
        setIsSimulationView(false)
        setSimAssignments([])
        setSimViolations([])
        toast.success('Escala oficial gerada com sucesso.')
      } else {
        const result = await api.scale.simulate({
          period_start: periodStart,
          period_end: periodEnd,
          sector_id: 'CAIXA',
          risk_ack: riskAck,
        })
        setSimAssignments(result.assignments)
        setSimViolations(result.violations)
        setLastSimulation({ assignments_count: result.assignments_count, violations_count: result.violations_count })
        await loadWeeklyAnalysis('SIMULATION')
        setIsSimulationView(true)
        toast.success('Simulação executada com sucesso.')
      }
      setPendingOperation(null)
      setAckDialogOpen(false)
      setAckReason('')
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const detail = e.detail as
          | { critical_warnings?: Array<{ code: string; message: string; recommended_action: string }>; message?: string }
          | undefined
        setPreflight((prev) =>
          prev
            ? {
              ...prev,
              critical_warnings: detail?.critical_warnings || prev.critical_warnings,
              ack_required: true,
            }
            : prev
        )
        setPendingOperation(operation)
        setAckDialogOpen(true)
      } else {
        setError(e instanceof Error ? e.message : 'Erro ao executar operação')
        toast.error(operation === 'GENERATE' ? 'Não foi possível gerar a escala.' : 'Não foi possível simular o período.')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadPreflight = async () => {
    setPreflightLoading(true)
    try {
      const pre = await api.scale.preflight({ period_start: periodStart, period_end: periodEnd, sector_id: 'CAIXA' })
      setPreflight(pre)
      return pre
    } finally {
      setPreflightLoading(false)
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const pre = await loadPreflight()
      if (!pre.can_proceed) {
        const firstBlocker = pre.blockers[0]
        setError(firstBlocker?.message || 'Bloqueio operacional identificado na validação.')
        toast.error(COPY.preflightBlockedToast)
        return
      }
      if (pre.ack_required) {
        setPendingOperation('GENERATE')
        setAckDialogOpen(true)
        return
      }
      await runOperation('GENERATE')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro na validação operacional')
      toast.error(COPY.preflightFailed)
    } finally {
      setLoading(false)
    }
  }

  const handleSimulate = async () => {
    setLoading(true)
    setError(null)
    try {
      const pre = await loadPreflight()
      if (!pre.can_proceed) {
        const firstBlocker = pre.blockers[0]
        setError(firstBlocker?.message || 'Bloqueio operacional identificado na validação.')
        toast.error(COPY.preflightBlockedToast)
        return
      }
      if (pre.ack_required) {
        setPendingOperation('SIMULATE')
        setAckDialogOpen(true)
        return
      }
      await runOperation('SIMULATE')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro na validação operacional')
      toast.error(COPY.preflightFailed)
    } finally {
      setLoading(false)
    }
  }

  const handleExportHtml = () => {
    window.open(api.export.html(), '_blank')
  }

  const handleExportMd = () => {
    window.open(api.export.markdown(), '_blank')
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">Escala de Trabalho</h1>
      <AlertDialog open={ackDialogOpen} onOpenChange={setAckDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{COPY.ackTitle}</AlertDialogTitle>
            <AlertDialogDescription>
              {COPY.ackDescription}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2">
            <Label htmlFor="ack-reason">Motivo obrigatório</Label>
            <Input
              id="ack-reason"
              value={ackReason}
              onChange={(e) => setAckReason(e.target.value)}
              placeholder="Descreva por que a operação precisa seguir agora."
            />
            <p className="text-xs text-muted-foreground">
              {COPY.ackReasonHint} ({ackReason.trim().length}/10).
            </p>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setPendingOperation(null)
                setAckReason('')
              }}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault()
                if (!pendingOperation || ackReason.trim().length < 10) {
                  toast.error(COPY.ackReasonInvalid)
                  return
                }
                runOperation(pendingOperation, { actor_role: 'OPERADOR', reason: ackReason.trim() }).catch(() => undefined)
              }}
            >
              Continuar e registrar justificativa
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {preflight && preflight.critical_warnings.length > 0 && (
        <div className="rounded border border-amber-400/40 bg-amber-50 dark:bg-amber-900/20 p-3">
          <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">
            Risco legal/compliance ({preflight.mode}) - operação permitida com governança
          </p>
          <ul className="text-sm text-amber-900 dark:text-amber-100 list-disc pl-5 space-y-1">
            {preflight.critical_warnings.map((item) => (
              <li key={item.code}>
                {item.message} - <span className="font-medium">{item.recommended_action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {preflight && preflight.blockers.length > 0 && (
        <div className="rounded border border-destructive/40 bg-destructive/10 p-3">
          <p className="text-sm font-medium text-destructive mb-2">Impossível lógico (bloqueado)</p>
          <ul className="text-sm text-destructive list-disc pl-5 space-y-1">
            {preflight.blockers.map((item) => (
              <li key={item.code}>
                {item.message} - <span className="font-medium">{item.recommended_action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Período</CardTitle>
          <CardDescription>Valida o cenário antes de gerar ou simular a escala.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 1. Período + Ações — fluxo principal */}
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="period-start" className="text-muted-foreground">De</Label>
                <DateInput id="period-start" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="period-end" className="text-muted-foreground">Até</Label>
                <DateInput id="period-end" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleGenerate} disabled={loading}>
                {loading ? 'Gerando...' : 'Gerar escala'}
              </Button>
              <Button variant="outline" onClick={handleSimulate} disabled={loading}>
                {loading ? 'Simulando...' : 'Simular período'}
              </Button>
              {isSimulationView && (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setIsSimulationView(false)
                    setTablePage(0)
                  }}
                >
                  Ver escala oficial
                </Button>
              )}
            </div>
          </div>

          {/* 2. Status — só quando há problema (BLOQUEADO, RISCO LEGAL) */}
          {preflightSignal.label !== 'LIBERADO' && preflightSignal.label !== 'AGUARDANDO' && (
            <div className="flex flex-wrap items-center gap-2">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive hover:bg-destructive/20"
                      onClick={() => loadPreflight().catch(() => toast.error(COPY.preflightRetryToast))}
                      disabled={loading || preflightLoading}
                    >
                      <Circle className="size-3 fill-current" />
                      {preflightSignal.label}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{preflightSignal.description}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => loadPreflight().catch(() => toast.error(COPY.preflightRetryToast))}
                disabled={loading || preflightLoading}
              >
                {preflightLoading ? 'Revalidando...' : 'Revalidar'}
              </Button>
            </div>
          )}

          {/* 3. Feedback */}
          {error && <ErrorState message={error} />}
          {isSimulationView && (
            <p className="text-sm text-amber-700 dark:text-amber-300">
              {COPY.simulationBanner}
            </p>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleExportHtml}>Exportar para impressão</Button>
        <Button variant="outline" size="sm" onClick={handleExportMd}>Exportar texto</Button>
      </div>

      <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
        <Collapsible defaultOpen className="group/collapsible">
          <CollapsibleTrigger asChild>
            <button className="flex w-full items-start justify-between gap-4 px-6 py-6 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <CardTitle>Aderência de contrato</CardTitle>
                  {(() => {
                    const n = (isSimulationView ? lastSimulation?.violations_count : lastResult?.violations_count) ?? 0
                    return n > 0 ? (
                      <Badge variant="destructive" className="shrink-0">
                        {n}
                      </Badge>
                    ) : null
                  })()}
                </div>
                <CardDescription>
                  Análise semanal da carga horária por janela de corte e status de governança.
                </CardDescription>
              </div>
              <ChevronDownIcon className="mt-1 size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180" />
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="border-t" />
            <div className="px-6 pb-6 pt-6 flex flex-col gap-6">
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant={weeklyWindow === 'MON_SUN' ? 'default' : 'outline'}
                  onClick={() => setWeeklyWindow('MON_SUN')}
                >
                  Segunda a Domingo
                </Button>
                <Button
                  size="sm"
                  variant={weeklyWindow === 'SUN_SAT' ? 'default' : 'outline'}
                  onClick={() => setWeeklyWindow('SUN_SAT')}
                >
                  Domingo a Sábado
                </Button>
              </div>

              {weeklyAnalysis && weeklyAnalysis.external_dependencies_open.length > 0 && (
                <div className="rounded border border-amber-400/40 bg-amber-50 dark:bg-amber-900/20 p-3">
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-2">
                    Governança e Compliance Legal
                  </p>
                  <ul className="text-sm text-amber-900 dark:text-amber-100 list-disc pl-5 space-y-1">
                    {weeklyAnalysis.external_dependencies_open.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {weeklyAnalysis && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Semana</TableHead>
                      <TableHead>Colaborador</TableHead>
                      <TableHead>Contrato</TableHead>
                      <TableHead className="text-right">Real</TableHead>
                      <TableHead className="text-right">Meta</TableHead>
                      <TableHead className="text-right">Delta</TableHead>
                      <TableHead className="text-center">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(weeklyWindow === 'MON_SUN'
                      ? weeklyAnalysis.summaries_mon_sun
                      : weeklyAnalysis.summaries_sun_sat
                    ).map((r, i) => (
                      <TableRow key={`${r.week_start}-${r.employee_id}-${i}`}>
                        <TableCell>
                          <span className="text-xs text-muted-foreground">
                            {formatDateBR(r.week_start)} – {formatDateBR(r.week_end)}
                          </span>
                        </TableCell>
                        <TableCell>{r.employee_name || r.employee_id}</TableCell>
                        <TableCell>{r.contract_code}</TableCell>
                        <TableCell className="text-right font-mono">{formatMinutes(r.actual_minutes)}</TableCell>
                        <TableCell className="text-right font-mono">{formatMinutes(r.target_minutes)}</TableCell>
                        <TableCell className="text-right font-mono">
                          <span
                            className={
                              r.delta_minutes === 0
                                ? 'text-muted-foreground'
                                : r.delta_minutes > 0
                                  ? 'text-amber-600 dark:text-amber-400'
                                  : 'text-destructive'
                            }
                          >
                            {r.delta_minutes > 0 ? '+' : ''}{formatMinutes(r.delta_minutes)}
                          </span>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant={r.status === 'OK' ? 'secondary' : 'destructive'} className="gap-1">
                            {r.status === 'OK' ? (
                              <>
                                <CheckCircle2Icon className="size-3" />
                                Dentro
                              </>
                            ) : (
                              <>
                                <AlertTriangleIcon className="size-3" />
                                Fora
                              </>
                            )}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Alocações</CardTitle>
          <CardDescription>
            {activeAssignments.length === 0
              ? 'Nenhuma alocação. Clique em "Gerar escala" para gerar.'
              : pluralize(activeAssignments.length, 'registro')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="calendario">
            <TabsList>
              <TabsTrigger value="calendario">Calendário</TabsTrigger>
              <TabsTrigger value="tabela">Tabela</TabsTrigger>
            </TabsList>
            <TabsContent value="calendario" className="mt-4">
              {activeAssignments.length === 0 ? (
                <EmptyState
                  className="py-8"
                  message='Execute "Gerar escala" ou "Simular período" para ver o calendário.'
                />
              ) : (
                <div className="overflow-x-auto -mx-2">
                  <Table className="w-full border-collapse text-sm">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-left p-2 border-b border-r font-medium bg-muted/50 sticky left-0 z-10 min-w-[5rem]">
                          Data
                        </TableHead>
                        {employees.map((empId) => (
                          <TableHead
                            key={empId}
                            className="text-center p-2 border-b font-medium bg-muted/50 min-w-[5rem] whitespace-nowrap"
                          >
                            {empNames[empId] || empId}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {dates.map((date) => (
                        <TableRow key={date}>
                          <TableCell className="p-2 border-b border-r font-medium sticky left-0 bg-background z-[1]">
                            {formatDateBR(date)}
                          </TableCell>
                          {employees.map((empId) => {
                            const cell = matrix.get(date)?.get(empId)
                            return (
                              <TableCell key={empId} className="p-1 border-b text-center">
                                {cell ? (
                                  <CellStatus status={cell.status} shiftCode={cell.shiftCode} />
                                ) : (
                                  <span className="text-muted-foreground">—</span>
                                )}
                              </TableCell>
                            )
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>
            <TabsContent value="tabela" className="mt-4">
              <Table>
                <TableCaption>Visão tabular paginada das alocações do período selecionado.</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead>Colaborador</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Turno</TableHead>
                    <TableHead>Carga</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedAssignments.map((a, i) => (
                    <TableRow key={`${a.work_date}-${a.employee_id}-${i}`}>
                      <TableCell>{formatDateBR(a.work_date)}</TableCell>
                      <TableCell>{a.employee_name || a.employee_id}</TableCell>
                      <TableCell>
                        <CellStatus status={a.status} shiftCode={a.shift_code} />
                      </TableCell>
                      <TableCell>{formatShift(a.shift_code)}</TableCell>
                      <TableCell>{formatMinutes(a.minutes)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
                <TableFooter>
                  <TableRow>
                    <TableCell colSpan={5}>{activeAssignments.length} registros totais no período.</TableCell>
                  </TableRow>
                </TableFooter>
              </Table>
              {activeAssignments.length > PAGE_SIZE && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-muted-foreground">
                    Página {tablePage + 1} de {totalPages} — {activeAssignments.length} registros
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTablePage((p) => Math.max(0, p - 1))}
                      disabled={tablePage === 0}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTablePage((p) => Math.min(totalPages - 1, p + 1))}
                      disabled={tablePage >= totalPages - 1}
                    >
                      Próxima
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

    </div>
  )
}
