import type { ReactNode } from 'react'
import { TabsContent } from '@/components/ui/tabs'

type DemandSectionProps = { children: ReactNode }

export function DemandSection({ children }: DemandSectionProps) {
  return <TabsContent value="demand">{children}</TabsContent>
}
