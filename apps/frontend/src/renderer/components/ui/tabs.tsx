"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// Contexto para tabs controlados (evita Radix/Electron "Maximum update depth")
const TabsContext = React.createContext<{
  value: string
  onValueChange: (v: string) => void
} | null>(null)

function Tabs({
  className,
  defaultValue,
  value: controlledValue,
  onValueChange,
  children,
  ...props
}: {
  className?: string
  defaultValue?: string
  value?: string
  onValueChange?: (v: string) => void
  children?: React.ReactNode
}) {
  const [uncontrolled, setUncontrolled] = React.useState(defaultValue ?? "")
  const isControlled = controlledValue !== undefined
  const value = isControlled ? controlledValue : uncontrolled
  const setValue = React.useCallback((v: string) => {
    if (!isControlled) setUncontrolled(v)
    onValueChange?.(v)
  }, [isControlled, onValueChange])

  return (
    <TabsContext.Provider value={{ value, onValueChange: setValue }}>
      <div
        data-slot="tabs"
        className={cn("group/tabs flex flex-col gap-2", className)}
        {...props}
      >
        {children}
      </div>
    </TabsContext.Provider>
  )
}

const tabsListVariants = cva(
  "rounded-lg p-[3px] h-9 text-muted-foreground inline-flex w-fit items-center justify-center",
  {
    variants: {
      variant: {
        default: "bg-muted",
        line: "gap-1 bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function TabsList({
  className,
  variant = "default",
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof tabsListVariants>) {
  return (
    <div
      data-slot="tabs-list"
      data-variant={variant}
      role="tablist"
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    >
      {children}
    </div>
  )
}

function TabsTrigger({
  className,
  value,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { value: string }) {
  const ctx = React.useContext(TabsContext)
  const isActive = ctx?.value === value
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      data-state={isActive ? "active" : "inactive"}
      data-slot="tabs-trigger"
      className={cn(
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring text-foreground/60 hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground relative inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-all focus-visible:ring-[3px] focus-visible:outline-1 disabled:pointer-events-none disabled:opacity-50",
        "data-[state=active]:bg-background dark:data-[state=active]:text-foreground dark:data-[state=active]:border-input dark:data-[state=active]:bg-input/30 data-[state=active]:text-foreground data-[state=active]:shadow-sm",
        "after:bg-foreground after:absolute after:opacity-0 after:transition-opacity after:inset-x-0 after:bottom-[-5px] after:h-0.5 data-[state=active]:after:opacity-100 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      onClick={() => ctx?.onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  )
}

function TabsContent({
  className,
  value,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { value: string }) {
  const ctx = React.useContext(TabsContext)
  if (ctx?.value !== value) return null
  return (
    <div
      data-slot="tabs-content"
      role="tabpanel"
      className={cn("flex-1 outline-none", className)}
      {...props}
    >
      {children}
    </div>
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent, tabsListVariants }
