# Auditoria — Pré-migração para Next.js

> Double-check do sistema antes de construir o frontend em Next.js.
> Data: 2026-02-12

---

## 1. Modelo de dados (para API Next.js)

### 1.1 Entidades principais

| Entidade | PK | Campos principais | Observação |
|----------|-----|-------------------|------------|
| **employees** | employee_id | name, contract_code, sector_id, rank, active | employee_id = nome canônico (ex: CLEONICE, ANA JULIA) |
| **sectors** | sector_id | name, active | |
| **contracts** | contract_code | sector_id, weekly_minutes, sunday_mode | H44_CAIXA=2640min, H36_CAIXA=2160min, H30_CAIXA=1800min |
| **preferences** | request_id | employee_id, request_date, request_type, priority, decision, note | decision: PENDING, APPROVED, REJECTED |
| **shifts** | shift_code | sector_id, minutes, day_scope | CAI1-CAI6, DOM_08_12_30 |
| **cycle_templates** | id | employee_id, day_key, shift_code, minutes, source | source=TEMPLATE_BASE |
| **sunday_rotations** | id | scale_index, employee_id, sunday_date, folga_date | |

### 1.2 Identificadores

- **employee_id**: sempre canônico (CLEONICE, ANA JULIA, GABRIEL). Não usar siglas (CLE, ANJ) para chaves.
- **request_id**: UUID completo (implementado).
- **contratos**: H44_CAIXA, H36_CAIXA, H30_CAIXA, CLT_44H (todos 44h).

---

## 2. Fluxos verificados

### 2.1 Geração de escala

1. Carrega mosaico (cycle_templates) + rodízio (sunday_rotations).
2. Fallback para CSV quando DB vazio.
3. Projeta ciclo para período (period_start → period_end).
4. **anchor_date**: usa o primeiro domingo do rodízio para alinhar ciclo ao calendário; `period_start` pode ser qualquer dia.
5. Aplica pedidos aprovados (FOLGA_ON_DATE, SHIFT_CHANGE_ON_DATE, AVOID_SUNDAY_DATE).
6. Valida: consecutivos (máx 6) e meta semanal.
7. Exporta: final_assignments.csv, violations.csv, preference_decisions.csv.

### 2.2 Meta semanal (contract_targets)

- `load_contract_targets(sector_id)` retorna `{employee_id: weekly_minutes}`.
- Vem do `contract_code` do employee + `weekly_minutes` do contract.
- Fallback 2640 quando contrato não encontrado.

### 2.3 Preferências

- **Cadastro**: employee_id, request_date, request_type, priority, note. decision = PENDING.
- **Aplicação**: FOLGA_ON_DATE e AVOID_SUNDAY_DATE → folga na data; SHIFT_CHANGE_ON_DATE (com target_shift_code) → troca turno.

---

## 3. Pontos de atenção para Next.js

### 3.1 O que precisa de API

| Endpoint | Descrição |
|---------|-----------|
| GET /employees | Listar colaboradores (com nome para display) |
| POST /employees | Criar/atualizar (upsert) |
| PATCH /employees/:id/rank | Reordenar |
| GET /sectors | Listar setores |
| POST /sectors | Criar setor |
| GET /preferences | Listar pedidos |
| POST /preferences | Criar pedido |
| PATCH /preferences/:id/decision | Aprovar/rejeitar |
| POST /scale/generate | Gerar escala (period_start, period_end, sector_id) → retorna assignments + violations |
| GET /scale/assignments | Última escala gerada (ou por período) |
| GET /scale/violations | Violações da última geração |

### 3.2 Formato de resposta esperado

**Assignments** (escala):
```json
{
  "work_date": "2026-02-08",
  "employee_id": "CLEONICE",
  "employee_name": "Cleonice",
  "status": "WORK",
  "shift_code": "DOM_08_12_30",
  "minutes": 270,
  "source_rule": "ROTATION_SUNDAY"
}
```

**Violations**:
```json
{
  "employee_id": "ALICE",
  "employee_name": "Alice",
  "rule_code": "R1_MAX_CONSECUTIVE",
  "rule_label": "Dias consecutivos (máx. 6)",
  "severity": "CRITICAL",
  "date_start": "2026-02-16",
  "date_end": "2026-02-22",
  "detail": "Trabalhou 7 dias seguidos (Max: 6)"
}
```

### 3.3 Semana de apuração

- **MON_SUN**: segunda a domingo (policy.week_definition).
- `validate_weekly_hours` usa `week_start = work_date - weekday` (segunda = início da semana).

---

## 4. Bugs / limitações conhecidas

| # | Item | Status |
|---|------|--------|
| 1 | Projeção sem anchor_date | **RESOLVIDO** — anchor_date do rodízio alinha ciclo ao calendário |
| 2 | SHIFT_CHANGE e AVOID_SUNDAY não aplicados | **RESOLVIDO** — ambos aplicados no motor |
| 3 | request_id 8 chars | **RESOLVIDO** — UUID completo |
| 4 | Folga compensatória: delta 0-6 dias | Mantido — lógica no engine |
| 5 | Policy fixa (JSON) | Para Next.js: considerar policy por período |

---

## 5. Schemas para Next.js

### 5.1 Tipos sugeridos (TypeScript)

```typescript
type EmployeeId = string;  // CLEONICE, ANA JULIA, etc
type ContractCode = 'H44_CAIXA' | 'H36_CAIXA' | 'H30_CAIXA' | 'CLT_44H';
type RequestType = 'FOLGA_ON_DATE' | 'SHIFT_CHANGE_ON_DATE' | 'AVOID_SUNDAY_DATE';
type RequestDecision = 'PENDING' | 'APPROVED' | 'REJECTED';
type Status = 'WORK' | 'FOLGA' | 'ABSENCE';

interface Employee {
  employee_id: EmployeeId;
  name: string;
  contract_code: ContractCode;
  sector_id: string;
  rank: number;
  active: boolean;
}

interface Assignment {
  work_date: string;  // YYYY-MM-DD
  employee_id: EmployeeId;
  status: Status;
  shift_code: string;
  minutes: number;
  source_rule: string;
}
```

### 5.2 CSV exportados (contrato atual)

- **final_assignments.csv**: work_date, employee_id, status, shift_code, minutes, source_rule
- **violations.csv**: employee_id, rule_code, severity, date_start, date_end, detail
- **preference_decisions.csv**: request_id, applied (quando houver)

---

## 6. Checklist de consistência

- [x] Policy contracts.employees usa nomes completos (CLEONICE, ANA JULIA)
- [x] DB employees.employee_id = nomes canônicos
- [x] load_contract_targets usa contrato do DB
- [x] Preferências aprovadas (FOLGA_ON_DATE) aplicadas na escala
- [x] UI exibe nomes em vez de employee_id onde possível
- [x] Seed popula fixtures corretamente
- [x] anchor_date no ProjectionContext (implementado)
- [x] SHIFT_CHANGE e AVOID_SUNDAY aplicados no motor
- [x] request_id com UUID completo

---

## 7. Conclusão

O sistema está **completo e consistente** para uso como piloto. Para Next.js:

1. Expor os mesmos conceitos via API REST ou tRPC.
2. Manter employee_id como string canônica; nomes para display.
3. period_start pode ser qualquer dia (anchor_date alinha o ciclo).
4. request_id já usa UUID completo.
5. SHIFT_CHANGE e AVOID_SUNDAY aplicados no motor; pedido de troca requer target_shift_code.
