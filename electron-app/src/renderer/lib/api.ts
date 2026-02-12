const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

export const api = {
  health: () => fetch(`${API_BASE}/health`).then((r) => r.ok),

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
    generate: (data: { period_start: string; period_end: string; sector_id?: string }) =>
      fetchApi<{ status: string; assignments_count: number; violations_count: number }>('/scale/generate', { method: 'POST', body: JSON.stringify(data) }),
    getAssignments: () => fetchApi<Array<{ work_date: string; employee_id: string; employee_name?: string; status: string; shift_code?: string; minutes: number }>>('/scale/assignments'),
    getViolations: () => fetchApi<Array<{ employee_id: string; rule_code: string; severity: string; detail: string }>>('/scale/violations'),
  },

  export: {
    html: () => `${API_BASE}/scale/export/html/download`,
    markdown: () => `${API_BASE}/scale/export/markdown/download`,
  },
}
