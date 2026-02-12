"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react"
import type React from "react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { HelpCircle } from "lucide-react"

export interface TourStep {
  content: React.ReactNode
  selectorId: string
  width?: number
  height?: number
  onClickWithinArea?: () => void
  position?: "top" | "bottom" | "left" | "right"
}

interface TourContextType {
  currentStep: number
  totalSteps: number
  nextStep: () => void
  previousStep: () => void
  endTour: () => void
  isActive: boolean
  startTour: () => void
  setSteps: (steps: TourStep[]) => void
  steps: TourStep[]
  isTourCompleted: boolean
  setIsTourCompleted: (completed: boolean) => void
}

interface TourProviderProps {
  children: React.ReactNode
  onComplete?: () => void
  className?: string
  isTourCompleted?: boolean
}

const TourContext = createContext<TourContextType | null>(null)

const PADDING = 16
const CONTENT_WIDTH = 300
const CONTENT_HEIGHT = 200

function getElementPosition(id: string) {
  const element = document.getElementById(id)
  if (!element) return null
  const rect = element.getBoundingClientRect()
  return {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  }
}

function calculateContentPosition(
  elementPos: { top: number; left: number; width: number; height: number },
  position: "top" | "bottom" | "left" | "right" = "bottom"
) {
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let left = elementPos.left
  let top = elementPos.top

  switch (position) {
    case "top":
      top = elementPos.top - CONTENT_HEIGHT - PADDING
      left = elementPos.left + elementPos.width / 2 - CONTENT_WIDTH / 2
      break
    case "bottom":
      top = elementPos.top + elementPos.height + PADDING
      left = elementPos.left + elementPos.width / 2 - CONTENT_WIDTH / 2
      break
    case "left":
      left = elementPos.left - CONTENT_WIDTH - PADDING
      top = elementPos.top + elementPos.height / 2 - CONTENT_HEIGHT / 2
      break
    case "right":
      left = elementPos.left + elementPos.width + PADDING
      top = elementPos.top + elementPos.height / 2 - CONTENT_HEIGHT / 2
      break
  }

  return {
    top: Math.max(
      PADDING,
      Math.min(top, viewportHeight - CONTENT_HEIGHT - PADDING)
    ),
    left: Math.max(
      PADDING,
      Math.min(left, viewportWidth - CONTENT_WIDTH - PADDING)
    ),
    width: CONTENT_WIDTH,
    height: CONTENT_HEIGHT,
  }
}


export function TourProvider({
  children,
  onComplete,
  className,
  isTourCompleted = false,
}: TourProviderProps) {
  const [steps, setStepsState] = useState<TourStep[]>([])
  const [currentStep, setCurrentStep] = useState(-1)
  const [elementPosition, setElementPosition] = useState<{
    top: number
    left: number
    width: number
    height: number
  } | null>(null)
  const [isCompleted, setIsCompleted] = useState(isTourCompleted)

  const updateElementPosition = useCallback(() => {
    if (currentStep >= 0 && currentStep < steps.length) {
      const position = getElementPosition(
        steps[currentStep]?.selectorId ?? ""
      )
      if (position) {
        setElementPosition(position)
      }
    }
  }, [currentStep, steps])

  useEffect(() => {
    updateElementPosition()
    window.addEventListener("resize", updateElementPosition)
    window.addEventListener("scroll", updateElementPosition)

    return () => {
      window.removeEventListener("resize", updateElementPosition)
      window.removeEventListener("scroll", updateElementPosition)
    }
  }, [updateElementPosition])

  const nextStep = useCallback(async () => {
    setCurrentStep((prev) => {
      if (prev >= steps.length - 1) {
        setIsCompleted(true)
        onComplete?.()
        return -1
      }
      return prev + 1
    })
  }, [steps.length, onComplete])

  const previousStep = useCallback(() => {
    setCurrentStep((prev) => (prev > 0 ? prev - 1 : prev))
  }, [])

  const endTour = useCallback(() => {
    setCurrentStep(-1)
  }, [])

  const startTour = useCallback(() => {
    setCurrentStep(0)
  }, [])

  const handleClick = useCallback(
    (e: MouseEvent) => {
      if (
        currentStep >= 0 &&
        elementPosition &&
        steps[currentStep]?.onClickWithinArea
      ) {
        const isWithinBounds =
          e.clientX >= elementPosition.left &&
          e.clientX <=
            elementPosition.left +
              (steps[currentStep]?.width ?? elementPosition.width) &&
          e.clientY >= elementPosition.top &&
          e.clientY <=
            elementPosition.top +
              (steps[currentStep]?.height ?? elementPosition.height)

        if (isWithinBounds) {
          steps[currentStep].onClickWithinArea?.()
        }
      }
    },
    [currentStep, elementPosition, steps]
  )

  useEffect(() => {
    window.addEventListener("click", handleClick)
    return () => {
      window.removeEventListener("click", handleClick)
    }
  }, [handleClick])

  const setIsTourCompleted = useCallback((completed: boolean) => {
    setIsCompleted(completed)
  }, [])

  const setSteps = useCallback((newSteps: TourStep[]) => {
    setStepsState(newSteps)
  }, [])

  const step = steps[currentStep]
  const contentPos =
    step && elementPosition
      ? calculateContentPosition(elementPosition, step.position ?? "bottom")
      : null

  return (
    <TourContext.Provider
      value={{
        currentStep,
        totalSteps: steps.length,
        nextStep,
        previousStep,
        endTour,
        isActive: currentStep >= 0,
        startTour,
        setSteps,
        steps,
        isTourCompleted: isCompleted,
        setIsTourCompleted,
      }}
    >
      {children}
      {currentStep >= 0 && elementPosition && step && contentPos && (
        <>
          <div
            className={cn(
              "fixed z-[100] rounded-lg border-2 border-primary bg-primary/20",
              className
            )}
            style={{
              top: elementPosition.top,
              left: elementPosition.left,
              width: step.width ?? elementPosition.width,
              height: step.height ?? elementPosition.height,
            }}
          />
          <div
            className="fixed z-[101] rounded-lg border bg-background p-4 shadow-lg"
            style={{
              top: contentPos.top,
              left: contentPos.left,
              width: contentPos.width,
              height: contentPos.height,
            }}
          >
            <div className="mb-2 text-xs text-muted-foreground">
              {currentStep + 1} / {steps.length}
            </div>
            <div className="mb-4 flex-1 overflow-auto text-sm">
              {step.content}
            </div>
            <div className="flex justify-between gap-2 items-center">
              <Button variant="ghost" size="sm" onClick={endTour}>
                Cancelar
              </Button>
              <div className="flex gap-2 ml-auto">
                {currentStep > 0 && (
                  <Button variant="outline" size="sm" onClick={previousStep}>
                    Anterior
                  </Button>
                )}
                <Button size="sm" onClick={nextStep}>
                  {currentStep === steps.length - 1 ? "Concluir" : "Próximo"}
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
    </TourContext.Provider>
  )
}

export function useTour() {
  const context = useContext(TourContext)
  if (!context) {
    throw new Error("useTour must be used within a TourProvider")
  }
  return context
}

export function TourAlertDialog({
  isOpen,
  setIsOpen,
}: {
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
}) {
  const { startTour, steps, isTourCompleted, currentStep, setIsTourCompleted } =
    useTour()

  if (isTourCompleted || steps.length === 0 || currentStep > -1) {
    return null
  }

  const handleStart = () => {
    startTour()
  }

  const handleSkip = () => {
    setIsTourCompleted(true)
    localStorage.setItem("tourCompleted", "true")
    setIsOpen(false)
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-full bg-primary/10">
            <HelpCircle className="size-6 text-primary" />
          </div>
          <AlertDialogTitle>Bem-vindo ao EscalaFlow</AlertDialogTitle>
          <AlertDialogDescription>
            Faça um tour rápido para conhecer as principais funcionalidades do
            sistema.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleSkip}>Pular</AlertDialogCancel>
          <AlertDialogAction onClick={handleStart}>Iniciar tour</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
