# weekday_template.py — Mosaico Semanal (Template)

Define **quem trabalha em qual dia da semana** e **em qual turno** (segunda a sábado).

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /weekday-template | Lista template (employee_id, day_key, shift_code, minutes) |
| POST | /weekday-template | Salva lista completa (substitui para o setor) |

## Semântica dos campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| employee_id | str | Colaborador (nome canônico: CLEONICE, ANA JULIA) |
| day_key | str | Dia da semana: MON, TUE, WED, THU, FRI, SAT (ou day_name: SEG, TER, QUA, QUI, SEX, SAB) |
| shift_code | str | Turno (CAI1, CAI2, CAI3, etc.) |
| minutes | int | Carga do dia em minutos |

## Regra de negócio

- **Mosaico** = matriz colaborador × dia → turno
- Ex.: CLEONICE + SEG + CAI1 = Cleonice trabalha segunda no turno CAI1
- **Domingo** não entra no mosaico; domingos vêm do rodízio (sunday_rotation)
- `day_name` (português) é normalizado para `day_key` (inglês) no CycleGenerator

## Uso no pipeline

- `repo.load_weekday_template_data()` — carregado pelo ValidationOrchestrator
- `CycleGenerator.build_weekday_template(mosaic_df, shifts)` — converte para template com minutos da policy
- `CycleGenerator.build_scale_cycle(..., weekday_template, ...)` — combina com rodízio

## Validação POST

- Aceita `day_name` ou `day_key` (prioriza day_name se existir)
- `minutes` opcional (default 0)
- Lista vazia → retorna `{ok: true, count: 0}`

## Dependências

- **SqlAlchemyRepository.save_weekday_template(df, sector_id)** — persiste no banco
- **LegacyCSVImporter.load_base_slots()** — fallback de `data/fixtures/pdf_rita1_slots.csv`

## Fixture de referência

- `data/fixtures/pdf_rita1_slots.csv` — slots por dia (day_name, employee, shift_code, time_slot)
- O seed normaliza para (employee_id, day_key, shift_code) via `cycle_templates`
