# Escala Caixa - Compliance Engine

Sistema de validação de compliance para escalas de caixa (turnos, domingos, folgas compensatórias).

## Estrutura

- `app.py`: app principal Streamlit — Validação de Compliance
- `pages/`: Gestão de Cadastros, Pedidos, Regras de Negócio
- `data/raw/`: arquivos originais (XLSX/PDF)
- `data/processed/`: CSV/JSON e saídas da validação
- `scripts/extract_scale_data.py`: extração e normalização dos dados brutos
- `scripts/seed_db_from_csv.py`: população do banco a partir dos CSVs processados
- `docs/`: documentação da arquitetura e regras

## Setup rápido

```bash
cd /Users/marcofernandes/horario
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Primeira execução

**1. Popular o banco** (obrigatório na primeira vez):

```bash
source .venv/bin/activate
PYTHONPATH=. python scripts/seed_db_from_csv.py
```

**2. Abrir o app:**

```bash
PYTHONPATH=. streamlit run app.py
```

Acesse http://localhost:8501 e clique em **Rodar Validação**.

## Gerar dados manipuláveis (extração de PDF/XLSX)

```bash
python scripts/extract_scale_data.py --year 2026
```

Saídas em `data/processed/`: `pdf_rita1_slots.csv`, `pdf_rita_sunday_rotation.csv`, etc.

