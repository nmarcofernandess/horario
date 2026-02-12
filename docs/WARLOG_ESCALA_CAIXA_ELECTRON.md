# WARLOG — Escala de Caixa Electron

> ⚠️ **Documento legado/histórico**  
> Warlog ativo do projeto: `docs/WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md`.
> Este arquivo fica apenas para rastreabilidade da fase inicial.

> Product Owner Mode: Backlog completo, spec, plano e rastreamento.
> Data: 2026-02-12

---

## FASE 1 — VISAO GERAL

### Mind Map

```plantuml
@startmindmap
* 🔥 GUERRA: Escala Caixa Electron
** 📦 Epico 1: Layout
*** T1: Sidebar escura
*** T2: Cor de destaque (âmbar)
*** T3: Container max-width
*** T4: Hierarquia tipográfica
** 📦 Epico 2: Escala
*** T5: Vista Calendário (grid)
*** T6: Tab Calendário + Tabela
*** T7: Tradução termos
*** T8: Células coloridas
*** T9: Paginação tabela
** 📦 Epico 3: Resiliência
*** T10: Indicador API
*** T11: Retry / Reconectar
*** T12: Loading states
** 📦 Epico 4: Configuração
*** T13: Turnos (listar)
*** T14: Exceções (CRUD)
*** T15: Demand (CRUD)
*** T16: Mosaico CRUD (API + UI)
*** T16b: Rodízio CRUD (API + UI)
** 📦 Epico 5: Manutenção/repo
*** T17: Unificar docs (SISTEMA_ESCALAFLOW.md)
*** T18: Remover docs antigos (ANALYST, AUDITORIA, DADOS)
*** T19: Limpar data/ (processed→gitignore, fixtures)
*** T20: Remover seed_db_from_csv.py
*** T21: Seed JSON (opcional — migrar CSVs para 1 JSON)
** 📦 Epico 6: Perfil usuário
*** T22: Página de perfil (foto, nome, tema) — sem auth, local
** 🚫 Fora de Escopo
*** API Python (já pronta)
** 🎯 Objetivo Final
*** App Electron com identidade visual
*** Escala em grid + tabela
*** Configuração funcional
@endmindmap
```

### Definições

```
MISSAO: App Electron de gestão de escala de caixa com identidade visual,
        vista calendário para imprimir e resiliência à API.

PRODUTO: Multi-tenant SaaS — vendido para várias empresas. Cada cliente configura
         tudo pela UI (colaboradores, turnos, mosaico, rodízio, exceções).
         Não há suporte com seed manual; tudo didático e auto-serviço.

OBJETIVO: RH consegue gerar escala, ver em grid/tabela, exportar e configurar
          sem esbarrar em layout genérico ou API offline sem feedback.

ESCOPO:
  ✅ FAZ PARTE:
     - Layout (sidebar escura, accent, container)
     - Escala (grid calendário, tabela, paginação)
     - Resiliência (API status, retry, loading)
     - Configuração (Turnos, Exceções, Demand, Mosaico, Rodízio)
     - API: adicionar endpoints para Mosaico e Rodízio (repo já tem save/load)
  🚫 NÃO FAZ PARTE:
     - Reescrever API Python do zero
     - Dark mode toggle (pode vir depois)

PRAZO: Sem data fixa; ordem de execução definida.
```

---

## FASE 2 — DUMP + CATEGORIZACAO

```
DUMP CATEGORIZADO:

✨ FEATURES:
- [ ] Sidebar escura (slate-900)
- [ ] Cor de destaque no nav ativo (amber)
- [ ] Vista Calendário (grid dia×colaborador)
- [ ] Tab Calendário como default
- [ ] Células coloridas por status
- [ ] Paginação na tabela de alocações
- [ ] Indicador API online/offline
- [ ] Botão Reconectar
- [ ] Skeleton/spinner durante generate
- [ ] Turnos: listar da API
- [ ] Exceções: listar + adicionar
- [ ] Demand: listar + adicionar slots
- [ ] Mosaico: definir matriz colaborador×dia→turno (seg–sáb)
- [ ] Rodízio: definir domingos trabalhados e folga compensatória

🔧 REFACTORS:
- [ ] Tradução WORK→Trabalho, FOLGA→Folga, ABSENCE→Ausência
- [ ] Container max-w-6xl no main
- [ ] Hierarquia tipográfica (H1/H2)

🧹 CHORES:
- [ ] Remover frontend-prototype (protótipo obsoleto)
- [ ] Limpar imports não usados
- [x] Unificar docs → SISTEMA_ESCALAFLOW.md
- [x] Remover docs antigos (ANALYST, AUDITORIA, DADOS)
- [x] Limpar data/ (processed→gitignore)
- [x] Remover seed_db_from_csv.py redundante

📚 DOCS:
- [ ] Migrar seed para JSON único (opcional)
```

---

## FASE 3 — WBS (Work Breakdown Structure)

```plantuml
@startwbs
* Escala Caixa Electron
** Epico 1: Layout
*** T1: Sidebar escura
*** T2: Cor de destaque nav
*** T3: Container max-width
*** T4: Hierarquia tipográfica
** Epico 2: Escala
*** T5: Vista Calendário grid
*** T6: Tab Calendário + Tabela
*** T7: Tradução termos
*** T8: Células coloridas
*** T9: Paginação tabela
** Epico 3: Resiliência
*** T10: Indicador API
*** T11: Retry / Reconectar
*** T12: Loading states
** Epico 4: Configuração
*** T13: Turnos listar
*** T14: Exceções CRUD
*** T15: Demand CRUD
*** T16: Mosaico CRUD (API + UI)
*** T16b: Rodízio CRUD (API + UI)
** Chore
*** T0: Remover frontend-prototype
** Epico 5: Manutenção
*** T17: Unificar docs
*** T18: Remover docs antigos
*** T19: Limpar data/
*** T20: Remover seed_db_from_csv
*** T21: Seed JSON (opcional)
@endwbs
```

### Prioridade

```
🔴 NÚCLEO (sem isso não existe produto):
- T5: Vista Calendário (principal para imprimir)
- T6: Tab Calendário + Tabela
- T1: Sidebar escura
- T2: Cor de destaque

🟡 IMPORTANTE (melhora significativamente):
- T7: Tradução termos
- T8: Células coloridas
- T3: Container max-width
- T10: Indicador API
- T11: Retry
- T12: Loading
- T14: Exceções
- T15: Demand

🟢 NICE-TO-HAVE:
- T4: Hierarquia tipográfica
- T9: Paginação
- T13: Turnos
- T16: Mosaico CRUD
- T16b: Rodízio CRUD
```

---

## FASE 4 — DEPENDENCIAS + SEQUENCIA

### Matriz

| Task | Depende de | Bloqueia | Paralelo? |
|------|------------|----------|-----------|
| T0  | -          | -        | -         |
| T1  | -          | -        | T2, T3    |
| T2  | -          | -        | T1, T3    |
| T3  | -          | -        | T1, T2    |
| T4  | T1, T2     | -        | -         |
| T5  | -          | T6       | -         |
| T6  | T5         | -        | -         |
| T7  | T6         | -        | T8        |
| T8  | T6         | -        | T7        |
| T9  | T6         | -        | -         |
| T10 | -          | -        | T11, T12  |
| T11 | -          | -        | T10, T12  |
| T12 | -          | -        | T10, T11  |
| T13 | -          | -        | T14, T15  |
| T14 | -          | -        | T13, T15  |
| T15 | -          | -        | T13, T14  |
| T16 | Mosaico CRUD | -        | -         |
| T16b | Rodízio CRUD | -        | -         |

### Fluxo de Dependências

```plantuml
@startuml
start

:T0: Remover frontend-prototype;

fork
  :Epico 1: Layout;
  :T1: Sidebar escura;
  :T2: Cor de destaque;
  :T3: Container max-width;
  :T4: Hierarquia tipográfica;
fork again
  :Epico 2: Escala;
  :T5: Vista Calendário grid;
  :T6: Tab Calendário + Tabela;
  :T7: Tradução;
  :T8: Células coloridas;
  :T9: Paginação;
fork again
  :Epico 3: Resiliência;
  :T10: Indicador API;
  :T11: Retry;
  :T12: Loading;
fork again
  :Epico 4: Configuração;
  :T13: Turnos;
  :T14: Exceções;
  :T15: Demand;
  :T16: Mosaico CRUD;
  :T16b: Rodízio CRUD;
end fork

:Integração final;
stop
@enduml
```

### Caminho Crítico

```
T0 → T5 → T6 → T7/T8 → Integração
(Remover proto → Calendário → Tabs → Tradução/Cores)
```

---

## FASE 5 — DASHBOARD DE GUERRA

```
════════════════════════════════════════════════════════════════════
🔥 GUERRA: Escala Caixa Electron
════════════════════════════════════════════════════════════════════

📊 STATUS GERAL: 5/17 tasks | 🟢 7 | 🟡 5 | 🔴 0 | ✅ 5

════════════════════════════════════════════════════════════════════
📋 BACKLOG
════════════════════════════════════════════════════════════════════

| ID  | Task                      | Tipo | Status    | Viab. | Dep.  | Est. |
|-----|---------------------------|------|-----------|-------|-------|------|
| T0  | Remover frontend-prototype| 🧹   | ✅ Done   | 🟢    | -     | P    |
| T1  | Sidebar escura            | ✨   | ✅ Done   | 🟢    | -     | P    |
| T2  | Cor de destaque nav      | ✨   | ✅ Done   | 🟢    | -     | P    |
| T3  | Container max-width      | 🔧   | ✅ Done   | 🟢    | -     | P    |
| T4  | Hierarquia tipográfica   | 🔧   | ✅ Done   | 🟢    | T1,T2 | P    |
| T5  | Vista Calendário grid    | ✨   | ✅ Done   | 🟢    | -     | M    |
| T6  | Tab Calendário + Tabela  | ✨   | ✅ Done   | 🟢    | T5    | M    |
| T7  | Tradução termos          | 🔧   | 📋 Backlog| 🟢    | T6    | P    |
| T8  | Células coloridas        | ✨   | 📋 Backlog| 🟢    | T6    | P    |
| T9  | Paginação tabela         | ✨   | 📋 Backlog| 🟢    | T6    | M    |
| T10 | Indicador API            | ✨   | 📋 Backlog| 🟢    | -     | P    |
| T11 | Retry / Reconectar       | ✨   | 📋 Backlog| 🟢    | -     | P    |
| T12 | Loading states           | ✨   | 📋 Backlog| 🟢    | -     | P    |
| T13 | Turnos listar            | ✨   | 📋 Backlog| 🟢    | -     | P    |
| T14 | Exceções CRUD            | ✨   | 📋 Backlog| 🟢    | -     | M    |
| T15 | Demand CRUD              | ✨   | 📋 Backlog| 🟢    | -     | M    |
| T16 | Mosaico CRUD (API + UI) | 🔍   | 📋 Backlog| 🟡    | -     | P    |
| T16b | Rodízio CRUD (API + UI) | 🔍   | 📋 Backlog| 🟡    | -     | P    |
| T17 | Unificar docs            | 🧹   | ✅ Done   | 🟢    | -     | P    |
| T18 | Remover docs antigos     | 🧹   | ✅ Done   | 🟢    | T17   | P    |
| T19 | Limpar data/             | 🧹   | ✅ Done   | 🟢    | -     | P    |
| T20 | Remover seed_db_from_csv | 🧹   | ✅ Done   | 🟢    | -     | P    |
| T21 | Seed JSON (opcional)     | ✨   | 📋 Backlog| 🟡   | -     | M    |

════════════════════════════════════════════════════════════════════
```

---

## FASE 6 — RFE (Tasks Complexas)

### RFE: T5 — Vista Calendário Grid

```
════════════════════════════════════════════════════════════════════
🔍 RFE: T5 - Vista Calendário (grid dia×colaborador)
════════════════════════════════════════════════════════════════════

GATILHO:
└── Usuário na EscalaPage, com assignments carregados

TRILHA DE EXECUCAO:
└── assignments (API) → agrupar por work_date →
    pivot: linhas=datas, colunas=colaboradores →
    célula = status + shift_code →
    renderizar <table> com classes por status

DADOS:
└── Entrada: assignments[] { work_date, employee_id, status, shift_code }
    Processamento: groupBy date, map employee→cell
    Saída: matrix[date][employee] = { status, shift }

CONFLITOS POSSÍVEIS:
└── ❌ assignments vazio → mostrar "Execute Atualizar escala"
    ❌ datas fora de ordem → sort por work_date
    ❌ colaboradores diferentes por dia → union de todos employee_id

CRITÉRIO DE DONE:
└── [ ] Grid renderiza com datas em linhas
    [ ] Colunas = colaboradores (ordenados)
    [ ] Célula mostra FOL/CAI1/DOM/AUS conforme status
    [ ] Cores: verde trabalho, âmbar folga, azul domingo, vermelho ausência
```

### RFE: T14 — Exceções CRUD

```
════════════════════════════════════════════════════════════════════
🔍 RFE: T14 - Exceções CRUD
════════════════════════════════════════════════════════════════════

GATILHO:
└── Usuário na ConfiguracaoPage, aba Exceções

TRILHA:
└── GET /exceptions → listar tabela →
    Form (employee_id, data, tipo) → POST /exceptions →
    reload list

API JÁ EXISTE: GET/POST /exceptions

CRITÉRIO DE DONE:
└── [ ] Lista exceções do período
    [ ] Form adicionar (employee, data, tipo: VACATION|MEDICAL_LEAVE|SWAP|BLOCK)
    [ ] Após criar, lista atualiza
```

---

## FASE 7 — TIMELINE (Gantt)

```plantuml
@startgantt
title Timeline Escala Caixa Electron

Project starts 2026-02-12

-- Sprint 1: Limpeza + Layout --
[T0: Remover prototype] lasts 0 days
[T1: Sidebar escura] lasts 1 day
[T2: Cor destaque] lasts 1 day
[T2] starts at [T1]'s end
[T3: Container] lasts 1 day
[T3] starts at [T1]'s end
[T4: Tipografia] lasts 1 day
[T4] starts at [T2]'s end

-- Sprint 2: Escala --
[T5: Vista Calendário] lasts 2 days
[T5] starts at [T0]'s end
[T6: Tab Calendário+Tabela] lasts 1 day
[T6] starts at [T5]'s end
[T7: Tradução] lasts 1 day
[T7] starts at [T6]'s end
[T8: Células coloridas] lasts 1 day
[T8] starts at [T6]'s end
[T9: Paginação] lasts 1 day
[T9] starts at [T6]'s end

-- Sprint 3: Resiliência --
[T10: Indicador API] lasts 1 day
[T10] starts at [T0]'s end
[T11: Retry] lasts 1 day
[T11] starts at [T10]'s end
[T12: Loading] lasts 1 day
[T12] starts at [T10]'s end

-- Sprint 4: Configuração --
[T13: Turnos] lasts 1 day
[T13] starts at [T0]'s end
[T14: Exceções] lasts 2 days
[T14] starts at [T13]'s end
[T15: Demand] lasts 2 days
[T15] starts at [T13]'s end
[T16: Mosaico CRUD] lasts 3 days
[T16b: Rodízio CRUD] lasts 2 days
[T16b] starts at [T16]'s end
[T16] starts at [T14]'s end

@endgantt
```

### Milestones

```
📍 MILESTONES:

M1: Limpeza + Layout (T0, T1–T4) — identidade visual
M2: Escala completa (T5–T9) — grid + tabela + tradução
M3: Resiliência (T10–T12) — API status + retry + loading
M4: Configuração (T13–T16b) — Turnos, Exceções, Demand, Mosaico, Rodízio
```

---

## FASE 8 — LOG + RECALIBRAÇÃO

```
════════════════════════════════════════════════════════════════════
📜 LOG DE GUERRA
════════════════════════════════════════════════════════════════════

[2026-02-12] INÍCIO
└── Guerra iniciada: Escala Caixa Electron
    Objetivo: Layout + Escala grid + Resiliência + Config
    Spec: SISTEMA_ESCALAFLOW.md + BUILD
    Backlog: 17 tasks

[2026-02-12] CHORE ✅
└── T0: Remover frontend-prototype — CONCLUÍDO
    Motivo: Sistema limpo, protótipo obsoleto

[2026-02-12] LAYOUT ✅
└── T1: Sidebar escura — CONCLUÍDO
    bg-slate-900, nav amber-600 ativo, ícones lucide

[2026-02-12] LAYOUT ✅
└── T3: Container max-width — CONCLUÍDO
    main com max-w-6xl mx-auto
└── T4: Hierarquia tipográfica — CONCLUÍDO
    h1 text-2xl font-semibold em todas as páginas

[2026-02-12] ESCALA ✅
└── T5: Vista Calendário grid — CONCLUÍDO
    Grid dia×colaborador, células coloridas (verde/âmbar/azul/vermelho)
└── T6: Tab Calendário + Tabela — CONCLUÍDO
    Calendário como default, Tabela na segunda aba

[2026-02-12] MANUTENÇÃO ✅
└── T17: Unificar docs → SISTEMA_ESCALAFLOW.md
    Consolida FLUXO_USUARIO + DADOS + resumo BUILD
└── T18: Remover docs antigos (ANALYST, AUDITORIA, DADOS)
└── T19: data/processed/ → .gitignore
└── T20: Remover seed_db_from_csv.py (redundante com seed.py)

════════════════════════════════════════════════════════════════════
```

### Recalibração

```
RECALIBRAÇÃO [2026-02-12]:

PROGRESSO:
├── Tasks concluídas: T0, T1
├── Tasks em andamento: 0
└── Tasks bloqueadas: 0

DESBLOQUEIOS:
└── Nenhum; todas tasks iniciais podem iniciar (exceto T4 que depende de T1,T2)

NOVOS ITENS:
└── Nenhum

⚡ PRÓXIMO PASSO IMEDIATO:
└── T2: Já integrado em T1 (amber no nav ativo)
    T3: Container max-width no main
```

---

## RESUMO DA SPEC (referência)

| Doc | Conteúdo |
|-----|----------|
| **SISTEMA_ESCALAFLOW.md** | **Doc unificado:** fluxo, dados, setup, arquitetura resumida |
| BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md | Motor de compliance (PlantUML, ER, fluxos) |

---

## CHECKLIST DE IMPLEMENTAÇÃO (por task)

| ID | Critério de Done |
|----|------------------|
| T0 | ✅ frontend-prototype/ removido |
| T1 | ✅ Sidebar: bg-slate-900, texto stone-100, nav amber |
| T2 | Nav ativo: bg-amber-600 ou amber-600/90 |
| T3 | ✅ Main: max-w-6xl mx-auto no container |
| T4 | ✅ H1 text-2xl font-semibold em páginas |
| T5 | ✅ Grid: linhas=datas, colunas=colaboradores, célula=status colorido |
| T6 | ✅ Tabs: Calendário (default) + Tabela |
| T7 | WORK→Trabalho, FOLGA→Folga, ABSENCE→Ausência |
| T8 | Células: verde work, âmbar folga, azul DOM, vermelho ausência |
| T9 | Tabela com paginação (ex: 20 por página) |
| T10 | Badge "Conectado" verde ou "API offline" vermelho |
| T11 | Botão "Reconectar" quando fetch falha |
| T12 | Spinner ou skeleton durante scale.generate |
| T13 | GET /shifts → tabela turnos |
| T14 | GET/POST /exceptions → listar + form adicionar |
| T15 | GET/POST /demand-profile → listar + form adicionar |
| T16 | Mosaico: matriz colaborador×dia→turno (API + UI) |
| T16b | Rodízio: domingos + folga compensatória (API + UI) |
| T17 | ✅ SISTEMA_ESCALAFLOW.md criado |
| T18 | ✅ ANALYST, AUDITORIA, DADOS removidos |
| T19 | ✅ data/processed/ no .gitignore |
| T20 | ✅ seed_db_from_csv.py removido |
| T21 | Migrar fixtures para seed.json único |
