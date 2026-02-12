import type { ReactNode } from 'react'
import { TabsContent } from '@/components/ui/tabs'

type ShiftSectionProps = { children: ReactNode }

export function ShiftSection({ children }: ShiftSectionProps) {
  return <TabsContent value="turnos">{children}</TabsContent>
}
