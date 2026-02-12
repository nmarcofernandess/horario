import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { api } from '@/lib/api'
import {
  formatDateBR,
  formatMinutes,
  formatStatus,
  formatShift,
  formatRule,
  formatSeverity,
  pluralize,
} from '@/lib/format'

export function EscalaPage() {
  const [periodStart, setPeriodStart] = useState('2026-02-08')
  const [periodEnd, setPeriodEnd] = useState('2026-03-31')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [assignments, setAssignments] = useState<Array<{ work_date: string; employee_id: string; employee_name?: string; status: string; shift_code?: string; minutes: number }>>([])
  const [violations, setViolations] = useState<Array<{ employee_id: string; rule_code: string; severity: string; detail: string }>>([])
  const [lastResult, setLastResult] = useState<{ assignments_count: number; violations_count: number } | null>(null)

  const loadData = async () => {
    try {
      setError(null)
      const [a, v] = await Promise.all([api.scale.getAssignments(), api.scale.getViolations()])
      setAssignments(a)
      setViolations(v)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar dados')
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.scale.generate({ period_start: periodStart, period_end: periodEnd, sector_id: 'CAIXA' })
      setLastResult({ assignments_count: result.assignments_count, violations_count: result.violations_count })
      await loadData()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao gerar escala')
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

      <Card>
        <CardHeader>
          <CardTitle>Período</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 flex-wrap items-end">
            <div>
              <label className="text-sm text-muted-foreground mb-2 block">De</label>
              <Input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-2 block">Até</label>
              <Input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} />
            </div>
            <Button onClick={handleGenerate} disabled={loading}>
              {loading ? 'Gerando...' : 'Atualizar escala'}
            </Button>
          </div>
          {error && <p className="text-destructive text-sm">{error}</p>}
          {lastResult && (
            <p className="text-sm text-muted-foreground">
              Última geração: {pluralize(lastResult.assignments_count, 'alocação')}
              {lastResult.violations_count > 0 && `, ${pluralize(lastResult.violations_count, 'alerta')}`}.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleExportHtml}>Exportar para impressão</Button>
        <Button variant="outline" size="sm" onClick={handleExportMd}>Exportar texto</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Alocações</CardTitle>
          <p className="text-sm text-muted-foreground">
            {assignments.length === 0
              ? 'Nenhuma alocação. Clique em "Atualizar escala" para gerar.'
              : pluralize(assignments.length, 'registro')}
          </p>
        </CardHeader>
        <CardContent>
          <Table>
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
              {assignments.slice(0, 50).map((a, i) => (
                <TableRow key={i}>
                  <TableCell>{formatDateBR(a.work_date)}</TableCell>
                  <TableCell>{a.employee_name || a.employee_id}</TableCell>
                  <TableCell>
                    <Badge variant={a.status === 'WORK' ? 'default' : a.status === 'FOLGA' ? 'secondary' : 'outline'}>
                      {formatStatus(a.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatShift(a.shift_code)}</TableCell>
                  <TableCell>{formatMinutes(a.minutes)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {assignments.length > 50 && (
            <p className="text-sm text-muted-foreground mt-2">
              Mostrando os 50 primeiros de {assignments.length} registros
            </p>
          )}
        </CardContent>
      </Card>

      {violations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Alertas</CardTitle>
            <p className="text-sm text-muted-foreground">
              {pluralize(violations.length, 'alerta')} para revisar
            </p>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Colaborador</TableHead>
                  <TableHead>Regra</TableHead>
                  <TableHead>Gravidade</TableHead>
                  <TableHead>Detalhe</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {violations.map((v, i) => (
                  <TableRow key={i}>
                    <TableCell>{v.employee_id}</TableCell>
                    <TableCell>{formatRule(v.rule_code)}</TableCell>
                    <TableCell>
                      <Badge variant={v.severity === 'CRITICAL' ? 'destructive' : 'secondary'}>
                        {formatSeverity(v.severity)}
                      </Badge>
                    </TableCell>
                    <TableCell>{v.detail}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
