# sunday_rotation.py — Rodízio de Domingos

Define **quem trabalha em qual domingo** e **quando folga** (folga compensatória).

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /sunday-rotation | Lista rodízio (scale_index, employee_id, sunday_date, folga_date) |
| POST | /sunday-rotation | Salva lista completa (substitui) |

## Semântica dos campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| scale_index | int | Posição no ciclo (1–8). Identifica a "vaga" no rodízio |
| employee_id | str | Colaborador (nome canônico: CLEONICE, ANA JULIA) |
| sunday_date | str | Data do domingo trabalhado (YYYY-MM-DD) |
| folga_date | str | Data da folga compensatória (ex.: 2 dias após o domingo) |

## Regra de negócio

- **Domingo trabalhado** → colaborador deve ter **folga compensatória** em dia útil (ex.: dom 08/fev → folga 10/fev)
- **scale_index** alinha o ciclo ao calendário: o anchor_date do rodízio é usado pelo CycleGenerator para projetar o período
- Um mesmo scale_index pode ter vários colaboradores em ciclos diferentes (table_index no CSV original)

## Uso no pipeline

- `repo.load_sunday_rotation()` — carregado pelo ValidationOrchestrator
- `CycleGenerator.build_scale_cycle(sunday_rotation_df, ...)` — combina com weekday_template
- `anchor_date` = min(sunday_date) do rodízio — alinha projeção ao calendário

## Validação POST

- Obrigatório: `scale_index`, `employee_id`, `sunday_date`
- `folga_date` opcional (pode ser null)
- Lista vazia → retorna `{ok: true, count: 0}`

## Dependências

- **SqlAlchemyRepository.save_sunday_rotation(df)** — persiste no banco
- **LegacyCSVImporter.load_sunday_rotation()** — fallback de `data/fixtures/pdf_rita_sunday_rotation.csv`
