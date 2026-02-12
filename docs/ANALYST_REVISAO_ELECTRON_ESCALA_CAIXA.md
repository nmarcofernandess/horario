# LOGICA — Revisão Electron Escala de Caixa (Analyst v2)

> Destilação de gaps, layout e roadmap. O que existe, o que falta, o que está feio e por quê.
> Data: 2026-02-12

---

## TL;DR EXECUTIVO

O app Electron + shadcn está **funcional em MVP** (API, spawn Python, páginas básicas) mas **incompleto e visualmente genérico**. O layout usa shadcn default sem identidade; a página Escala não oferece visão calendário (grid para imprimir); a Configuração é placeholder; faltam tratamento de API offline, tradução de termos técnicos e hierarquia visual clara. O protótipo em `frontend-prototype/` foi removido (sistema limpo); a direção visual (sidebar escura, âmbar, grid calendário) está documentada no WARLOG.

---

## FASE 1 — ESCUTA ATIVA

**O que o usuário QUER:**
- Revisão honesta: "longe de acabar" + "layout é lixo"
- Especificação executável: o que falta, em que ordem, com critérios claros

**O que ENTRA:** Código atual, docs (FLUXO_USUARIO, DADOS_E_REVISAO), protótipo anterior.

**O que SAI:** Documento com gaps priorizados, proposta de layout e checklist de implementação.

---

## FASE 2 — SEPARACAO: O QUE É FIXO vs O QUE FALTA

### 2.1 O que JÁ EXISTE (regras fixas do sistema)

| Componente | Status | Comentário |
|------------|--------|------------|
| API FastAPI | ✅ | Endpoints prontos |
| Spawn Python | ✅ | Main process inicia uvicorn |
| Layout base | ✅ | Sidebar + main |
| EscalaPage | ⚠️ Parcial | Período + gerar + tabela + violações + export |
| ColaboradoresPage | ⚠️ Parcial | CRUD colaboradores e setores |
| PedidosPage | ⚠️ Parcial | Pendentes + novo pedido |
| ConfiguracaoPage | ❌ Placeholder | Apenas tabs vazias |

### 2.2 O que FALTA (variáveis / trabalho pendente)

```
MAQUINA: Implementação Electron Escala de Caixa

REGRAS FIXAS (referência):
- FLUXO_USUARIO.md define jornada do RH
- API já expõe o necessário
- Protótipo definiu calendário grid como formato principal

TRABALHO PENDENTE (prioridade):
1. LAYOUT: Identidade visual (sidebar escura, cor de destaque, hierarquia)
2. ESCALA: Vista calendário (grid dia×colaborador) além da tabela
3. CONFIGURAÇÃO: Conteúdo real (Turnos, Mosaico, Rodízio, Exceções, Demand)
4. RESILIÊNCIA: API offline, loading, retry
5. UX: Tradução WORK→Trabalho, FOLGA→Folga, etc.
6. PAGINAÇÃO: Tabela de alocações sem limite 50
```

---

## FASE 3 — MAPA DE ENTIDADES (visão do produto)

```plantuml
@startuml
left to right direction
skinparam actorStyle awesome

actor "RH / Gestor" as RH

rectangle "App Electron" {
  usecase "Definir período" as UC1
  usecase "Gerar escala" as UC2
  usecase "Ver calendário (grid)" as UC3
  usecase "Ver tabela" as UC4
  usecase "Ver violações" as UC5
  usecase "Exportar HTML/MD" as UC6
  usecase "Cadastrar colaborador" as UC7
  usecase "Aprovar/rejeitar pedido" as UC8
  usecase "Configurar turnos" as UC9
  usecase "Configurar mosaico" as UC10
  usecase "Configurar rodízio" as UC11
  usecase "Adicionar exceção" as UC12
}

RH --> UC1
RH --> UC2
RH --> UC3
RH --> UC4
RH --> UC5
RH --> UC6
RH --> UC7
RH --> UC8
RH --> UC9
RH --> UC10
RH --> UC11
RH --> UC12

note right of UC3 : Vista principal para imprimir
note right of UC9 : Hoje: placeholder
@enduml
```

### Hierarquia de telas

```
APP
├── LAYOUT
│   ├── Sidebar (navegação)
│   └── Main (conteúdo)
├── ESCALA
│   ├── Período + Ação
│   ├── Vista Calendário (grid) ← FALTA
│   ├── Vista Tabela
│   ├── Violações
│   └── Export
├── COLABORADORES
│   ├── Colaboradores (CRUD)
│   └── Setores (CRUD)
├── PEDIDOS
│   ├── Pendentes (aprovar/rejeitar)
│   └── Novo pedido
└── CONFIGURAÇÃO ← QUASE TUDO FALTA
    ├── Turnos
    ├── Mosaico
    ├── Rodízio
    ├── Exceções
    └── Demand
```

---

## FASE 4 — FLUXO LOGICO: Jornada do usuário

```plantuml
@startuml
start

:Abrir app;
:Electron spawna Python API;

if (API pronta?) then (sim)
else (não)
  #pink:Mostrar "API não disponível";
  :Botão "Reiniciar conexão";
  stop
endif

:Usuário navega para Escala;

:Definir período (De/Até);
:Clicar "Atualizar escala";

:Chamar POST /scale/generate;

if (Gerou?) then (sim)
  :Carregar assignments + violations;
  :Exibir vista escolhida;
  
  if (Vista?) then (Calendário)
    :Renderizar grid dia × colaborador;
  else (Tabela)
    :Renderizar tabela com paginação;
  endif
  
  if (Tem violações?) then (sim)
    :Exibir alertas expandíveis;
  endif
else (erro)
  #pink:Mostrar mensagem de erro;
endif

:Usuário pode exportar HTML/MD;

stop
@enduml
```

---

## FASE 5 — REGRAS DO LAYOUT E GAPS

### 5.1 Problemas de layout identificados

| Problema | Descrição | Referência |
|----------|-----------|------------|
| **Genericidade** | shadcn default neutro, sem identidade | Protótipo tinha stone-900 + amber |
| **Sidebar** | Clara demais, pouco contraste | Layout atual: `bg-muted/40` |
| **Cor de destaque** | Nenhum accent forte | Protótipo: amber-600 no ativo |
| **Content width** | Sem max-width, conteúdo se espalha | Protótipo: `max-w-6xl mx-auto` |
| **Hierarquia** | Títulos fracos | Falta peso visual nos H1/H2 |
| **Células calendário** | Não existem | Protótipo: cores por status (verde/âmbar/azul) |

### 5.2 Regras de layout propostas

```
REGRAS DE LAYOUT — Escala Caixa

PODE:
- Sidebar escura (neutral-900 / slate-900)
- Cor de destaque âmbar ou laranja suave
- max-w-6xl no main para leitura confortável
- Grid calendário com células coloridas por status

DEVE:
- Item ativo na nav com destaque claro
- Título da página em destaque
- Tab Calendário como default na Escala

NÃO DEVE:
- Deixar termos técnicos (WORK, FOLGA) sem tradução
- Ocultar erros de API em silêncio
- Mostrar tabela com "50 de N" sem paginação real
```

### 5.3 Tabela de decisão: Layout

```
┌──────────────────┬─────────────────────┬────────────────────────────┐
│ Elemento         │ Estado atual        │ Ação                       │
├──────────────────┼─────────────────────┼────────────────────────────┤
│ Sidebar          │ bg-muted/40         │ Sidebar escura (slate-900)  │
│ Nav ativo        │ bg-accent           │ Amber/laranja destaque      │
│ Main content     │ Sem max-width       │ max-w-6xl mx-auto           │
│ Escala vista     │ Só tabela           │ Tab Calendário + Tabela     │
│ Células status   │ Badge texto         │ Cores (verde/âmbar/azul)    │
│ Configuração     │ Placeholder         │ Implementar ou remover tab  │
│ API offline      │ Erro genérico       │ Estado dedicado + retry     │
└──────────────────┴─────────────────────┴────────────────────────────┘
```

---

## FASE 6 — DIAGRAMAS PLANTUML

### 6.1 Mind Map — Escopo da revisão

```plantuml
@startmindmap
* Revisão Electron Escala Caixa
** Layout
*** Sidebar escura
*** Cor de destaque (âmbar)
*** Container max-width
*** Hierarquia tipográfica
** Escala
*** Vista Calendário (grid)
*** Vista Tabela com paginação
*** Tradução termos (WORK→Trabalho)
*** Células coloridas por status
** Configuração
*** Turnos (CRUD)
*** Mosaico (template semanal)
*** Rodízio domingos
*** Exceções (férias, atestado)
*** Demand profile
** Resiliência
*** Indicador API online/offline
*** Retry quando falha
*** Loading states
** Pendente menor
*** Paginação tabela
*** Export com nome de arquivo
@endmindmap
```

### 6.2 Activity — Fluxo de geração da escala

```plantuml
@startuml
start

:Usuário na página Escala;
:Definir período (De, Até);

: Clicar "Atualizar escala";

:POST /scale/generate;

if (Resposta OK?) then (sim)
  :Interpretar resultado;
  :Carregar assignments e violations;
  
  if (Vista = Calendário?) then (sim)
    :Agrupar por data;
    :Montar grid (colunas = colaboradores);
    :Colorir células (WORK=FOL=DOM=AUS);
  else (Tabela)
    :Exibir com paginação;
  endif
  
  if (Tem violações?) then (sim)
    :Exibir seção de alertas;
  endif
else (erro)
  #pink:Exibir mensagem;
  :Permitir retry;
endif

stop
@enduml
```

### 6.3 ER — Entidades da UI (simplificado)

```plantuml
@startuml
entity "EscalaPage" as EP {
  * period_start : Date
  * period_end : Date
  --
  assignments : List<Assignment>
  violations : List<Violation>
  view_mode : Calendario | Tabela
}

entity "Assignment" as A {
  * work_date : Date
  * employee_id : String
  --
  status : WORK | FOLGA | ABSENCE
  shift_code : String
  minutes : Int
}

entity "Violation" as V {
  * employee_id : String
  * rule_code : String
  --
  severity : CRITICAL | HIGH
  detail : String
}

EP ||--o{ A : contém
EP ||--o{ V : contém
@enduml
```

---

## FASE 7 — ROADMAP EXECUTÁVEL

### Prioridade 1 — Layout (impacto visual imediato)

| # | Tarefa | Critério de done |
|---|--------|------------------|
| 1 | Sidebar escura | `bg-slate-900` ou `bg-neutral-900`, texto claro |
| 2 | Cor de destaque | Item ativo com amber-600 ou laranja |
| 3 | Container main | `max-w-6xl mx-auto` no conteúdo |
| 4 | Tipografia | H1/H2 com peso e hierarquia clara |

### Prioridade 2 — Escala (funcionalidade principal)

| # | Tarefa | Critério de done |
|---|--------|------------------|
| 5 | Tab Calendário | Grid dia×colaborador com células coloridas |
| 6 | Tab Tabela | Manter, adicionar paginação real |
| 7 | Tradução | WORK→Trabalho, FOLGA→Folga, ABSENCE→Ausência |
| 8 | Células coloridas | Verde trabalho, âmbar folga, azul domingo, vermelho ausência |

### Prioridade 3 — Resiliência

| # | Tarefa | Critério de done |
|---|--------|------------------|
| 9 | Indicador API | Badge/indicador "Conectado" ou "API offline" |
| 10 | Retry | Botão "Reconectar" quando API falha |
| 11 | Loading | Skeleton ou spinner durante generate |

### Prioridade 4 — Configuração

| # | Tarefa | Critério de done |
|---|--------|------------------|
| 12 | Turnos | Listar turnos da API, edição mínima |
| 13 | Exceções | Listar + adicionar (API já existe) |
| 14 | Demand | Listar + adicionar slots (API já existe) |
| 15 | Mosaico / Rodízio | Ou integrar ou remover tab até ter backend |

---

## DISCLAIMERS CRÍTICOS

- **API Python:** O spawn assume `python3` no PATH. Em máquinas sem venv ativo, pode falhar.
- **Configuração:** Mosaico e Rodízio dependem de seed/CSV hoje; API não expõe CRUD completo. Ou documentar "carregar via seed" ou expandir API.
- **Export:** `window.open` para download pode ser bloqueado por pop-up em alguns contextos.

---

## RESUMO FINAL

```
┌─────────────────────────────────────────────────────────────────┐
│  O QUE TEM:  MVP funcional — API, spawn, CRUD básico, export     │
│  O QUE FALTA: Identidade visual, calendário grid, Config real   │
│  O QUE MUDAR: Layout = sidebar escura + accent + grid          │
│  ORDEM: Layout → Escala grid → Resiliência → Config             │
└─────────────────────────────────────────────────────────────────┘
```

**O protótipo tinha a direção certa.** O Electron atual perdeu identidade ao adotar shadcn "virgem". A revisão deve recuperar: sidebar escura, cor de destaque, grid calendário como vista principal e conteúdo real nas abas de Configuração.
