import type { ReactNode } from 'react'
import { TabsContent } from '@/components/ui/tabs'

type TemplateSectionProps = { children: ReactNode }

export function TemplateSection({ children }: TemplateSectionProps) {
  return <TabsContent value="mosaico">{children}</TabsContent>
}
