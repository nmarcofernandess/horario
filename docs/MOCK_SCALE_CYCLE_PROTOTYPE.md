# Mock Prototype - Scale-Cycle First

## Objetivo
Provar, com logica Python e mocks, que os dados "bons" ja extraidos conseguem ser transformados no modelo:
- base estrutural por escala (`scale_id + employee_id + cycle_day`);
- projecao por dia (`employee_id + work_date`);
- semana somente como visao (`MON_SUN` ou `SUN_SAT`).
- pedido do colaborador com decisao RH (aceita/rejeita) sem quebrar compliance.

## Script
- `/Users/marcofernandes/horario/scripts/mock_scale_cycle_pipeline.py`

## Entradas usadas
- `/Users/marcofernandes/horario/data/processed/xlsx_caixas_sunday_rotation.csv`
- `/Users/marcofernandes/horario/data/processed/pdf_rita1_totals.csv`
- `/Users/marcofernandes/horario/schemas/compliance_policy.example.json`

## Como rodar
```bash
cd /Users/marcofernandes/horario
source .venv/bin/activate
python scripts/mock_scale_cycle_pipeline.py --period-start 2026-02-08 --period-end 2026-03-31
```

## Saidas geradas
Diretorio:
- `/Users/marcofernandes/horario/data/processed/mock_scale_cycle/`

Arquivos principais:
- `scale_cycle_template.mock.csv`
- `day_assignments.mock.csv`
- `employee_preferences.mock.csv`
- `preference_decisions.mock.csv`
- `weekly_summary_mon_sun.mock.csv`
- `weekly_summary_sun_sat.mock.csv`
- `violations.mock.csv`
- `run_summary.mock.json`

## Resultado principal do experimento
- Ciclo mock gerado com `8` escalas e `56` dias de ciclo.
- Projecao diaria criada para o periodo.
- Pedidos de preferencia mock foram avaliados e classificados em `APPROVED`/`REJECTED`.
- No mock, `SUN_SAT` fecha contrato semanal (delta 0 em todas as semanas completas).
- No mock, `MON_SUN` mostra deltas (efeito de domingo + compensacao cruzando corte).

Isso confirma, em ambiente de prototipo, a tese operacional:
**escala fixa roda no dia; semana e apenas filtro/visao.**
