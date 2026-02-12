import type { ReactNode } from 'react'
import { TabsContent } from '@/components/ui/tabs'

type ExceptionSectionProps = { children: ReactNode }

export function ExceptionSection({ children }: ExceptionSectionProps) {
  return <TabsContent value="excecoes">{children}</TabsContent>
}
