import type { ReactNode } from 'react'

type FormSectionProps = {
  children: ReactNode
}

export function FormSection({ children }: FormSectionProps) {
  return <div className="space-y-2">{children}</div>
}
