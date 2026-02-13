# EscalaFlow

Sistema local/offline para gestão de escalas com motor de compliance, focado no piloto do setor `CAIXA` e preparado para evolução multi-setor por `sector_id`.

Este tutorial substitui o guia antigo e reflete o comportamento atual do código.

---

## 1) O que o sistema entrega hoje

- Geração oficial de escala por período com validação de compliance.
- Simulação de período sem sobrescrever a escala oficial.
- Preflight operacional antes de executar (bloqueio lógico vs risco legal).
- Gestão via UI de colaboradores, setores, turnos, mosaico, rodízio, exceções e demanda.
- Governança operacional (modo `NORMAL`/`ESTRITO`, semântica 5/6, CCT, trilha de auditoria).
- Export da escala em HTML e Markdown.

---

## 2) Arquitetura rápida (mapa atualizado)

### Stack

- Backend: FastAPI + SQLite + camada de domínio em Python.
- Frontend desktop: Electron + React + Vite + shadcn/ui.
- Persistência principal: `data/compliance_engine.db`.

### Fluxo principal

1. UI chama `POST /scale/preflight`.
2. Backend valida se dá para executar:
   - `LOGIC_HARD`: bloqueia (ex.: setor inexistente, sem colaboradores, sem turnos, mosaico vazio).
   - `LEGAL_SOFT`: alerta; em modo estrito exige ACK com justificativa.
3. UI chama `POST /scale/generate` (oficial) ou `POST /scale/simulate` (preview).
4. Orquestrador monta escala e aplica:
   - mosaico + rodízio,
   - pedidos aprovados,
   - exceções.
5. Motor roda regras R1..R6 e retorna violações.
6. Na geração oficial, salva:
   - `data/processed/real_scale_cycle/final_assignments.csv`
   - `data/processed/real_scale_cycle/violations.csv`
   - export `escala_calendario.html` e `escala_calendario.md`.

---

## 3) Regras de compliance ativas hoje

- `R1_MAX_CONSECUTIVE`: máximo de dias consecutivos.
- `R2_MIN_INTERSHIFT_REST`: intervalo mínimo entre jornadas.
- `R3_SUNDAY_ROTATION`: domingos consecutivos por regra contratual.
- `R4_WEEKLY_TARGET`: meta semanal por contrato.
- `R5_DEMAND_COVERAGE`: cobertura mínima por slot de demanda.
- `R6_MAX_DAILY_MINUTES`: limite diário de jornada.

---

## 4) Setup inicial (primeira vez)

Na raiz do projeto:

```bash
cd horario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend:

```bash
cd apps/frontend
npm install
```

Volte para a raiz e rode o seed canônico:

```bash
cd ../..
PYTHONPATH=. python scripts/seed.py
```

O seed usa `data/fixtures/seed_supermercado_fernandes.json` e popula banco + patch de governança na policy.

---

## 5) Executar o sistema

Abra 2 terminais.

### Terminal 1 - API

```bash
cd horario/apps/frontend
source ../../.venv/bin/activate
npm run api
```

### Terminal 2 - Electron (desktop)

```bash
cd horario/apps/frontend
npm run electron
```

Opcional (web):

```bash
cd horario/apps/frontend
source ../../.venv/bin/activate
npm run online
```

---

## 6) Tutorial operacional (passo a passo)

### Passo 1 - Ajuste configuração base

Na página `Configuração`:

- Cadastre/edite `Turnos`.
- Monte o `Mosaico` (SEG-SAB por colaborador).
- Ajuste `Rodízio` de domingos.
- Cadastre `Exceções` (férias, atestados etc.).
- Cadastre `Demanda por horário` (slots e mínimo de pessoas).

### Passo 2 - Defina governança (E4)

Ainda em `Configuração` > aba Governança:

- Revise semântica dos marcadores `5/6`.
- Informe identificador de CCT.
- Marque validação jurídica domingo/feriado quando concluída.
- Defina modo runtime:
  - `NORMAL`: alerta risco legal e permite seguir.
  - `ESTRITO`: exige justificativa (`risk_ack`) para continuar em risco legal.

### Passo 3 - Gere ou simule escala

Na página `Escala`:

1. Informe período (`De`/`Até`).
2. Clique em `Gerar escala` ou `Simular período`.
3. Se houver bloqueio lógico, ajuste a configuração antes de continuar.
4. Se houver risco legal em modo estrito, informe justificativa no modal de ACK.

### Passo 4 - Analise resultado

Na página `Escala`:

- Veja tabela/calendário de alocações.
- Acompanhe o resultado de compliance (contagem de violações e status da execução).
- Use bloco de aderência semanal para comparar:
  - `Segunda a Domingo` (`MON_SUN`)
  - `Domingo a Sábado` (`SUN_SAT`)

### Passo 5 - Exporte

- `Exportar para impressão` (HTML)
- `Exportar texto` (Markdown)

---

## 7) Páginas da UI (estado atual)

- `Escala`: preflight, gerar, simular, análise semanal, export.
- `Colaboradores`: cadastro de colaboradores e setores.
- `Pedidos`: criação e decisão (aprovar/rejeitar).
- `Configuração`: turnos, mosaico, rodízio, exceções, demanda e governança.
- `Perfil`: nome, organização e foto local (localStorage).

---

## 8) Comandos úteis

Dentro de `apps/frontend`:

- `npm run api` - sobe API FastAPI (`127.0.0.1:8000`).
- `npm run electron` - app desktop.
- `npm run online` - API + frontend web.
- `npm run build` - build Electron/Vite.
- `npm run make` - empacotamento.
- `npm run lint` - lint frontend.
- `npm run test` - testes frontend (Vitest).

Na raiz do projeto:

- `PYTHONPATH=. pytest` - testes backend.
- `PYTHONPATH=. python scripts/seed.py` - repopular base local.

---

## 9) Estrutura do projeto

```text
horario/
├── apps/
│   ├── backend/                  # FastAPI + domain/application/infrastructure
│   └── frontend/                 # Electron + React
├── data/
│   ├── fixtures/                 # Seed canônico JSON
│   └── processed/                # Saída gerada em runtime
├── schemas/
│   ├── compliance_policy.example.json
│   └── compliance_policy.schema.json
├── scripts/
│   └── seed.py
├── tests/
└── docs/
```

---

## 10) Principais endpoints (referência rápida)

- Escala: `/scale/preflight`, `/scale/generate`, `/scale/simulate`, `/scale/weekly-analysis`, `/scale/assignments`, `/scale/violations`.
- Config: `/config/governance`, `/config/governance/apply-defaults`, `/config/runtime-mode`, `/config/governance/audit`.
- Cadastros: `/employees`, `/sectors`, `/preferences`, `/shifts`, `/exceptions`, `/demand-profile`, `/weekday-template`, `/sunday-rotation`.

---

## 11) Troubleshooting rápido

- **Erro ao gerar**: rode preflight na própria UI e corrija o primeiro blocker.
- **Escala vazia**: confirme seed + mosaico + rodízio.
- **Risco legal travando em estrito**: informe justificativa no ACK ou ajuste modo/runtime e governança.
- **API fora**: valide `http://127.0.0.1:8000/health`.
- **Dados inconsistentes após testes**: rode seed novamente.

---

## 12) Documentação oficial do projeto

- `docs/SISTEMA_ESCALAFLOW.md` - visão unificada de operação.
- `docs/BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md` - arquitetura detalhada.
- `docs/WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md` - warlog e evolução contínua.
