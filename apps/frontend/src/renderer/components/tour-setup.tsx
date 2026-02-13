"use client"

import { useEffect, useState } from "react"
import { TourAlertDialog, useTour } from "@/components/tour"
import { TOUR_NAVIGATE_EVENT, TOUR_STEP_IDS } from "@/lib/tour-constants"
import type { Page } from "@/types"

function navigateTourTo(page: Page) {
  window.dispatchEvent(new CustomEvent(TOUR_NAVIGATE_EVENT, { detail: page }))
}

const tourSteps = [
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 1: Entenda onde você está</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Aqui fica o contexto da instalação atual. No momento, o foco operacional
          é o setor Caixa no EscalaFlow.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.TEAM_SWITCHER,
    position: "right" as const,
    cardWidth: 300,
    cardHeight: 180,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 2: Fluxo de entrada recomendado</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Use este menu para seguir o fluxo recomendado de entrada:
        </p>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Configuração</li>
          <li>Colaboradores</li>
          <li>Pedidos</li>
          <li>Escala</li>
        </ol>
        <p className="mt-2 text-sm text-muted-foreground">
          Esse caminho reduz erro e evita bloqueio no preflight.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_MAIN,
    position: "right" as const,
    cardWidth: 320,
    cardHeight: 230,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 3: Abra Configuração</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          O tour já levou você para <strong>Configuração</strong>. Esse é o primeiro
          passo prático para começar com segurança.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_CONFIGURACAO,
    position: "right" as const,
    onEnter: () => navigateTourTo("configuracao"),
    cardWidth: 300,
    cardHeight: 190,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 4: Configure a base operacional</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Em <strong>Configuração</strong>, revise nesta ordem:
        </p>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Turnos</li>
          <li>Mosaico (SEG-SAB)</li>
          <li>Rodízio de domingos</li>
          <li>Exceções (férias/atestados)</li>
          <li>Demanda por horário</li>
          <li>Governança (modo NORMAL/ESTRITO, CCT e semântica 5/6)</li>
        </ol>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.CONTENT_AREA,
    position: "bottom" as const,
    cardWidth: 380,
    cardHeight: 320,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 5: Cadastre colaboradores</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Agora o tour te leva para <strong>Colaboradores</strong>, onde você mantém
          equipe, contrato e setor.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_COLABORADORES,
    position: "right" as const,
    onEnter: () => navigateTourTo("colaboradores"),
    cardWidth: 320,
    cardHeight: 200,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 6: Trate os pedidos</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Em seguida, abra <strong>Pedidos</strong> e deixe as solicitações
          decididas (aprovadas/rejeitadas) antes da escala.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_PEDIDOS,
    position: "right" as const,
    onEnter: () => navigateTourTo("pedidos"),
    cardWidth: 320,
    cardHeight: 210,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 7: Feche na Escala</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Agora vá para <strong>Escala</strong>, selecione período e execute
          simulação ou geração oficial.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.NAV_ESCALA,
    position: "right" as const,
    onEnter: () => navigateTourTo("escala"),
    cardWidth: 320,
    cardHeight: 210,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 8: Gere com segurança</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Em <strong>Escala</strong>, selecione período e execute:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          <li><strong>Simular período</strong> para testar sem sobrescrever oficial.</li>
          <li><strong>Gerar escala</strong> para publicar resultado oficial.</li>
          <li>Se houver risco legal em modo estrito, informe justificativa no ACK.</li>
        </ul>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.CONTENT_AREA,
    position: "bottom" as const,
    cardWidth: 380,
    cardHeight: 300,
  },
  {
    content: (
      <div>
        <h3 className="font-semibold">Passo 9: Conferência final</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Depois da execução:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Revise calendário/tabela e violações.</li>
          <li>Confira aderência semanal (MON_SUN e SUN_SAT).</li>
          <li>Exporte HTML/Markdown para operação.</li>
        </ul>
        <p className="mt-2 text-sm text-muted-foreground">
          Pronto: esse é o fluxo oficial de entrada no sistema.
        </p>
      </div>
    ),
    selectorId: TOUR_STEP_IDS.CONTENT_AREA,
    position: "bottom" as const,
    cardWidth: 360,
    cardHeight: 280,
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
    // Tour desabilitado: dialog de boas-vindas bloqueava cliques (sidebar, tabs)
    if (!completed) {
      localStorage.setItem("tourCompleted", "true")
    }
  }, [])

  return <TourAlertDialog isOpen={showWelcome} setIsOpen={setShowWelcome} />
}
