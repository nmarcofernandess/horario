# Análise: Referência Auto-Claude para Melhorias no EscalaFlow

> Comparação estrutural entre o Auto-Claude (AndyMik90/Auto-Claude) e o EscalaFlow.
> Repo referência: `/Users/marcofernandes/commandflow/auto-claude`
> Data: 2026-02-12

---

## 1. Resumo executivo

O Auto-Claude é um framework de coding autônomo multi-agente (Electron + Python). Sua estrutura foi revisada para identificar práticas que o EscalaFlow pode adotar em **organização**, **documentação para IA**, **documentação para devs** e **qualidade de entrega**.

---

## 2. Estrutura comparada

### Auto-Claude (referência)

```
Auto-Claude/
├── apps/
│   ├── backend/           # Python (agents, specs, QA)
│   └── frontend/          # Electron (main, preload, renderer)
├── guides/                # CLI-USAGE, linux, README
├── tests/                 # Pytest (50+ arquivos)
├── scripts/               # bump-version, install-backend, test-backend
├── .github/
│   ├── ISSUE_TEMPLATE/    # bug_report, config, docs, question
│   ├── workflows/         # ci, lint, release, pre-release, virustotal
│   └── PULL_REQUEST_TEMPLATE.md
├── .husky/                # commit-msg, pre-commit
├── .pre-commit-config.yaml
├── README.md
├── CLAUDE.md              # Documento principal para IA
├── CONTRIBUTING.md
├── CHANGELOG.md
├── RELEASE.md
├── CLA.md
└── package.json           # workspaces: apps/*, libs/*
```

### EscalaFlow (atual)

```
horario/
├── api/                   # FastAPI (backend)
├── electron-app/          # Electron (main, preload, renderer)
├── src/                   # Core domain/application/infra
├── docs/
├── scripts/
├── .cursor/rules/
├── README.md
└── requirements.txt
```

---

## 3. Recomendações (priorizadas)

### 3.1 Documentação para IA (alta prioridade)

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **CLAUDE.md** | Arquivo dedicado para guiar IA: estrutura, comandos, onde procurar código | Só .cursor/rules | **Criar `CLAUDE.md`** na raiz com: visão geral, estrutura, comandos (setup, seed, run), onde procurar (api/, electron-app/, src/), convenções |
| **Where to look** | "Look in apps/backend/core/client.py", "Reference agents/" | Implícito | **Incluir seções "When working with X"** apontando para arquivos-chave |
| **Critical rules** | "CRITICAL: All AI interactions use SDK, NOT Anthropic API" | Nenhum | **Documentar regras críticas** (ex: nunca usar streamlit, sempre usar api/ para backend) |

**Exemplo de CLAUDE.md para EscalaFlow:**

```markdown
# CLAUDE.md — EscalaFlow

## Project Overview
Sistema de validação de compliance para escalas de trabalho (turnos, domingos, folgas).
Stack: Electron + React + FastAPI + SQLite.

## Project Structure
- api/ — FastAPI REST, routes/, schemas
- electron-app/ — Electron (main spawna API), React+Vite
- src/ — Core: domain, application, infrastructure

## When working with...
- **API/backend:** api/main.py, api/routes/, api/schemas.py
- **Frontend:** electron-app/src/renderer/pages/, lib/api.ts
- **Business logic:** src/domain/engines.py, src/application/use_cases.py
- **Database:** src/infrastructure/database/, src/infrastructure/repositories_db.py

## Commands
npm run api / npm run electron / npm run online
PYTHONPATH=. python scripts/seed.py
```

---

### 3.2 Documentação para devs

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **CONTRIBUTING.md** | 600+ linhas: setup, code style, PR process | — | **Não aplicável** — projeto sem colaboradores externos |
| **CHANGELOG.md** | Histórico versionado | — | **Não aplicável** |
| **guides/** | CLI-USAGE, linux, README | N/A | Criar `guides/` com docs específicos se fizer sentido |

---

### 3.3 Organização de código (média prioridade)

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **Monorepo workspaces** | `apps/backend` + `apps/frontend` | `api/` + `electron-app/` fora de apps/ | Opcional: mover para `apps/api` e `apps/electron-app` se quiser alinhar; hoje está ok |
| **Preload API modular** | `preload/api/modules/*.ts` (changelog, github, shell, etc.) | `preload/index.ts` único | **Modularizar preload** em `api/` + `modules/` se crescer |
| **Shared types** | `src/shared/` com i18n, types | `renderer/types.ts` | Considerar `src/shared/` para types e utils compartilhados |
| **E2E tests** | `e2e/` separado | Ausente | Adicionar `electron-app/e2e/` quando tiver testes E2E |

---

### 3.4 CI/CD e qualidade (média prioridade)

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **pre-commit** | ruff, ruff-format, eslint, typecheck, trailing-whitespace | Ausente | **Adicionar .pre-commit-config.yaml** com ruff (api/) e eslint (electron-app/) |
| **GitHub workflows** | ci, lint, release, quality-security | Ausente | **Criar .github/workflows/ci.yml** (lint + test) |
| **PULL_REQUEST_TEMPLATE** | Checklist base branch, type, area, CI | — | **Não aplicável** — sem colaboradores |
| **ISSUE_TEMPLATE** | bug_report, docs, question | — | Opcional (só se usar issues para tracking) |

---

### 3.5 Release e versionamento (baixa prioridade)

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **RELEASE.md** | Fluxo de release com diagrama | Ausente | Adicionar quando houver releases formais |
| **bump-version** | Script centralizado | Ausente | Idem |
| **CHANGELOG obrigatório** | Release falha sem entry | - | Manter CHANGELOG atualizado ao fazer releases |

---

### 3.6 Outros (baixa prioridade)

| Item | Auto-Claude | EscalaFlow | Ação sugerida |
|------|-------------|------------|---------------|
| **Husky** | commit-msg, pre-commit | Ausente | Adicionar com pre-commit quando configurar hooks |
| **Design system** | `.design-system/` (componentes) | shadcn inline | Manter shadcn; considerar extrair tokens/style se crescer |
| **i18n** | react-i18next, locales | Ausente | Adicionar só se houver necessidade de múltiplos idiomas |
| **E2E via MCP** | QA agents usam Electron MCP | N/A | Não aplicável ao EscalaFlow |

---

## 4. Checklist de implementação

**Contexto:** Projeto sem colaboradores externos — CONTRIBUTING, CHANGELOG, PULL_REQUEST_TEMPLATE não aplicáveis.

### Fase 1 — Documentação para IA

- [x] Criar regra `agent.mdc` em `.cursor/rules/` (CLAUDE.md equivalente)

### Fase 2 — Qualidade (opcional)

- [ ] Adicionar `.pre-commit-config.yaml` (ruff, eslint, trailing-whitespace)
- [ ] Criar `.github/workflows/ci.yml` (lint + test)

### Fase 3 — Organização (conforme necessidade)

- [ ] Modularizar preload em `api/` + `modules/` se crescer
- [ ] Criar `guides/` com docs específicos
- [ ] Considerar `src/shared/` para tipos compartilhados

---

## 5. O que NÃO copiar

- **CLA** — Só necessário se houver licensing específico
- **CONTRIBUTING, CHANGELOG, PULL_REQUEST_TEMPLATE** — Sem colaboradores externos; não aplicável
- **Graphiti/Memory** — Não aplicável ao EscalaFlow
- **Worktree/git flow complexo** — Fluxo simples basta
- **E2E via MCP** — Feature específica de agents autônomos
- **Versão em 3+ arquivos** — Manter versão em package.json/__init__.py até ter releases

---

## 6. Referências lidas

- `commandflow/auto-claude/README.md`
- `commandflow/auto-claude/CLAUDE.md`
- `commandflow/auto-claude/CONTRIBUTING.md`
- `commandflow/auto-claude/RELEASE.md`
- `commandflow/auto-claude/.pre-commit-config.yaml`
- `commandflow/auto-claude/.github/PULL_REQUEST_TEMPLATE.md`
- `commandflow/auto-claude/guides/CLI-USAGE.md`
- Estrutura `apps/backend`, `apps/frontend`
