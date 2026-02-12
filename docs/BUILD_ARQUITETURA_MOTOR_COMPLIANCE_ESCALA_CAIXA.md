# ARQUITETURA: Motor de Compliance de Escalas (Core Multi-Setor, Piloto Caixa)

> Fonte única de arquitetura para o motor.
> Última revisão: 2026-02-12

---

## 0. Fonte de Verdade e Escopo

### 0.0 Prioridade de produto (contexto validação)
**Escala legível para o funcionário é o output principal.** Deve responder: em qual dia trabalha, em qual horário, qual domingo trabalha, qual dia de folga naquela semana. Sem esse output humano, o resto não resolve o problema.

### 0.1 Decisao oficial de escopo
- Este BUILD e a fonte unica de arquitetura para o motor.
- O **core do motor** e desenhado para operar por `sector_id` (multi-setor).
- O **piloto operacional atual** (dados reais, regras homologadas e UI) e **somente Caixa**.
- **Acougue e demais setores nao entram no MVP atual**; entram via onboarding de setor (policy + turnos + cobertura + excecoes).

### 0.2 Regra de leitura para evitar ambiguidade
- Quando o documento disser "Escala Caixa", ler como "instancia piloto atual".
- Quando o documento disser "Motor de Compliance", ler como "core reaproveitavel para qualquer setor".

### 0.3 Matriz de cobertura atual

| Escopo | Status hoje | Fonte |
|---|---|---|
| Core de validacao (hard/soft/semana/preferencia) | Implementado | `src/domain/engines.py`, `src/application/use_cases.py` |
| Dados e regras Caixa | Cobertos | `schemas/compliance_policy.example.json` + datasets extraidos |
| Acougue/outros setores | Nao onboarded | Sem policy/versionamento/demand profile dedicado |

## 1. Visao Geral

### 1.1 Escopo (Mind Map)
```plantuml
@startmindmap
* Motor de Compliance - Escalas por Setor
** Entrada
*** PDF turnos (seg-sab)
*** PDF rodizio domingo
*** XLSX DOM/FOLGAS
*** Cadastro de contratos (44/36/30h)
*** Preferencias do colaborador (pedido)
*** Politica legal versionada
** Core
*** Ingestao e parsing
*** Modelo canonico (scale_cycle -> employee+date)
*** Policy Engine
**** Hard constraints
**** Soft constraints
*** Suggestion Engine
*** RH Decision Gate (aprova/rejeita pedido)
*** Audit trail explicavel
** Saida
*** Escala diaria validada
*** Visao semanal MON_SUN
*** Visao semanal SUN_SAT
*** Relatorio de violacoes
*** Export CSV/HTML
** Governanca
*** Vigencia de politica
*** Referencia legal (CLT/CCT)
*** Evidencia por violacao
@endmindmap
```

### 1.2 Casos de Uso (Use Case)
```plantuml
@startuml
left to right direction
skinparam actorStyle awesome

actor "Gestora Operacional" as Gestora
actor "RH/DP" as RH
actor "Juridico" as Juridico
actor "Colaborador" as Colab

rectangle "Escala Compliance System (Piloto Caixa)" {
  usecase "Importar dados\n(PDF/XLSX)" as UC1
  usecase "Registrar preferencia\n(folga/turno/domingo)" as UC0
  usecase "Validar escala diaria\ncom politica ativa" as UC2
  usecase "Gerar sugestoes de ajuste" as UC3
  usecase "Aprovar/Rejeitar preferencia" as UC7
  usecase "Comparar visoes semanais\nMON_SUN vs SUN_SAT" as UC4
  usecase "Exportar relatorio auditavel" as UC5
  usecase "Versionar politica\npor vigencia" as UC6
}

Colab --> UC0
Gestora --> UC1
Gestora --> UC2
Gestora --> UC3
Gestora --> UC4
Gestora --> UC5
RH --> UC2
RH --> UC7
RH --> UC4
RH --> UC5
Juridico --> UC6
Juridico --> UC5

UC7 ..> UC0 : <<include>>
UC3 ..> UC2 : <<extend>>
UC5 ..> UC2 : <<include>>
UC5 ..> UC6 : <<include>>
@enduml
```

### 1.3 Componentes (Component Diagram)
```plantuml
@startuml
skinparam componentStyle rectangle

package "Presentation" {
  [Electron/React UI]
}

package "Application Layer" {
  [Validation Orchestrator]
  [Export Service]
}

package "Domain Layer" {
  [Policy Engine]
  [Suggestion Engine]
  [Preference Engine]
  [Week View Engine]
}

package "Infrastructure Layer" {
  [PDF/XLSX Parsers]
  [Dataset Repository]
  [Preference Repository]
  [Policy Repository]
  [Violation Reporter]
}

database "Processed CSV/JSON" as DataLake
database "Policy JSON" as PolicyStore

[Electron/React UI] --> [Validation Orchestrator]
[Validation Orchestrator] --> [PDF/XLSX Parsers]
[Validation Orchestrator] --> [Dataset Repository]
[Validation Orchestrator] --> [Preference Repository]
[Validation Orchestrator] --> [Policy Repository]
[Validation Orchestrator] --> [Policy Engine]
[Policy Engine] --> [Week View Engine]
[Policy Engine] --> [Suggestion Engine]
[Policy Engine] --> [Preference Engine]
[Preference Engine] --> [Preference Repository]
[Policy Engine] --> [Violation Reporter]
[Export Service] --> [Violation Reporter]
[Dataset Repository] --> DataLake
[Policy Repository] --> PolicyStore
@enduml
```

---

## 2. Fluxos Principais

### 2.1 Fluxo A - Ingestao + Validacao Completa

#### Sequencia
```plantuml
@startuml
actor "Gestora" as G
participant "Electron/React UI" as UI
participant "Validation Orchestrator" as ORQ
participant "Dataset Repository" as REPO
participant "Policy Repository" as PRepo
participant "Policy Engine" as PE
participant "Violation Reporter" as VR

G -> UI: Seleciona periodo + setor + politica
UI -> ORQ: run_validation(period, sector_id, policy_id)
ORQ -> REPO: load_assignments(period, sector_id)
REPO --> ORQ: day_assignments
ORQ -> PRepo: load_active_policy(policy_id, sector_id, period)
PRepo --> ORQ: policy_version
ORQ -> PE: validate(assignments, policy)
PE --> ORQ: violations + weekly_snapshots + stats
ORQ -> VR: build_report(result, policy_refs)
VR --> ORQ: compliance_report
ORQ --> UI: validation_result + report
UI --> G: tabela + alertas + evidencia
@enduml
```

#### Processo (Activity)
```plantuml
@startuml
start
:Carregar periodo solicitado;
:Carregar assignments canonicos\n(employee + date);
:Carregar politica ativa por vigencia;

if (Dados minimos completos?) then (sim)
  :Rodar hard constraints;
  :Rodar soft constraints;
  :Gerar visao MON_SUN;
  :Gerar visao SUN_SAT;
  :Consolidar violacoes por severidade;
else (nao)
  :Bloquear validacao;
  :Reportar pendencias de input;
  stop
endif

if (Tem violacao critica?) then (sim)
  :Status = INVALID;
else (nao)
  :Status = VALID ou VALID_WITH_WARNINGS;
endif

:Gerar relatorio auditavel;
stop
@enduml
```

### 2.2 Fluxo B - Sugestao de Ajuste para Quebrar Violacao

#### Sequencia
```plantuml
@startuml
actor "RH" as RH
participant "Electron/React UI" as UI
participant "Policy Engine" as PE
participant "Suggestion Engine" as SE
participant "Week View Engine" as WV

RH -> UI: Solicita correcao de violacoes
UI -> PE: get_violations(employee, period)
PE --> UI: violations list
UI -> SE: propose_fix(violations, constraints)
SE -> WV: simulate_weekly_impact(proposed_changes)
WV --> SE: hours_delta + streak_delta
SE --> UI: ranked_suggestions
UI --> RH: sugestao com explicacao e trade-off
@enduml
```

#### Processo (Activity)
```plantuml
@startuml
start
:Selecionar violacao alvo;
:Gerar candidatos de ajuste\n(mover folga / trocar domingo);

repeat
  :Simular impacto do candidato;
  if (Remove hard violation?) then (sim)
    if (Mantem horas no limite?) then (sim)
      :Marcar candidato como recomendado;
    else (nao)
      :Manter como opcao com alerta de horas;
    endif
  else (nao)
    :Descartar candidato;
  endif
repeat while (Ainda existem candidatos?)

if (Existe candidato recomendado?) then (sim)
  :Retornar top sugestoes ordenadas;
else (nao)
  :Retornar "sem ajuste automatico seguro";
endif
stop
@enduml
```

### 2.3 Fluxo C - Acordo Colaborador x RH (pedido dinamico)

#### Sequencia
```plantuml
@startuml
actor "Colaborador" as C
actor "RH" as RH
participant "Electron/React UI" as UI
participant "Preference Engine" as PREF
participant "Policy Engine" as PE

C -> UI: Registra pedido (folga/turno/domingo)
UI -> PREF: create_request(payload)
PREF -> PE: simulate_request_impact(payload, policy)
PE --> PREF: impact_result (hard/soft/coverage/hours)
PREF --> UI: recomendacao (ACEITAR ou REJEITAR)
RH -> UI: Decide pedido
UI -> PREF: apply_decision(request_id, decision)
PREF --> UI: escala atualizada + justificativa
@enduml
```

#### Processo (Activity)
```plantuml
@startuml
start
:Receber pedido do colaborador;
:Classificar tipo (folga/turno/domingo);
:Simular impacto no ciclo projetado;

if (Quebra hard constraint?) then (sim)
  :Sugerir REJEITAR;
  :Registrar motivo tecnico;
else (nao)
  if (Quebra cobertura minima?) then (sim)
    :Sugerir REJEITAR;
    :Registrar motivo operacional;
  else (nao)
    :Sugerir ACEITAR;
  endif
endif

:Aplicar Picking Rules (Rank Manual / Senioridade);
if (Conflito de prioridade?) then (sim)
  :Resolver via Rank (Cleonice ganha);
endif

:RH decide;
if (RH aprovou?) then (sim)
  :Aplicar mudanca na escala;
else (nao)
  :Manter escala original;
endif

:Registrar trilha (pedido, decisao, motivo);
stop
@enduml
```

---

## 3. Estrutura de Dados

### 3.1 Modelo ER
```plantuml
@startuml
entity "SectorProfile" as SectorProfile {
  * sector_id : String <<PK>>
  --
  sector_code : String
  name : String
  active : Boolean
}

entity "Employee" as Employee {
  * employee_id : String <<PK>>
  --
  sector_id : String <<FK>>
  full_name : String
  active : Boolean
  contract_code : String <<FK>>
}

entity "ContractProfile" as ContractProfile {
  * contract_code : String <<PK>>
  --
  sector_id : String <<FK>>
  weekly_minutes : Integer
  sunday_mode : Enum
}

entity "ShiftDefinition" as ShiftDefinition {
  * shift_code : String <<PK>>
  --
  sector_id : String <<FK>>
  minutes : Integer
  day_scope : WEEKDAY|SUNDAY
  immutable : Boolean
}

entity "ScaleCycle" as ScaleCycle {
  * scale_id : String <<PK>>
  --
  sector_id : String <<FK>>
  cycle_length_days : Integer
  label : String
  active : Boolean
}

entity "ScaleCycleAssignment" as ScaleCycleAssignment {
  * cycle_assignment_id : UUID <<PK>>
  --
  * sector_id : String <<FK>>
  * scale_id : String <<FK>>
  * employee_id : String <<FK>>
  * cycle_day : Integer
  status : WORK|FOLGA
  shift_code : String <<FK>>
}

entity "DayAssignment" as DayAssignment {
  * assignment_id : UUID <<PK>>
  --
  * sector_id : String <<FK>>
  * employee_id : String <<FK>>
  * work_date : Date
  scale_id : String <<FK>>
  cycle_day : Integer
  status : WORK|FOLGA|ABSENCE
  shift_code : String <<FK>>
  source : PDF|XLSX|MANUAL|ENGINE
}

entity "SundayRotation" as SundayRotation {
  * rotation_id : UUID <<PK>>
  --
  * sector_id : String <<FK>>
  * sunday_date : Date
  * employee_id : String <<FK>>
  folga_date : Date
  scale_index : Integer
}

entity "PolicyVersion" as PolicyVersion {
  * policy_id : String <<PK>>
  * policy_version : String <<PK>>
  --
  sector_id : String <<FK>>
  effective_from : Date
  effective_to : Date
  effective_from : Date
  effective_to : Date
  week_definition : MON_SUN|SUN_SAT
}

entity "PickingRules" as PickingRules {
  * policy_id : String <<FK>>
  --
  strategy : MANUAL_RANK | WEIGHTED_SCORE
  criteria : JSON
}

entity "ViolationEvent" as ViolationEvent {
  * violation_id : UUID <<PK>>
  --
  * employee_id : String <<FK>>
  * rule_code : String
  severity : CRITICAL|HIGH|MEDIUM|LOW
  date_start : Date
  date_end : Date
  evidence_json : JSON
}

entity "WeeklySnapshot" as WeeklySnapshot {
  * snapshot_id : UUID <<PK>>
  --
  * employee_id : String <<FK>>
  week_start : Date
  week_end : Date
  total_minutes : Integer
  target_minutes : Integer
}

SectorProfile ||--o{ Employee : groups
SectorProfile ||--o{ ContractProfile : defines_contracts
SectorProfile ||--o{ ShiftDefinition : defines_shifts
SectorProfile ||--o{ ScaleCycle : owns_cycle
SectorProfile ||--o{ DayAssignment : partitions
SectorProfile ||--o{ PolicyVersion : scopes_policy
Employee ||--|| ContractProfile : belongs_to
ScaleCycle ||--o{ ScaleCycleAssignment : has_days
Employee ||--o{ ScaleCycleAssignment : receives_pattern
ShiftDefinition ||--o{ ScaleCycleAssignment : classifies
Employee ||--o{ DayAssignment : has
ShiftDefinition ||--o{ DayAssignment : classifies
ScaleCycle ||--o{ DayAssignment : projects_to_date
Employee ||--o{ SundayRotation : participates
Employee ||--o{ ViolationEvent : may_trigger
Employee ||--o{ WeeklySnapshot : produces
PolicyVersion ||--o{ ViolationEvent : evaluates
PolicyVersion ||--|| PickingRules : defines_priority
@enduml
```

### 3.2 Estado do Ciclo de Escala
```plantuml
@startuml
[*] --> Draft : iniciar periodo
Draft --> ReadyForValidation : dados minimos completos
ReadyForValidation --> Invalid : hard violation encontrada
ReadyForValidation --> ValidWithWarnings : sem hard / com soft
ReadyForValidation --> ValidCompliant : sem violacao

Invalid --> ReadyForValidation : aplicar ajustes
ValidWithWarnings --> ReadyForValidation : ajustar opcional

ValidWithWarnings --> Published : aprovacao RH
ValidCompliant --> Published : aprovacao RH
Published --> Archived : fim da vigencia
Archived --> [*]
@enduml
```

### 3.3 Entradas Necessarias + Ordem de Alimentacao

#### Modelo de referencia
- Primary key estrutural: `sector_id + scale_id + employee_id + cycle_day`.
- Projecao operacional: `sector_id + employee_id + work_date` (unico por dia).
- Semana: sempre derivada da data (`MON_SUN` ou `SUN_SAT`), nunca chave base.

#### Entradas obrigatorias

| Ordem | Dataset de entrada | Obrigatorio | Chave minima | Observacao |
|---|---|---|---|---|
| 0 | `sector_registry` | Sim | `sector_id` | Define setores ativos no motor (ex.: `CAIXA`, `ACOUGUE`) |
| 1 | `compliance_policy` | Sim | `sector_id + policy_id + policy_version` | Regras legais/operacionais por setor |
| 2 | `employee_registry` | Sim | `sector_id + employee_id` | Nome vira atributo, nao chave |
| 3 | `shift_catalog` | Sim | `sector_id + shift_code` | Turnos validos por setor |
| 4 | `scale_cycle_template` | Sim | `sector_id + scale_id + cycle_day + employee_id` | Padrao fixo da escala |
| 5 | `cycle_projection_context` | Sim | `sector_id + period_start + period_end + anchor_date + anchor_cycle_day` | Ancoragem real do ciclo no calendario |
| 6 | `sunday_rotation` | Condicional | `sector_id + employee_id + sunday_date` | Obrigatorio para setor com trabalho aos domingos |
| 7 | `demand_profile` | Condicional | `sector_id + date + slot_start` | Cobertura minima por faixa horaria (picos/vales) |
| 8 | `employee_preferences` | Nao | `sector_id + employee_id + request_date + request_type` | Pedido do colaborador (folga/turno/domingo) |
| 9 | `exceptions` | Nao | `sector_id + employee_id + date + type` | Ferias, atestado, trocas, bloqueios |

#### Ordem de ingestao (pipeline)
1. Selecionar `sector_id` e validar existencia em `sector_registry`.
2. Validar `compliance_policy` + `shift_catalog` do setor.
3. Validar `employee_registry` do setor e resolver aliases.
4. Rodar preflight de consistencia entre fontes criticas (ex.: PDF vs XLSX domingo) com fail-fast.
5. Carregar `scale_cycle_template` do setor e checar completude por ciclo.
6. Projetar ciclo para calendario com `cycle_projection_context` (anchor explicito).
7. Aplicar `sunday_rotation` (quando setor operar domingo).
8. Aplicar `demand_profile` para validar cobertura por faixa horaria.
9. Aplicar `employee_preferences` (simulacao + decisao RH).
10. Aplicar `exceptions`.
11. Gerar `day_assignments` canonicos.
12. Rodar compliance e gerar visoes semanais (oficial + diagnostica).

#### Regras de correlacao (como os dados se ligam)

| Relacao | Chave primaria | Fallback | Regra de conflito |
|---|---|---|---|
| Particionamento global | `sector_id` | Nenhum | Nao misturar registros entre setores |
| Funcionario em qualquer fonte | `sector_id + employee_id` | `name_normalized` + alias map (dentro do setor) | Se ambiguo, bloquear |
| Turno | `sector_id + shift_code` | Nenhum | Codigo desconhecido invalida input |
| Padrao de ciclo | `sector_id + scale_id + cycle_day + employee_id` | Nenhum | Duplicata invalida template |
| Evento de dia projetado | `sector_id + employee_id + work_date` | Nenhum | Duplicata invalida projecao |
| Domingo x folga compensatoria | `sector_id + employee_id + sunday_date` | Nenhum | Sem folga vinculada => violacao |
| Pedido de preferencia | `sector_id + employee_id + request_date + request_type` | Nenhum | Se ambiguo ou sem decisao RH, nao aplica |

#### Resultado canonico apos ingestao
- `scale_cycle_assignments` (fixo, reutilizavel, particionado por `sector_id`).
- `day_assignments` (instancia por periodo, particionado por `sector_id`).
- `weekly_views` (somente leitura/analise por corte).

---

## 4. Estrutura de Codigo

### 4.1 Arvore de arquivos alvo
```text
horario/
|-- app.py
|-- pages/
|   |-- 1_Colaboradores.py
|   |-- 2_Pedidos.py
|   `-- 3_Configuracao.py
|-- scripts/
|   `-- seed.py
|-- data/
|   |-- fixtures/          # Seed canônico único
|   |   `-- seed_supermercado_fernandes.json
|   `-- processed/        # Saída da validação (gerado em runtime)
|-- docs/
|   `-- BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md
|-- schemas/
|   |-- compliance_policy.schema.json
|   `-- compliance_policy.example.json
|-- src/
|   |-- application/
|   |   `-- use_cases.py
|   |-- domain/
|   |   |-- models.py
|   |   |-- policy_loader.py
|   |   `-- engines.py
|   `-- infrastructure/
|       |-- database/
|       |-- parsers/legacy/
|       `-- repositories_db.py
```

### 4.2 Responsabilidades

| Camada | Responsabilidade | Resultado |
|---|---|---|
| `scripts/` | Extrair e normalizar dados brutos | CSV/JSON confiavel para processamento |
| `src/domain/` | Regras de negocio e compliance | Violacoes + sugestoes deterministicas |
| `src/application/` | Orquestrar casos de uso | Fluxo completo de validacao/exportacao |
| `src/infrastructure/` | IO, parser, repositorios e apresentacao | Integracao com arquivos e UI |
| `schemas/` | Contrato de politica versionada | Validador de configuracao legal/operacional |
| `tests/` | Regressao de regras criticas | Confianca para evoluir sem quebrar |

---

## 5. Consolidacao

### TL;DR
- O core do sistema e multi-setor, sempre particionado por `sector_id`; o piloto atual homologado e Caixa.
- O sistema deve usar `scale_cycle` como base estrutural e projetar para granularidade diaria (`employee + date`).
- Semana deve existir apenas como visao derivada.
- O motor de compliance fica separado da ingestao de dados para reduzir acoplamento.
- Politica legal/operacional precisa ser versionada por vigencia para nao hardcodar regra.
- Saida deve ser explicavel (regra, evidencias, impacto e sugestao) para RH/Juridico.
- Schema de politica e o contrato central para previsibilidade de execucao.

### Documentos de suporte
- **SISTEMA_ESCALAFLOW.md**: Doc unificado — fluxo do usuario, fixtures, processados, setup, arquitetura resumida.

### Checklist de implementacao (ordem obrigatoria)

| # | Item | Tipo | Dependencia |
|---|---|---|---|
| 1 | Formalizar `sector_registry` + particionamento `sector_id` em todo input/output | Data contract | - |
| 2 | Definir semantica oficial dos marcadores `5/6` e bloquear publish com `UNKNOWN` | Product/Data | 1 |
| 3 | Definir corte semanal oficial de bloqueio (`MON_SUN` ou `SUN_SAT`) | Product/RH | 1 |
| 4 | [DONE] Implementar preflight fail-fast de conflito entre fontes criticas (PDF vs XLSX) | Infrastructure | 1 |
| 5 | Implementar `ScaleCycle -> DayAssignment` com ancoragem explicita (`anchor_date + anchor_cycle_day`) | Domain | 1 |
| 6 | Implementar aplicacao real de `exceptions` (ferias/atestado/troca) com precedencia definida | Domain | 5 |
| 7 | Implementar interjornada auditavel (inicio/fim por turno e por dia) | Domain | 5 |
| 8 | Implementar validacao de cobertura por faixa horaria (`demand_profile`) | Domain | 5 |
| 9 | Consolidar detector de streak em bloco unico (sem ruido 7/8/9 repetido) | Domain | 5 |
| 10 | [WIP] Promover `PreferenceEngine` com Picking Rules (Rank Manual / Fator Cleonice) | Domain/Application | 6, 7, 8 |
| 11 | Integrar no `app.py` com dashboard de violacoes + fila de pedidos | Presentation | 10 |
| 12 | Criar testes de regressao com datasets reais por setor (Caixa primeiro) | QA | 4, 6, 7, 8, 10 |

### Dependencias externas
- [ ] Definicao oficial da semantica dos marcadores `5` e `6`.
- [ ] Definicao oficial de corte semanal da operacao (`MON_SUN` ou `SUN_SAT`).
- [ ] Validacao juridica interna sobre regra aplicavel de domingo/feriado (CCT + CNAE + vigencia).
- [ ] Definir ordem de onboarding dos proximos setores (ex.: Acougue, Padaria, FLV) e dono de cada policy.

### Riscos identificados

| Risco | Impacto | Mitigacao |
|---|---|---|
| Escopo misturado (Caixa vs multi-setor) | Alto | Toda entrada/saida particionada por `sector_id` + onboarding por setor |
| Semantica de marcador errada | Alto | Tratar como configuracao obrigatoria no schema e bloquear publish sem mapa valido |
| Semana de apuracao divergente de RH | Alto | Calcular e exibir as duas visoes simultaneamente ate definicao oficial |
| Mudanca legal no meio do periodo | Alto | Versionar politica por vigencia e registrar referencia legal em cada violacao |
| Dados de entrada com ruido (nomes/linhas espurias) | Medio | Pipeline de normalizacao + limpeza deterministica + testes com fixtures reais |
| Heuristica de ajuste gerar efeito colateral | Medio | Rodar simulacao completa e impedir recomendacao que cria hard violation nova |
| Pedido de colaborador conflitar com cobertura/compliance | Alto | Passar por gate RH + simulacao obrigatoria com motivo de aceite/rejeicao |
