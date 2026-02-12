# EscalaFlow - Compliance Engine

Sistema de validação de compliance para escalas de trabalho (turnos, domingos, folgas compensatórias).

---

## Como rodar

### Primeira vez (setup)

```bash
cd horario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/seed.py
cd apps/frontend && npm install
```

### Rodar o app (Electron desktop)

Abra **dois terminais**. Em cada um, rode os comandos (copie e cole tudo de uma vez):

**Terminal 1 — API:**
```bash
cd apps/frontend
source ../../.venv/bin/activate
npm run api
```

**Terminal 2 — Electron:**
```bash
cd apps/frontend
npm run electron
```

> ⚠️ **Pré-requisito:** você precisa estar na pasta `horario` (a raiz do projeto). Se não estiver, rode antes: `cd horario` ou `cd /caminho/para/horario`.

### Rodar no navegador (web)

```bash
cd apps/frontend
source ../../.venv/bin/activate
npm run online
```

Sube API (8000) + frontend (5173). Abra http://localhost:5173

---

## Estrutura

```
horario/
├── apps/
│   ├── backend/            # API FastAPI + core
│   └── frontend/           # Electron + React (desktop)
├── data/fixtures/          # Seed canônico em JSON
├── scripts/seed.py         # Popular banco
├── tests/                  # Testes pytest
└── docs/
```

## Scripts (apps/frontend)

| Comando | Descrição |
|---------|-----------|
| `npm run electron` | App Electron (desktop) |
| `npm run api` | API Python (porta 8000) |
| `npm run online` | API + frontend web juntos |

## Gerar instalador (Mac e Windows)

Rode **no sistema onde quer gerar** (Mac para .app/.zip, Windows para .exe):

```bash
cd horario/apps/frontend
npm run make
```

**Saída em** `apps/frontend/out/make/`:
- **Mac:** `.zip` (descompacte e arraste o app para Aplicativos)
- **Windows:** `.exe` (instalador Squirrel)

> **Importante:** O app precisa da API Python rodando. Para distribuir, inclua instruções para o usuário rodar `npm run api` (ou um wrapper que inicie a API automaticamente) antes de usar o app.

## Testes

```bash
cd horario
PYTHONPATH=. pytest
```

## Docs

- `docs/SISTEMA_ESCALAFLOW.md` — fluxo, dados, setup
- `docs/BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md` — arquitetura do motor
- `docs/WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md` — warlog e status
