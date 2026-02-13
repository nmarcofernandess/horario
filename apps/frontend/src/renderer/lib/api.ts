const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(message: string, status: number, detail: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string'
          ? detail.message
          : res.statusText)
    throw new ApiError(message, res.status, detail)
  }
  return res.json()
}

function buildQuery(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v != null && v !== '')
  if (entries.length === 0) return ''
  return '?' + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v!)}`).join('&')
}

export const api = {
  health: () => fetch(`${API_BASE}/health`).then((r) => r.ok),

  config: {
    getRuntimeMode: () =>
      fetchApi<{
        mode: 'NORMAL' | 'ESTRITO'
        updated_at?: string
        updated_by_role?: string
        source: string
      }>('/config/runtime-mode'),
    updateRuntimeMode: (data: { mode: 'NORMAL' | 'ESTRITO'; actor_role: 'ADMIN' | 'OPERADOR' }) =>
      fetchApi<{
        mode: 'NORMAL' | 'ESTRITO'
        updated_at?: string
        updated_by_role?: string
        source: string
      }>('/config/runtime-mode', { method: 'PATCH', body: JSON.stringify(data) }),
    listGovernanceAudit: (limit = 50) =>
      fetchApi<
        Array<{
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
        }>
      >(`/config/governance/audit${buildQuery({ limit: String(limit) })}`),
    getGovernance: () =>
      fetchApi<{
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
      }>('/config/governance'),
    updateGovernance: (data: {
      marker_semantics: Record<string, string>
      collective_agreement_id: string
      sunday_holiday_legal_validated: boolean
      legal_validation_note?: string
    }) =>
      fetchApi<{
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
      }>('/config/governance', { method: 'PATCH', body: JSON.stringify(data) }),
    applyGovernanceDefaults: () =>
      fetchApi<{
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
      }>('/config/governance/apply-defaults', { method: 'POST' }),
  },

  shifts: {
    list: (sector_id = 'CAIXA') =>
      fetchApi<Array<{ shift_code: string; sector_id: string; minutes: number; day_scope: string }>>(
        `/shifts${buildQuery({ sector_id })}`
      ),
    create: (data: { shift_code: string; sector_id?: string; minutes: number; day_scope: string }) =>
      fetchApi<{ shift_code: string; sector_id: string; minutes: number; day_scope: string }>(
        '/shifts',
        { method: 'POST', body: JSON.stringify({ sector_id: 'CAIXA', ...data }) }
      ),
    update: (shift_code: string, data: { minutes: number; day_scope: string; sector_id?: string }) =>
      fetchApi<{ shift_code: string; sector_id: string; minutes: number; day_scope: string }>(
        `/shifts/${encodeURIComponent(shift_code)}${buildQuery({ sector_id: data.sector_id || 'CAIXA' })}`,
        { method: 'PATCH', body: JSON.stringify({ minutes: data.minutes, day_scope: data.day_scope }) }
      ),
    remove: (shift_code: string, sector_id = 'CAIXA') =>
      fetchApi<{ ok: boolean; shift_code: string }>(
        `/shifts/${encodeURIComponent(shift_code)}${buildQuery({ sector_id })}`,
        { method: 'DELETE' }
      ),
  },

  exceptions: {
    list: (opts?: { sector_id?: string; period_start?: string; period_end?: string }) =>
      fetchApi<Array<{ sector_id: string; employee_id: string; exception_date: string; exception_type: string; note: string | null }>>(
        `/exceptions${buildQuery(opts || {})}`
      ),
    create: (data: { sector_id?: string; employee_id: string; exception_date: string; exception_type: string; note?: string }) =>
      fetchApi<{ sector_id: string; employee_id: string; exception_date: string; exception_type: string; note: string | null }>(
        '/exceptions',
        { method: 'POST', body: JSON.stringify({ sector_id: 'CAIXA', ...data }) }
      ),
    update: (data: {
      sector_id?: string
      original_employee_id: string
      original_exception_date: string
      original_exception_type: string
      employee_id: string
      exception_date: string
      exception_type: string
      note?: string
    }) =>
      fetchApi<{ sector_id: string; employee_id: string; exception_date: string; exception_type: string; note: string | null }>(
        '/exceptions',
        { method: 'PATCH', body: JSON.stringify({ sector_id: 'CAIXA', ...data }) }
      ),
    remove: (data: { employee_id: string; exception_date: string; exception_type: string; sector_id?: string }) =>
      fetchApi<{ ok: boolean }>(
        `/exceptions${buildQuery({
          sector_id: data.sector_id || 'CAIXA',
          employee_id: data.employee_id,
          exception_date: data.exception_date,
          exception_type: data.exception_type,
        })}`,
        { method: 'DELETE' }
      ),
  },

  demandProfile: {
    list: (opts?: { sector_id?: string; period_start?: string; period_end?: string }) =>
      fetchApi<Array<{ sector_id: string; work_date: string; slot_start: string; min_required: number }>>(
        `/demand-profile${buildQuery(opts || {})}`
      ),
    create: (data: { sector_id?: string; work_date: string; slot_start: string; min_required: number }) =>
      fetchApi<{ sector_id: string; work_date: string; slot_start: string; min_required: number }>(
        '/demand-profile',
        { method: 'POST', body: JSON.stringify({ sector_id: 'CAIXA', ...data }) }
      ),
    update: (data: {
      sector_id?: string
      original_work_date: string
      original_slot_start: string
      work_date: string
      slot_start: string
      min_required: number
    }) =>
      fetchApi<{ sector_id: string; work_date: string; slot_start: string; min_required: number }>(
        '/demand-profile',
        { method: 'PATCH', body: JSON.stringify({ sector_id: 'CAIXA', ...data }) }
      ),
    remove: (data: { work_date: string; slot_start: string; sector_id?: string }) =>
      fetchApi<{ ok: boolean }>(
        `/demand-profile${buildQuery({
          sector_id: data.sector_id || 'CAIXA',
          work_date: data.work_date,
          slot_start: data.slot_start,
        })}`,
        { method: 'DELETE' }
      ),
  },

  weekDayTemplate: {
    list: (sector_id = 'CAIXA') =>
      fetchApi<Array<{ employee_id: string; day_key: string; shift_code: string; minutes: number }>>(
        `/weekday-template${buildQuery({ sector_id })}`
      ),
    save: (data: Array<{ employee_id: string; day_key: string; shift_code: string; minutes?: number }>, sector_id = 'CAIXA') =>
      fetchApi<{ ok: boolean; count: number }>(
        `/weekday-template${buildQuery({ sector_id })}`,
        { method: 'POST', body: JSON.stringify(data) }
      ),
  },

  sundayRotation: {
    list: (sector_id = 'CAIXA') =>
      fetchApi<Array<{ scale_index: number; employee_id: string; sunday_date: string; folga_date: string | null }>>(
        `/sunday-rotation${buildQuery({ sector_id })}`
      ),
    save: (
      data: Array<{ scale_index: number; employee_id: string; sunday_date: string; folga_date?: string | null }>,
      sector_id = 'CAIXA'
    ) =>
      fetchApi<{ ok: boolean; count: number }>(
        `/sunday-rotation${buildQuery({ sector_id })}`,
        { method: 'POST', body: JSON.stringify(data) }
      ),
  },

  employees: {
    list: () => fetchApi<Array<{ employee_id: string; name: string; contract_code: string; sector_id: string; rank: number; active: boolean }>>('/employees'),
    create: (data: { employee_id: string; name: string; contract_code: string; sector_id: string; rank?: number }) =>
      fetchApi('/employees', { method: 'POST', body: JSON.stringify(data) }),
    updateRank: (id: string, rank: number) => fetchApi(`/employees/${encodeURIComponent(id)}/rank`, { method: 'PATCH', body: JSON.stringify({ rank }) }),
  },

  sectors: {
    list: () => fetchApi<Array<{ sector_id: string; name: string }>>('/sectors'),
    create: (data: { sector_id: string; name: string }) => fetchApi('/sectors', { method: 'POST', body: JSON.stringify(data) }),
  },

  preferences: {
    list: () => fetchApi<Array<{ request_id: string; employee_id: string; request_date: string; request_type: string; decision: string }>>('/preferences'),
    create: (data: { request_id: string; employee_id: string; request_date: string; request_type: string; priority?: string; note?: string }) =>
      fetchApi('/preferences', { method: 'POST', body: JSON.stringify(data) }),
    updateDecision: (id: string, data: { decision: string; reason?: string }) =>
      fetchApi(`/preferences/${id}/decision`, { method: 'PATCH', body: JSON.stringify(data) }),
  },

  scale: {
    preflight: (data: {
      period_start: string
      period_end: string
      sector_id?: string
    }) =>
      fetchApi<{
        mode: 'NORMAL' | 'ESTRITO'
        blockers: Array<{ code: string; message: string; recommended_action: string }>
        critical_warnings: Array<{ code: string; message: string; recommended_action: string }>
        can_proceed: boolean
        ack_required: boolean
      }>('/scale/preflight', { method: 'POST', body: JSON.stringify(data) }),
    generate: (data: {
      period_start: string
      period_end: string
      sector_id?: string
      risk_ack?: { actor_role: string; actor_name?: string; reason: string }
    }) =>
      fetchApi<{ status: string; assignments_count: number; violations_count: number }>('/scale/generate', { method: 'POST', body: JSON.stringify(data) }),
    simulate: (data: {
      period_start: string
      period_end: string
      sector_id?: string
      risk_ack?: { actor_role: string; actor_name?: string; reason: string }
    }) =>
      fetchApi<{
        status: string
        assignments_count: number
        violations_count: number
        preferences_processed: number
        exceptions_applied: number
        assignments: Array<{ work_date: string; employee_id: string; employee_name?: string; status: string; shift_code?: string; minutes: number }>
        violations: Array<{ employee_id: string; employee_name?: string; rule_code: string; rule_label?: string; severity: string; detail: string }>
      }>('/scale/simulate', { method: 'POST', body: JSON.stringify(data) }),
    weeklyAnalysis: (data: { period_start: string; period_end: string; sector_id?: string; mode?: 'OFFICIAL' | 'SIMULATION' }) =>
      fetchApi<{
        period_start: string
        period_end: string
        sector_id: string
        policy_week_definition: 'MON_SUN' | 'SUN_SAT'
        tolerance_minutes: number
        summaries_mon_sun: Array<{
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
        }>
        summaries_sun_sat: Array<{
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
        }>
        external_dependencies_open: string[]
      }>('/scale/weekly-analysis', { method: 'POST', body: JSON.stringify({ mode: 'OFFICIAL', ...data }) }),
    getAssignments: () => fetchApi<Array<{ work_date: string; employee_id: string; employee_name?: string; status: string; shift_code?: string; minutes: number }>>('/scale/assignments'),
    getViolations: () => fetchApi<Array<{ employee_id: string; employee_name?: string; rule_code: string; rule_label?: string; severity: string; detail: string }>>('/scale/violations'),
  },

  export: {
    html: () => `${API_BASE}/scale/export/html/download`,
    markdown: () => `${API_BASE}/scale/export/markdown/download`,
  },
}
