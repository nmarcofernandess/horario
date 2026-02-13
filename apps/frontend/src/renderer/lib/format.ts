/**
 * Formatação para pt-BR e usuários leigos.
 * Traduz códigos técnicos em labels amigáveis.
 */

const SHIFT_LABELS: Record<string, string> = {
  CAI1: 'Manhã (9h30)',
  CAI2: 'Manhã (6h)',
  CAI3: 'Tarde (8h30)',
  CAI4: 'Manhã (5h)',
  CAI5: 'Tarde (5h30)',
  CAI6: 'Manhã (5h30)',
  'DOM_08_12_30': 'Domingo (4h30)',
  H_DOM: 'Domingo',
}

const STATUS_LABELS: Record<string, string> = {
  WORK: 'Trabalho',
  FOLGA: 'Folga',
  ABSENCE: 'Ausência',
}

const RULE_LABELS: Record<string, string> = {
  R1_MAX_CONSECUTIVE: 'Dias consecutivos (máx. 6)',
  R2_MIN_INTERSHIFT_REST: 'Intervalo entre jornadas (mín. 11h)',
  R2_INTERSHIFT_REST: 'Intervalo entre jornadas',
  R3_SUNDAY_ROTATION: 'Rodízio de domingos',
  R3_WEEKLY_HOURS: 'Meta semanal de horas',
  R4_WEEKLY_TARGET: 'Meta semanal de horas',
  R4_DEMAND_COVERAGE: 'Cobertura insuficiente',
  R5_DEMAND_COVERAGE: 'Cobertura insuficiente',
  R6_MAX_DAILY_MINUTES: 'Limite diário de jornada',
}

const SEVERITY_LABELS: Record<string, string> = {
  CRITICAL: 'Crítico',
  HIGH: 'Alto',
  MEDIUM: 'Médio',
  LOW: 'Baixo',
}

const REQUEST_TYPE_LABELS: Record<string, string> = {
  FOLGA_ON_DATE: 'Folga na data',
  SHIFT_CHANGE_ON_DATE: 'Troca de turno',
  AVOID_SUNDAY_DATE: 'Evitar domingo',
}

const CONTRACT_LABELS: Record<string, string> = {
  H44_CAIXA: '44h semanais',
  H36_CAIXA: '36h semanais',
  H30_CAIXA: '30h semanais',
  CLT_44H: '44h semanais',
}

/** Data YYYY-MM-DD → DD/MM/YYYY */
export function formatDateBR(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-')
  if (!y || !m || !d) return dateStr
  return `${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`
}

/** Minutos → "8h" ou "8h 30min" */
export function formatMinutes(minutes: number): string {
  if (minutes === 0) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (m === 0) return `${h}h`
  return `${h}h ${m}min`
}

/** Status técnico → label amigável */
export function formatStatus(status: string | null | undefined): string {
  if (!status) return '—'
  return STATUS_LABELS[status] ?? status
}

/** Código de turno → label amigável */
export function formatShift(code: string | null | undefined): string {
  if (!code) return '—'
  return SHIFT_LABELS[code] ?? code
}

/** Regra de compliance → label amigável */
export function formatRule(code: string | null | undefined): string {
  if (!code) return '—'
  return RULE_LABELS[code] ?? code
}

/** Severidade → label amigável */
export function formatSeverity(sev: string | null | undefined): string {
  if (!sev) return '—'
  return SEVERITY_LABELS[sev] ?? sev
}

/** Tipo de pedido → label amigável */
export function formatRequestType(type: string | null | undefined): string {
  if (!type) return '—'
  return REQUEST_TYPE_LABELS[type] ?? type
}

/** Contrato → label amigável */
export function formatContract(code: string | null | undefined): string {
  if (!code) return '—'
  return CONTRACT_LABELS[code] ?? code
}

/** Pluralizar contagem: "1 alocação" vs "5 alocações" */
export function pluralize(count: number, singular: string, plural?: string): string {
  const p = plural ?? `${singular}s`
  return count === 1 ? `1 ${singular}` : `${count} ${p}`
}
