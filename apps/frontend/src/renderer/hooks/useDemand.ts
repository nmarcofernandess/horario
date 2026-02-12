import { useCallback, useState } from 'react'
import { api } from '@/lib/api'

export type DemandSlot = { sector_id: string; work_date: string; slot_start: string; min_required: number }
export type NewDemandForm = { work_date: string; slot_start: string; min_required: string }

export function useDemand() {
  const [demandSlots, setDemandSlots] = useState<DemandSlot[]>([])
  const [newDemand, setNewDemand] = useState<NewDemandForm>({ work_date: '', slot_start: '08:00', min_required: '1' })
  const [editingDemandKey, setEditingDemandKey] = useState<string | null>(null)

  const loadDemand = useCallback(async () => {
    const data = await api.demandProfile.list()
    setDemandSlots(data)
  }, [])

  const startEditDemand = useCallback((d: DemandSlot) => {
    setEditingDemandKey(`${d.work_date}|${d.slot_start}`)
    setNewDemand({
      work_date: d.work_date,
      slot_start: d.slot_start,
      min_required: String(d.min_required),
    })
  }, [])

  return {
    demandSlots,
    setDemandSlots,
    newDemand,
    setNewDemand,
    editingDemandKey,
    setEditingDemandKey,
    loadDemand,
    startEditDemand,
  }
}
