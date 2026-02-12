# Sistema EscalaFlow — Como Funciona

> Documento unificado: fluxo do usuário, dados, arquitetura e setup.
> Substitui: FLUXO_USUARIO, DADOS_E_REVISAO, resumo BUILD.

---

## 1. Visão geral

O EscalaFlow é um app de gestão de escalas de trabalho (turnos, domingos, compliance).  
**Piloto atual:** setor Caixa.

**Stack:** Electron + React + API FastAPI (Python) + SQLite

---

## 2. Setup e execução

### Dependências

```bash
# Python
cd horario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Electron
cd apps/frontend
npm install
```

### Seed (primeira vez)

```bash
PYTHONPATH=. python scripts/seed.py
```

Popula o banco com colaboradores, turnos, mosaico semanal e rodízio de domingos a partir de `data/fixtures/`.

### Rodar o app

**Terminal 1 — API:**
```bash
cd apps/frontend
npm run api
```

**Terminal 2 — Electron:**
```bash
cd apps/frontend
npm run electron
```

**Alternativa web:** `npm run online` (API + frontend no browser)

---

## 3. Fluxo do usuário (RH / gestor)

### Página inicial — Escala de Trabalho

1. Definir período (De / Até)
2. O app executa **preflight** (impossível lógico x risco legal)
3. Se houver `LOGIC_HARD`, bloqueia com ação recomendada
4. Se houver `LEGAL_SOFT`:
   - modo `NORMAL`: alerta e permite seguir
   - modo `ESTRITO`: exige justificativa (ACK) para continuar
5. Clicar em **Gerar escala** ou **Simular período**
6. Ver resultado: tabela (Data, Colaborador, Status, Turno, Carga)
7. Ver alertas (violações) em expander
8. Exportar: HTML ou Markdown para imprimir/colar na parede

### Colaboradores

- Cadastrar: Código, Nome, Contrato, Setor  
- Editar, reordenar prioridade (picking de pedidos)

### Pedidos

- Novo: colaborador escolhe data, tipo (Folga, Troca de turno, Evitar domingo)
- Pendentes (RH): aprovar ou rejeitar, ordenados por prioridade
- Histórico

### Configuração

- Turnos: códigos e duração
- Mosaico semanal: quem trabalha em qual dia (seg–sáb)
- Rodízio de domingos: quem trabalha em cada domingo e quando folga
- Exceções: férias, atestado, bloqueios
- Demand (cobertura): mínimo de pessoas por faixa
- Simular: testar período sem atualizar a escala principal
- Governança E4:
  - definir semântica dos marcadores `5/6`
  - registrar CCT vigente
  - alternar modo runtime `NORMAL/ESTRITO`
  - consultar trilha de auditoria de ACK de risco legal

---

## 4. Dados e fixtures

### Fixtures (entrada para seed)

| Arquivo | Conteúdo |
|---------|----------|
| `seed_supermercado_fernandes.json` | Preset canônico (setor, contratos, colaboradores, turnos, mosaico, rodízio, governança E4) |

- **Origem:** consolidação das regras operacionais/jurídicas e necessidades do piloto.
- **Uso:** `scripts/seed.py` → carregamento JSON único → SQLite + patch de política (`compliance_policy.example.json`)

### Processados (saída do motor)

Gerados em `data/processed/real_scale_cycle/` ao clicar em "Gerar escala":

| Arquivo | Conteúdo |
|---------|----------|
| `final_assignments.csv` | Escala final: data, colaborador, status, turno, minutos |
| `violations.csv` | Alertas de regras (consecutivos, meta semanal, etc.) |
| `escala_calendario.html` / `.md` | Export para impressão |

### Política de compliance

- `schemas/compliance_policy.example.json` — política ativa (regras, picking, vigência)
- `schemas/compliance_policy.schema.json` — schema JSON para validação

---

## 5. Arquitetura resumida

### Componentes

```
Electron/React UI
    ↓
Validation Orchestrator (use_cases.py)
    ↓
Policy Engine, CycleGenerator, Suggestion Engine
    ↓
Repositories (DB), Policy Loader
```

### Fluxo principal

1. UI chama API → `POST /scale/generate`
2. Orchestrator carrega: turnos, mosaico, rodízio, exceções, pedidos
3. CycleGenerator gera escala com template + rodízio domingos
4. Policy Engine valida (hard/soft constraints)
5. Saída: assignments + violations + export HTML/MD

### Regras principais

| Código | Descrição |
|--------|-----------|
| R1_MAX_CONSECUTIVE | Dias consecutivos (máx. 6) |
| R2_MIN_INTERSHIFT_REST | Intervalo entre jornadas (mín. 11h) |
| R4_WEEKLY_TARGET | Meta semanal de horas |
| R5_DEMAND_COVERAGE | Cobertura insuficiente |

---

## 6. Scripts e schemas

### scripts/

| Script | Uso |
|--------|-----|
| `seed.py` | Seed principal — popula banco a partir de `data/fixtures/seed_supermercado_fernandes.json` |

### schemas/

| Arquivo | Uso |
|---------|-----|
| `compliance_policy.example.json` | Política ativa (regras, picking, vigência) — usado pela API |
| `compliance_policy.schema.json` | Schema JSON para validação da política |

---

## 7. Estrutura do projeto

```
horario/
├── apps/
│   ├── backend/            # API FastAPI + src/ (domain, application, infrastructure)
│   └── frontend/           # Electron + React
├── schemas/                # compliance_policy.example.json
├── data/
│   ├── fixtures/           # Seed canônico em JSON
│   └── processed/          # Output (gerado em runtime)
├── scripts/
│   └── seed.py             # Popular banco
└── docs/
```

---

## 8. Termos técnicos → usuário

| Técnico | Usuário |
|---------|---------|
| employee_id | Colaborador (nome) |
| WORK / FOLGA | Trabalho / Folga |
| ABSENCE | Ausência |
| CAI1, CAI2... | Turnos (ex.: Manhã 9h30) |
| CRITICAL / HIGH | Crítico / Alto |

---

## 9. Docs relacionados

| Doc | Conteúdo |
|-----|----------|
| `BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md` | Arquitetura completa do motor (PlantUML, ER, fluxos) |
| `WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md` | Backlog mestre, dashboard de guerra |
| `POLITICA_DOCUMENTACAO.md` | Política de atualização de docs e checklist |
| `legacy/REDPILL_LEIS_LOGICA_HUMANA_ESCALA.md` | Leis de alocação (pirâmide de prioridade) |

---

## 10. Status atual: o sistema fecha?

**Resposta curta:** O sistema **quase fecha para operação do Caixa**, com robustez técnica já elevada; resta fechamento externo/jurídico para produção final.

### O que fecha hoje

| Área | Status |
|------|--------|
| Gerar escala (período + setor) | ✅ |
| Ver escala em calendário e tabela | ✅ |
| Exportar HTML/MD | ✅ |
| Colaboradores CRUD | ✅ |
| Setores CRUD | ✅ |
| Pedidos (criar, aprovar/rejeitar) | ✅ |
| Turnos CRUD | ✅ |
| Exceções CRUD | ✅ |
| Demand CRUD | ✅ |
| Mosaico CRUD explícito (limpar linha/grade + salvar) | ✅ |
| Rodízio CRUD explícito (editar/remover + salvar) | ✅ |
| Simulação sem sobrescrever escala oficial | ✅ |
| Labels de violação harmonizadas (R1..R6) | ✅ |
| Tradução de status (WORK/FOLGA/ABSENCE) na Escala | ✅ |
| Células coloridas (calendário e tabela) | ✅ |
| Indicador API + retry | ✅ |
| Paginação + clamp | ✅ |
| Perfil (nome, foto, tema) | ✅ |
| Isolamento por sector_id (mosaico/rodízio) | ✅ |

### Lacunas pendentes (fechamento final)

| Área | Lacuna |
|------|--------|
| Visão semanal | Definir corte oficial para operação (MON_SUN vs SUN_SAT), já disponível em comparativo |
| Decisões externas | Fechar semântica dos marcadores 5/6 e validação jurídica domingo/feriado (já existe aba de Governança E4 para registrar e auditar) |

> Observação operacional (atual): o preflight separa bloqueio lógico e risco legal.
> - `LOGIC_HARD`: bloqueia sempre (`422`)
> - `LEGAL_SOFT`: em `NORMAL` alerta; em `ESTRITO` exige ACK com motivo (`409` sem ACK)
> - ACK válido registra auditoria e permite execução.

### Critério de "fechado"

O sistema fecha quando: o RH configura tudo pela UI (incluindo mosaico, rodízio, exceções, demand), gera e simula a escala, exporta, aprova pedidos — **sem depender de seed ou scripts manuais**, com regras contratuais/semanais formalizadas, E4 sem pendências no checklist de governança e regressão automatizada mínima. Ver `docs/POLITICA_DOCUMENTACAO.md` seção 7.
