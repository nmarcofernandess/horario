import type { ReactNode } from 'react'
import { TabsContent } from '@/components/ui/tabs'

type RotationSectionProps = { children: ReactNode }

export function RotationSection({ children }: RotationSectionProps) {
  return <TabsContent value="rodizio">{children}</TabsContent>
}
