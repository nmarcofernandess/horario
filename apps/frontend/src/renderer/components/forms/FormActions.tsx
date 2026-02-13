import { Button } from '@/components/ui/button'

type FormActionsProps = {
  isSubmitting: boolean
  submitLabel: string
  cancelLabel?: string
  onCancel?: () => void
  /** ID do form para submit quando o botão fica fora do form (ex.: CardFooter) */
  formId?: string
}

export function FormActions({ isSubmitting, submitLabel, cancelLabel, onCancel, formId }: FormActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <Button type="submit" form={formId} disabled={isSubmitting}>
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
