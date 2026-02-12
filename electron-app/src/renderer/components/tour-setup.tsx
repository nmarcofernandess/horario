"use client"

import { useEffect, useState } from "react"
import { TourAlertDialog, useTour } from "@/components/tour"
import { TOUR_STEP_IDS } from "@/lib/tour-constants"

const tourSteps = [
  {
    content: (
      <div>
        <h3 className="font-semibold">Equipe</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Aqui você alterna entre equipes. O plano atual é EscalaFlow.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.TEAM_SWITCHER,
    position: "right" as const,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Menu principal</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Escala, Colaboradores, Pedidos e Configuração. Clique em qualquer item
          para navegar.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_MAIN,
    position: "right" as const,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Área de conteúdo</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Aqui aparece o conteúdo da página. Na Escala você define período e
          gera a escala; em Colaboradores cadastra pessoas; em Pedidos gerencia
          pedidos de folga; em Configuração ajusta turnos e regras.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.CONTENT_AREA,
    position: "bottom" as const,
  },
]

export function TourSetup() {
  const { setSteps } = useTour()
  const [showWelcome, setShowWelcome] = useState(false)

  useEffect(() => {
    setSteps(tourSteps)
  }, [setSteps])

  useEffect(() => {
    const completed = localStorage.getItem("tourCompleted")
    if (!completed) {
      setShowWelcome(true)
    }
  }, [])

  return <TourAlertDialog isOpen={showWelcome} setIsOpen={setShowWelcome} />
}
