import { Button } from '@/components/ui/button'

type FormActionsProps = {
  isSubmitting: boolean
  submitLabel: string
  cancelLabel?: string
  onCancel?: () => void
}

export function FormActions({ isSubmitting, submitLabel, cancelLabel, onCancel }: FormActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Salvando...' : submitLabel}
      </Button>
      {onCancel && cancelLabel && (
        <Button type="button" variant="outline" onClick={onCancel}>
          {cancelLabel}
        </Button>
      )}
    </div>
  )
}
