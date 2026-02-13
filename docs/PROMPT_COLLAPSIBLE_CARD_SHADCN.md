# Prompt para IA do shadcn — Collapsible Card "Aderência de contrato"

## Contexto

App Electron + React + Vite + shadcn/ui. Na página **Escala de Trabalho**, existe um card **"Aderência de contrato"** que deve ser **colapsável**. O header mostra o título, a contagem de alertas (violações) e um chevron. Ao clicar, o conteúdo expande/recolhe.

## Estado atual do código

### Arquivo: `apps/frontend/src/renderer/pages/EscalaPage.tsx` (trecho relevante)

```tsx
<Card className="overflow-hidden">
  <Collapsible defaultOpen className="group/collapsible">
    <CollapsibleTrigger asChild>
      <button className="flex w-full items-start justify-between gap-4 border-b px-6 py-4 text-left transition-colors hover:bg-muted/50">
        <div className="space-y-1.5">
          <CardTitle>Aderência de contrato</CardTitle>
          <CardDescription>
            {(() => {
              const count = isSimulationView ? lastSimulation?.violations_count : lastResult?.violations_count
              const n = count ?? 0
              return n > 0
                ? `${pluralize(n, 'alerta')} — Análise semanal da carga horária.`
                : 'Análise semanal da carga horária por janela de corte e status de governança.'
            })()}
          </CardDescription>
        </div>
        <ChevronDownIcon className="text-muted-foreground size-4 shrink-0 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180" />
      </button>
    </CollapsibleTrigger>
    <CollapsibleContent>
      <CardContent className="space-y-4 border-t-0 pt-6">
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant={weeklyWindow === 'MON_SUN' ? 'default' : 'outline'} onClick={() => setWeeklyWindow('MON_SUN')}>
            Segunda a Domingo
          </Button>
          <Button size="sm" variant={weeklyWindow === 'SUN_SAT' ? 'default' : 'outline'} onClick={() => setWeeklyWindow('SUN_SAT')}>
            Domingo a Sábado
          </Button>
        </div>
        {/* bloco external_dependencies_open — alerta governança */}
        {/* tabela weeklyAnalysis com colunas Semana, Colaborador, Contrato, Real, Meta, Delta, Status */}
      </CardContent>
    </CollapsibleContent>
  </Collapsible>
</Card>
```

### Componente Collapsible: `apps/frontend/src/renderer/components/ui/collapsible.tsx`

```tsx
"use client"

import * as React from "react"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

import { cn } from "@/lib/utils"

const Collapsible = CollapsiblePrimitive.Root
const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger

function CollapsibleContent({
  className,
  ...props
}: React.ComponentProps<typeof CollapsiblePrimitive.CollapsibleContent>) {
  return (
    <CollapsiblePrimitive.CollapsibleContent
      data-slot="collapsible-content"
      className={cn(
        "overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
        className
      )}
      {...props}
    />
  )
}

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
```

### Componente Card: `apps/frontend/src/renderer/components/ui/card.tsx`

- Card, CardHeader, CardTitle, CardDescription, CardContent disponíveis
- Card tem `flex flex-col gap-6 rounded-xl border py-6 shadow-sm`

## Variáveis/estado usados no card

- `weeklyWindow`: `'MON_SUN' | 'SUN_SAT'` — qual janela semanal exibir
- `weeklyAnalysis`: objeto com `summaries_mon_sun`, `summaries_sun_sat`, `external_dependencies_open`, etc.
- `isSimulationView`: boolean
- `lastSimulation?.violations_count`, `lastResult?.violations_count`: número de alertas
- `pluralize(n, 'alerta')`: helper que retorna "1 alerta" ou "103 alertas"
- `formatDateBR`, `formatMinutes`: helpers de formatação

---

## PROMPT para enviar à IA do shadcn

```
Preciso de um Collapsible Card seguindo o padrão oficial do shadcn (collapsible-card pattern).

Contexto:
- App React + shadcn/ui + Tailwind
- Já tenho Collapsible (@radix-ui/react-collapsible), Card, CardHeader, CardTitle, CardDescription, CardContent
- O CollapsibleContent já tem animação accordion-up/accordion-down

Objetivo:
- Card "Aderência de contrato" totalmente colapsável
- Header clicável com: título, descrição (que mostra contagem de alertas quando há violações) e ChevronDown que gira ao expandir/recolher
- Conteúdo: botões de filtro (Segunda a Domingo / Domingo a Sábado), eventual bloco de governança, tabela de aderência

Requisitos:
1. Usar o padrão oficial shadcn de collapsible card (ver https://ui.shadcn.com/docs/components/radix/collapsible e https://www.shadcn.io/patterns/collapsible-card-1)
2. CollapsibleTrigger deve envolver o header (CardHeader ou equivalente)
3. ChevronDown com rotação correta no expand/collapse (group-data-[state=open] ou equivalente)
4. Separador visual (border) entre trigger e content
5. defaultOpen para iniciar expandido
6. Animação suave no CollapsibleContent
7. Preservar a estrutura: Card > Collapsible > (Trigger + Content), com o conteúdo dentro de CardContent

Me envie o código completo do bloco do card (do <Card> ao </Card>), pronto para colar no arquivo, mantendo as variáveis:
- weeklyWindow, setWeeklyWindow
- weeklyAnalysis
- isSimulationView, lastSimulation, lastResult
- pluralize(n, 'alerta')
- E a tabela com formatDateBR, formatMinutes, Badge "Dentro"/"Fora"
```

---

## Arquivo completo da seção (para referência)

O bloco completo está em `apps/frontend/src/renderer/pages/EscalaPage.tsx` entre as linhas ~531 e ~634.
