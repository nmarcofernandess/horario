import * as React from "react"
import { CalendarDays } from "lucide-react"

import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"

type DateInputProps = React.ComponentProps<"input">

const DateInput = React.forwardRef<HTMLInputElement, DateInputProps>(
  ({ className, ...props }, forwardedRef) => {
    const innerRef = React.useRef<HTMLInputElement>(null)

    React.useImperativeHandle(forwardedRef, () => innerRef.current as HTMLInputElement)

    const openPicker = () => {
      const input = innerRef.current
      if (!input) return
      if (typeof input.showPicker === "function") {
        input.showPicker()
        return
      }
      input.focus()
    }

    return (
      <div className="relative">
        <Input
          {...props}
          ref={innerRef}
          type="date"
          className={cn(
            "pr-10 [color-scheme:light_dark] [&::-webkit-calendar-picker-indicator]:opacity-0",
            className
          )}
        />
        <button
          type="button"
          onClick={openPicker}
          aria-label="Selecionar data"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
        >
          <CalendarDays className="size-4" />
        </button>
      </div>
    )
  }
)

DateInput.displayName = "DateInput"

export { DateInput }
