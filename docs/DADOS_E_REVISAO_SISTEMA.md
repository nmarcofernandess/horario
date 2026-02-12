# Interpretação dos Dados e Revisão do Sistema

> Documento de apoio ao BUILD. Interpreta os fixtures/processados como "dados jogados no Excel" e revisa coerência do sistema.
> Data: 2026-02-12

---

## 1. O que são os fixtures (dados “jogados”)

Os arquivos em `data/fixtures/` vieram de planilhas/PDFs que o usuário estava montando manualmente para controlar a escala de caixa. Não são dados estruturados de sistema — são **extrações manuais** que precisam ser interpretadas.

### 1.1 `pdf_rita1_slots.csv` — Mosaico semanal (turnos seg–sáb)

| Coluna | Significado |
|--------|-------------|
| `day_name` | Dia da semana (SEG, TER, QUA, QUI, SEX, SAB) |
| `employee` / `employee_norm` | Colaborador (nome cru / normalizado) |
| `time_slot` | Faixa de 30 min (08:00, 08:30, …) — indica presença no caixa |
| `shift_code` | Código do turno (CAI1, CAI2, …) |
| `day_total_hms` | Total de horas do dia em formato H:MM:SS |

**O que representa:** A matriz “quem trabalha em qual dia da semana em qual turno”. Ex.: SEG + CLEONICE + CAI1 = Cleonice trabalha segunda no turno CAI1. O `day_total_hms` é redundante (deriva do turno) mas ajuda a checar inconsistências.

**Inconsistência:** O `shift_catalog_by_day` tem minutos por turno/dia variando (ex.: CAI1 em SEG=570 min, em TER=360 min). O `slots` usa `day_total_hms` por linha. O sistema hoje usa `shift_catalog` da policy para minutos, não o `day_total_hms` do slots. Isso pode divergir.

---

### 1.2 `pdf_rita1_shift_catalog_by_day.csv` — Catálogo de turnos por dia

| Coluna | Significado |
|--------|-------------|
| `day_name` | Dia da semana |
| `shift_code` | CAI1–CAI6 |
| `minutes_median` | Duração média do turno naquele dia (min) |
| `hours_median` | Idem em horas (redundante) |

**O que representa:** Duração de cada turno por dia. Ex.: CAI1 em SEG = 9h30 (570 min), em TER = 6h (360 min). O turno muda de carga conforme o dia.

**Problema:** A policy `compliance_policy.example.json` usa **um único valor fixo** por turno (ex.: CAI1=570). O `engines.py` ignora o catálogo por dia e usa só o da policy. O dado real do Excel está ignorado.

---

### 1.3 `pdf_rita_sunday_rotation.csv` — Rodízio de domingos + folga compensatória

| Coluna | Significado |
|--------|-------------|
| `source` | pdf (origem) |
| `table_index` | “Tabela” do PDF (1, 2, 3 = ciclos diferentes) |
| `scale_index` | Posição no ciclo (1–8) — identifica o domingo no ciclo |
| `sunday_raw` / `sunday_date` | Data do domingo trabalhado |
| `employee_raw` / `employee_norm` | Quem trabalha |
| `folga_raw` / `folga_date` | Data da folga compensatória (ex.: 2 dias após o domingo) |

**O que representa:** Regra “quem trabalha em qual domingo e quando folga” e “em qual ciclo isso está”. A estrutura tem 4 ciclos (8 posições cada) — 4 grupos de domingos rodando em paralelo.

**Semântica:** `scale_index` 1–8 dentro de um `table_index` = posições na sequência do ciclo. O domingo trabalhado é seguido de folga compensatória em dias úteis (ex.: dom 08/fev → folga 2 dias depois).

---

## 2. O que são os processados (saída do motor)

A pasta `data/processed/real_scale_cycle/` é gerada em runtime ao clicar em “Atualizar escala”.

### 2.1 `final_assignments.csv`

| Coluna | Significado |
|--------|-------------|
| `work_date` | Data do calendário |
| `employee_id` | Colaborador |
| `status` | WORK / FOLGA |
| `shift_code` | Turno (ex.: CAI1, DOM_08_12_30) |
| `minutes` | Carga do dia |
| `source_rule` | Origem: TEMPLATE_BASE, ROTATION_SUNDAY, ROTATION_COMPENSATION |

**O que representa:** A escala final dia a dia: quem trabalha, em qual turno, quantos minutos. É o output principal do sistema.

---

### 2.2 `violations.csv`

| Coluna | Significado |
|--------|-------------|
| `employee_id` | Colaborador |
| `rule_code` | R1_MAX_CONSECUTIVE, R4_WEEKLY_TARGET, etc. |
| `severity` | CRITICAL, HIGH, MEDIUM, LOW |
| `date_start` / `date_end` | Período da violação |
| `detail` | Texto explicativo |

**Regras detectadas hoje:**
- **R1_MAX_CONSECUTIVE:** Mais de 6 dias seguidos trabalhados (CLT).
- **R4_WEEKLY_TARGET:** Desvio da meta semanal (2640 min para 44h) — ex.: domingo curto + folga compensatória desalinhada.

---

### 2.3 `preference_decisions.csv`

Vazio — pedidos de preferência ainda não estão integrados ao fluxo.

---

## 3. O que é o schema (policy)

| Arquivo | Papel |
|---------|-------|
| `compliance_policy.schema.json` | Regras de validação JSON |
| `compliance_policy.example.json` | Política de exemplo para Caixa |

A policy define: contratos (44h/36h/30h), turnos, regras de domingo, folga compensatória, constraints (max 6 dias seguidos, meta semanal).

**Problema:** A policy usa siglas como `CLE`, `ANJ`, `GAB` — o banco usa `CLEONICE`, `ANA JULIA`, `GABRIEL`. O mapeamento entre policy e banco não está formalizado.

---

## 4. Fluxo completo (resumo)

```
fixtures (Excel/PDF) → seed.py → DB (employees, sectors, contracts, shifts, template, rotation)
                                           ↓
Policy (JSON) → PolicyLoader
                                           ↓
                    ValidationOrchestrator.run(context)
                                           ↓
          CycleGenerator: template + rotation → scale_cycle
          project_cycle_to_period() → final_assignments
          PolicyEngine: validate_consecutive_days, validate_weekly_hours → violations
                                           ↓
                    CSV em data/processed/real_scale_cycle/
```

---

## 5. Gaps e inconsistências

| # | Problema | Impacto |
|---|----------|---------|
| 1 | `shift_catalog_by_day` tem minutos variáveis por dia; a policy usa fixo | O motor não usa a variação real do Excel |
| 2 | Policy usa siglas (CLE, ANJ); DB usa nomes completos (CLEONICE, ANA JULIA) | Sem mapeamento explícito; pode quebrar validação por contrato |
| 3 | `table_index` 1–3 no sunday_rotation não tem semântica clara no engine | Ciclo pode ser mal interpretado |
| 4 | `preference_decisions.csv` vazio; pedidos não aplicados | Fluxo de preferência incompleto |
| 5 | `day_total_hms` no slots vs policy/engines | Possível divergência de carga |
| 6 | Semana de apuração: MON_SUN vs SUN_SAT | Documento alerta; não definido na operação |
| 7 | Marcadores 5/6 citados no BUILD | Semântica não definida |

---

## 6. O que está coerente

- Mosaico (slots) → template base → ciclo de escala.
- Rodízio de domingos → domingo trabalhado + folga compensatória.
- Regras R1 (consecutivos) e R4 (meta semanal) funcionando.
- UI com Colaboradores, Pedidos, Configuração e escala principal.
- Exportação em CSV para auditoria.

---

## 7. Recomendações

1. **Documentar no schema:** Mapeamento employee_id (DB) ↔ sigla (policy) ou padronizar um.
2. **Usar ou não:** Decidir se `shift_catalog_by_day` entra no engine (minutos por dia) ou se a policy fixa continua.
3. **Preferências:** Reintegrar fluxo de pedidos (preferences) → preference_decisions.
4. **Semana oficial:** Definir MON_SUN ou SUN_SAT para RH e compliance.
5. **Marcadores 5/6:** Esclarecer no BUILD e refletir no schema.

---

## 8. Resumo executivo

O sistema é um **motor de validação de escala de caixa** que:
- Lê mosaico (seg–sáb) e rodízio de domingos de fixtures “Excel/PDF”.
- Projeta para um período e gera `final_assignments`.
- Valida contra regras (consecutivos, meta semanal) e gera `violations`.
- A UI permite cadastrar colaboradores, setores e pedidos; a escala principal mostra o resultado.

Os dados estão “jogados” no sentido de origem manual e nomes variados; o fluxo principal funciona. O que falta é alinhar policy ↔ DB, tratar preferências e usar (ou descartar) a variação de turnos por dia do `shift_catalog_by_day`.
