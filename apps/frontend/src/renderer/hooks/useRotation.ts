import { useCallback, useState } from 'react'
import { api } from '@/lib/api'

export type RotationRow = { scale_index: number; employee_id: string; sunday_date: string; folga_date: string | null }
export type NewRotationForm = { scale_index: number; employee_id: string; sunday_date: string; folga_date: string }

export function useRotation() {
  const [rotationRows, setRotationRows] = useState<RotationRow[]>([])
  const [newRotation, setNewRotation] = useState<NewRotationForm>({
    scale_index: 1,
    employee_id: '',
    sunday_date: '',
    folga_date: '',
  })
  const [editingRotationIndex, setEditingRotationIndex] = useState<number | null>(null)

  const loadRotation = useCallback(async () => {
    const data = await api.sundayRotation.list()
    setRotationRows(data)
  }, [])

  const startEditRotation = useCallback((row: RotationRow, index: number) => {
    setEditingRotationIndex(index)
    setNewRotation({
      scale_index: row.scale_index,
      employee_id: row.employee_id,
      sunday_date: row.sunday_date,
      folga_date: row.folga_date || '',
    })
  }, [])

  return {
    rotationRows,
    setRotationRows,
    newRotation,
    setNewRotation,
    editingRotationIndex,
    setEditingRotationIndex,
    loadRotation,
    startEditRotation,
  }
}
