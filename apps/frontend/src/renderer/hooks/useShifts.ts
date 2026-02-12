import { useCallback, useState } from 'react'
import { api } from '@/lib/api'

export type Shift = { shift_code: string; sector_id: string; minutes: number; day_scope: string }

type NewShiftForm = { shift_code: string; minutes: string; day_scope: string }

export function useShifts() {
  const [shifts, setShifts] = useState<Shift[]>([])
  const [newShift, setNewShift] = useState<NewShiftForm>({ shift_code: '', minutes: '480', day_scope: 'WEEKDAY' })
  const [editingShiftCode, setEditingShiftCode] = useState<string | null>(null)

  const loadShifts = useCallback(async () => {
    const data = await api.shifts.list()
    setShifts(data)
  }, [])

  const resetShiftForm = useCallback(() => {
    setNewShift({ shift_code: '', minutes: '480', day_scope: 'WEEKDAY' })
    setEditingShiftCode(null)
  }, [])

  const startEditShift = useCallback((shift: Shift) => {
    setEditingShiftCode(shift.shift_code)
    setNewShift({
      shift_code: shift.shift_code,
      minutes: String(shift.minutes),
      day_scope: shift.day_scope,
    })
  }, [])

  return {
    shifts,
    setShifts,
    newShift,
    setNewShift,
    editingShiftCode,
    setEditingShiftCode,
    loadShifts,
    resetShiftForm,
    startEditShift,
  }
}
