# PRD: Escala Electron — Backlog Completo (T7–T21)

> **Workflow:** feature
> **Budget sugerido:** high
> **Criado em:** 2026-02-12
> **Fonte:** WARLOG_ESCALA_CAIXA_ELECTRON.md
> **Ambiente:** Cursor IDE — agentes expawnados (não Claude Code)

---

## Visão Geral

**Produto multi-tenant:** O EscalaFlow será vendido para várias empresas. Cada cliente configura tudo pela UI — colaboradores, turnos, mosaico, rodízio, exceções, demanda. **Não há suporte com seed manual.** Tudo deve ser didático e auto-serviço.

**Modelo:** Sistema offline (instalação local). Não temos login, pagamento ou autenticação por email agora. Teremos página de perfil simples (foto, nome, tema) para o usuário sentir que o sistema é dele — sem validação de credenciais.

O app já tem: layout (sidebar escura, âmbar), vista calendário (grid), tabs Calendário/Tabela, export HTML/MD. Este PRD cobre o backlog pendente **com a premissa de produto vendável**: configuração completa pela UI, incluindo Mosaico e Rodízio.

**Objetivo:** App completo e auto-serviço — resiliência, configuração real (incluindo Mosaico e Rodízio), tradução, paginação.

**Referência:** `docs/WARLOG_ESCALA_CAIXA_ELECTRON.md`

---

## Requisitos Funcionais

### Escala (Epico 2)

- [ ] **T7 — Tradução termos:** Garantir que WORK→Trabalho, FOLGA→Folga, ABSENCE→Ausência apareçam em todos os lugares (grid, tabela, violações, pedidos). Hoje `format.ts` já tem; auditar se falta em algum componente.
- [ ] **T8 — Células coloridas:** Verde (trabalho), âmbar (folga), azul (domingo), vermelho (ausência). Já implementado no grid; garantir que tabela também use `CellStatus` ou equivalente.
- [ ] **T9 — Paginação tabela:** A tabela de alocações na aba Tabela deve ter paginação real (ex.: 20 por página) em vez de slice fixo de 50.

### Resiliência (Epico 3)

- [ ] **T10 — Indicador API:** Badge ou indicador visível mostrando "Conectado" (verde) ou "API offline" (vermelho). Deve reagir a falhas de fetch.
- [ ] **T11 — Retry / Reconectar:** Botão "Reconectar" visível quando API está offline ou quando fetch falha. Ao clicar, tenta novamente e atualiza o estado.
- [ ] **T12 — Loading states:** Spinner ou skeleton durante chamada a `POST /scale/generate` ("Gerar escala"). Feedback imediato durante a operação.

### Configuração (Epico 4)

- [ ] **T13 — Turnos:** Na ConfiguracaoPage, aba Turnos, listar turnos da API (`GET /shifts`). Exibir código, duração (minutos), tipo (WEEKDAY/SUNDAY).
- [ ] **T14 — Exceções CRUD:** Na ConfiguracaoPage, aba Exceções: listar exceções (`GET /exceptions`) e formulário para adicionar (`POST /exceptions`). Campos: colaborador, data, tipo (VACATION, MEDICAL_LEAVE, SWAP, BLOCK).
- [ ] **T15 — Demand CRUD:** Na ConfiguracaoPage, aba Demand: listar slots de demanda (`GET /demand-profile`) e formulário para adicionar (`POST /demand-profile`). Campos: data, slot (HH:MM), mínimo de pessoas.
- [ ] **T16 — Mosaico CRUD:** Aba Mosaico: definir quem trabalha em qual dia da semana (SEG–SAB) e em qual turno. API: GET/POST week-day-template (ou equivalente). UI: tabela editável (colaborador × dia → turno).
- [ ] **T16b — Rodízio CRUD:** Aba Rodízio: definir quem trabalha em cada domingo e quando folga (folga compensatória). API: GET/POST sunday-rotation. UI: tabela editável (domingo, colaborador, folga_date).
- [ ] **T16c — API Mosaico/Rodízio:** Backend já tem `save_weekday_template` e `save_sunday_rotation` no repo; criar rotas para expor GET/POST. Schemas Pydantic para request/response.

### Perfil do usuário (Epico 6)

- [ ] **T22 — Página de perfil:** Página simples para o usuário configurar nome, foto e tema (preferências visuais). Objetivo: o gestor/RH sentir que "o sistema é meu". **Não é login** — sem validação de email/senha. Dados locais (localStorage ou arquivo). Acesso via sidebar ou ícone de usuário.

### Manutenção / Repo (Epico 5)

- [ ] **T21 — Seed JSON (nice-to-have):** Migrar CSVs para `seed.json` para facilitar demo/onboarding. **Prioridade baixa** — o produto deve funcionar 100% pela UI.

---

## Critérios de Aceitação

- [ ] Indicador API aparece na header ou sidebar; muda conforme health check.
- [ ] Botão Reconectar aparece quando API offline ou erro; ao clicar, tenta `GET /health` e recarrega dados.
- [ ] Botão "Gerar escala" mostra loading (spinner/disabled) durante a requisição.
- [ ] Tabela de alocações: controles de paginação (anterior/próxima ou página N de M); exibe 20 itens por página.
- [ ] Configuração > Turnos: tabela com turnos da API.
- [ ] Configuração > Exceções: lista + form adicionar; após criar, lista atualiza.
- [ ] Configuração > Demand: lista + form adicionar; após criar, lista atualiza.
- [ ] Mosaico: usuário pode listar e editar matriz (colaborador × dia → turno).
- [ ] Rodízio: usuário pode listar e editar regras (domingo trabalhado → colaborador, folga compensatória).
- [ ] T7: Nenhum componente exibe WORK/FOLGA/ABSENCE sem tradução.
- [ ] T8: Células coloridas no grid e na tabela.
- [ ] T21: `seed.json` existe; `seed.py` popula com sucesso a partir dele.
- [ ] T22: Página de perfil acessível; usuário pode editar nome, foto e tema; dados persistem localmente.

---

## Constraints

- Manter identidade visual (sidebar escura, âmbar) já aplicada.
- ConfiguracaoPage já existe com tabs; adicionar conteúdo em todas.
- **Pode adicionar endpoints** na API para Mosaico e Rodízio — o repo já tem `save_weekday_template` e `save_sunday_rotation`.

---

## Fora do Escopo

- Reescrever API do zero.
- Dark mode toggle.
- Multi-tenancy (isolamento por empresa) — foco em single-tenant por agora; estrutura deve permitir evoluir.

---

## Serviços Envolvidos

- [x] Frontend (electron-app: React, Vite)
- [x] Backend (API — adicionar rotas para mosaico e rodízio)
- [ ] Scripts (seed.py — T21, prioridade baixa)
- [ ] Database (indireto via API)

---

## Budget Sugerido

**Recomendação:** high — inclui T7–T21 + Mosaico/Rodízio CRUD completo (API + UI). Produto deve ser auto-serviço e didático. Coder sonnet; critic opus.

---

## Notas Adicionais

- **Endpoints API existentes:** `GET /shifts`, `GET /exceptions`, `POST /exceptions`, `GET /demand-profile`, `POST /demand-profile`, `GET /health`.
- **Endpoints a criar:** `GET /week-day-template`, `POST /week-day-template` (ou batch), `GET /sunday-rotation`, `POST /sunday-rotation` (ou batch). Repo já tem `load_weekday_template_data`, `save_weekday_template`, `load_sunday_rotation`, `save_sunday_rotation`.
- **Mosaico:** Matriz colaborador × dia (SEG–SAB) → turno. Ex.: Cleonice trabalha SEG no CAI1.
- **Rodízio:** Lista de regras: domingo X, colaborador Y, folga compensatória em data Z.
- **ConfiguracaoPage:** Todas as tabs devem ter conteúdo funcional — turnos, mosaico, rodízio, exceções, demand.
- **T22 Perfil:** Foto (upload local), nome (texto), tema (light/dark ou variante). Persistir em localStorage ou arquivo; sem API de auth.
- **Didático:** Labels claros, tooltips se necessário, fluxo óbvio para novo usuário.
- **Cursor:** Execução via agentes; Use `/vibe` ou agentes para executar tarefas.
