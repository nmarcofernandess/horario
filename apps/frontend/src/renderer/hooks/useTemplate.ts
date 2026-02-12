import { useCallback, useState } from 'react'
import { api } from '@/lib/api'
import type { Shift } from '@/hooks/useShifts'

export type TemplateSlot = { employee_id: string; day_key: string; shift_code: string; minutes: number }

export function useTemplate() {
  const [templateSlots, setTemplateSlots] = useState<TemplateSlot[]>([])

  const loadTemplate = useCallback(async () => {
    const data = await api.weekDayTemplate.list()
    setTemplateSlots(data)
  }, [])

  const getTemplateCell = useCallback(
    (employeeId: string, day: string) =>
      templateSlots.find((s) => s.employee_id === employeeId && s.day_key === day)?.shift_code || '',
    [templateSlots],
  )

  const handleTemplateCellChange = useCallback((empId: string, day: string, shiftCode: string, shifts: Shift[]) => {
    const shift = shifts.find((s) => s.shift_code === shiftCode)
    const minutes = shift?.minutes ?? 0
    setTemplateSlots((prev) => {
      const rest = prev.filter((s) => !(s.employee_id === empId && s.day_key === day))
      if (!shiftCode) return rest
      return [...rest, { employee_id: empId, day_key: day, shift_code: shiftCode, minutes }]
    })
  }, [])

  const clearTemplateForEmployee = useCallback((employeeId: string) => {
    setTemplateSlots((prev) => prev.filter((s) => s.employee_id !== employeeId))
  }, [])

  const clearTemplateAllLocal = useCallback(() => {
    setTemplateSlots([])
  }, [])

  return {
    templateSlots,
    setTemplateSlots,
    loadTemplate,
    getTemplateCell,
    handleTemplateCellChange,
    clearTemplateForEmployee,
    clearTemplateAllLocal,
  }
}
