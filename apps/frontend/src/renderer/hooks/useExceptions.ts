import { useCallback, useState } from 'react'
import { api } from '@/lib/api'

export type Exception = { sector_id: string; employee_id: string; exception_date: string; exception_type: string; note: string | null }
export type NewExceptionForm = { employee_id: string; exception_date: string; exception_type: string; note: string }

export function useExceptions() {
  const [exceptions, setExceptions] = useState<Exception[]>([])
  const [newExc, setNewExc] = useState<NewExceptionForm>({
    employee_id: '',
    exception_date: '',
    exception_type: 'VACATION',
    note: '',
  })
  const [editingExceptionKey, setEditingExceptionKey] = useState<string | null>(null)

  const loadExceptions = useCallback(async () => {
    const data = await api.exceptions.list()
    setExceptions(data)
  }, [])

  const startEditException = useCallback((ex: Exception) => {
    setEditingExceptionKey(`${ex.employee_id}|${ex.exception_date}|${ex.exception_type}`)
    setNewExc({
      employee_id: ex.employee_id,
      exception_date: ex.exception_date,
      exception_type: ex.exception_type,
      note: ex.note || '',
    })
  }, [])

  return {
    exceptions,
    setExceptions,
    newExc,
    setNewExc,
    editingExceptionKey,
    setEditingExceptionKey,
    loadExceptions,
    startEditException,
  }
}
