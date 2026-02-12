# scale.py — Geração de Escala

Rota principal que orquestra a geração da escala de trabalho. Contém a lógica mais pesada da API.

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | /scale/generate | Gera escala para período (period_start, period_end, sector_id) |
| GET | /scale/assignments | Lista alocações da última geração |
| GET | /scale/violations | Lista violações da última geração |
| GET | /scale/export/html | Retorna HTML do calendário |
| GET | /scale/export/markdown | Retorna Markdown do calendário |
| GET | /scale/export/html/download | Download do HTML |
| GET | /scale/export/markdown/download | Download do Markdown |

## Fluxo de geração (POST /generate)

1. **PolicyLoader** carrega `schemas/compliance_policy.example.json` (turnos, regras)
2. **Repositório** carrega mosaico (weekday_template) e rodízio (sunday_rotation)
3. **Fallback CSV** — se DB vazio, usa `data/fixtures/` via LegacyCSVImporter
4. **CycleGenerator.build_weekday_template** — converte mosaico em template (employee_id × day_key → shift_code, minutes)
5. **CycleGenerator.build_scale_cycle** — combina template + rodízio em ciclo completo
6. **CycleGenerator.project_cycle_to_period** — projeta ciclo para período (period_start → period_end) usando anchor_date
7. **Pedidos aprovados** — aplica FOLGA_ON_DATE, SHIFT_CHANGE_ON_DATE, AVOID_SUNDAY_DATE
8. **Exceções** — aplica férias, atestado, etc.
9. **PolicyEngine** — valida R1 (consecutivos máx 6), R4 (meta semanal), etc.
10. **Export** — salva `final_assignments.csv`, `violations.csv`, `escala_calendario.html`, `escala_calendario.md` em `data/processed/real_scale_cycle/`

## Dependências

- **ValidationOrchestrator** (`apps/backend/src/application/use_cases.py`) — orquestra todo o pipeline
- **CycleGenerator** (`apps/backend/src/domain/engines.py`) — template, ciclo, projeção
- **PolicyEngine** (`apps/backend/src/domain/engines.py`) — validação de regras
- **PolicyLoader** (`apps/backend/src/domain/policy_loader.py`) — carrega policy JSON
- **SqlAlchemyRepository** — mosaico, rodízio, pedidos, exceções, colaboradores

## Output

- **ROOT** = projeto (horario/)
- **OUTPUT** = `data/processed/real_scale_cycle/`
- **POLICY_PATH** = `schemas/compliance_policy.example.json`
- **DATA_DIR** = `data/fixtures/` (fallback quando DB vazio)

## Códigos de violação (rule_labels)

| Código | Label |
|--------|-------|
| R1_MAX_CONSECUTIVE | Dias consecutivos (máx. 6) |
| R2_MIN_INTERSHIFT_REST | Intervalo entre jornadas (mín. 11h) |
| R4_WEEKLY_TARGET | Meta semanal de horas |
| R5_DEMAND_COVERAGE | Cobertura insuficiente |

## Erros

- **ValueError** → 400: "Não há dados suficientes... Execute o seed ou configure Mosaico e Rodízio"
- **404** nas rotas de export: "Escala não gerada. Execute POST /scale/generate primeiro."

## Onde procurar

- Lógica de projeção: `apps/backend/src/domain/engines.py` (CycleGenerator, PolicyEngine)
- Use case: `apps/backend/src/application/use_cases.py` (ValidationOrchestrator)
- Export: `apps/backend/src/infrastructure/presenters/export_calendar.py`
