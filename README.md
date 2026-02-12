# EscalaFlow - Compliance Engine

Sistema de validação de compliance para escalas de trabalho (turnos, domingos, folgas compensatórias).

## Estrutura

- `app.py`: app principal Streamlit
- `pages/`: Gestão de Cadastros, Pedidos, Regras de Negócio
- `data/fixtures/`: CSVs mínimos para seed (slots, rotação domingo, catálogo turnos)
- `scripts/seed.py`: população do banco
- `docs/BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md`: arquitetura

## Setup rápido

```bash
cd horario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Primeira execução

**1. Popular o banco:**

```bash
PYTHONPATH=. python scripts/seed.py
```

**2. Abrir o app:**

```bash
PYTHONPATH=. streamlit run app.py
```

Acesse http://localhost:8501 e clique em **Rodar Validação**.
