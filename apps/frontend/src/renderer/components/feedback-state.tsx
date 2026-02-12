import { cn } from '@/lib/utils'

type FeedbackStateProps = {
  message: string
  className?: string
}

export function EmptyState({ message, className }: FeedbackStateProps) {
  return <p className={cn('text-sm text-muted-foreground', className)}>{message}</p>
}

export function ErrorState({ message, className }: FeedbackStateProps) {
  return <p className={cn('text-sm text-destructive', className)}>{message}</p>
}

export function LoadingState({ message = 'Carregando...', className }: Partial<FeedbackStateProps>) {
  return <p className={cn('text-sm text-muted-foreground', className)}>{message}</p>
}
