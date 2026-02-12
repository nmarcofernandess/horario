# LÓGICA: O FATOR HUMANO NA ESCALA (JOGO DO PRESIDENTE)

> Gerado por Miss Monday via /analyst em 2026-02-11
> Base: Conversa com Mãe (RH) + Conceito "Burro Bebe Água"

## TL;DR EXECUTIVO
O sistema não pode ser apenas binário (Pode/Não Pode). A realidade operacional exige uma **Fila de Prioridade Baseada em Contexto**. A "Cleonice" não é um `if`, é uma **Regra de Senioridade**. A "Igreja" não é exceção aleatória, é uma **Restrição de Disponibilidade Pactuada**. O "Jogo do Presidente" é o algoritmo de resolução de conflitos.

---

## 1. O CONCEITO "BURRO BEBE ÁGUA" (Priority Queue)

Na teoria dos jogos (e na vida real), recursos escassos (folgas no domingo, turnos bons) são alocados por ordem de poder.

### A Pirâmide de Prioridade

```plantuml
@startmindmap
* Alocação de Escala
** 1. LEI (CLT/Sindicato)
*** 11h Interjornada
*** 1 folga/semana
*** Domingo a cada X
** 2. OPERAÇÃO (A Loja Abre)
*** Cobertura Mínima
*** Abertura/Fechamento Keyholder
** 3. PACTOS (Acordos Fixos)
*** Igreja (Restrição Horária)
*** Faculdade (Restrição Horária)
*** Transporte (Restrição Geográfica)
** 4. MERITOCRACIA (VIPs)
*** "Fator Cleonice" (Senioridade)
*** Performance
** 5. DEMOCRACIA (Preferência)
*** "Quem pediu primeiro"
*** Rodízio de desejos
** 6. O BURRO (Sobras)
*** Preenche lacunas restantes
@endmindmap
```

---

## 2. TRADUÇÃO: DE "DONA CLEONICE" PARA "SISTEMA"

Não podemos hardcodar nomes. Precisamos de **Atributos Qualificadores**.

| O que a mãe disse | O que o sistema entende (Atributo) | Tipo de Regra |
|---|---|---|
| "Faz 26 anos que ela trabalha" | `seniority_score` (int) ou `tags: ["VIP_LEGACY"]` | Tie-breaker (Desempate) |
| "Vá na igreja" | `availability_constraints` (TimeWindow bloqueada) | Hard Constraint (pessoal) |
| "Pergunto qual dia prefere" | `preference_request` (Input dinâmico) | Soft Constraint (Maximizar) |
| "Prioridade de sair mais cedo" | `preferred_shift_pattern` | Soft Constraint |

---

## 3. MODELAGEM LÓGICA (ER Estendido)

Precisamos estender o modelo do `Employee` para suportar essa complexidade sem código espaguete.

```plantuml
@startuml
entity "EmployeeProfile" as Emp {
  * employee_id : UUID
  --
  name : String
  seniority_date : Date
  seniority_tier : L1..L5
  tags : List<String> ["IGREJA", "FACULDADE"]
}

entity "AvailabilityConstraint" as Avail {
  * constraint_id : UUID
  --
  employee_id : FK
  day_of_week : MON..SUN
  blocked_start : Time
  blocked_end : Time
  reason : "RELIGIOUS" | "EDUCATION" | "HEALTH"
  rigidity : HARD | SOFT
}

entity "PrioritizationRule" as Rule {
  * rule_id : UUID
  --
  criteria : "SENIORITY" | "FIRST_COME" | "ROTATION"
  weight : Integer
}

Emp ||--o{ Avail : possui
@enduml
```

---

## 4. ALGORITMO DE ALOCAÇÃO (Fluxo)

O motor não roda aleatório. Ele roda em **Passadas (Passes)**.

```plantuml
@startuml
start
:Inicializar Grade Vazia;

partition "Passo 1: Bloqueios Rígidos" {
  :Aplicar CLT (Folgas Obrigatórias);
  :Aplicar Pactos Fixos (Igreja, Faculdade);
}

partition "Passo 2: Definição Operacional" {
  :Verificar Demand Profile (Mínimo de gente);
  if (Sobrou gente suficiente?) then (sim)
    :Seguir;
  else (nao)
    #pink:ALERTA: Pactos inviabilizam operação;
    :Fura pacto SOFT ou pede hora extra;
  endif
}

partition "Passo 3: O Jogo do Presidente (Alocação de Preferência)" {
  :Listar Pedidos de Preferência;
  :Ordenar Funcionários por SCORING (Senioridade + Rank);
  
  while (Tem funcionário na fila?) is (sim)
    :Pegar Top 1 (A "Cleonice");
    if (Pedido cabe na grade?) then (sim)
      :Atender Pedido;
      :Travar Horário;
    else (nao)
      :Registrar "Não Atendido";
      :Alocar no que sobrou (Melhor possível);
    endif
  endwhile (nao)
}

partition "Passo 4: O Burro (Preenchimento)" {
  :Pegar funcionários sem preferência/não atendidos;
  :Preencher buracos da escala para bater meta;
}

stop
@enduml
```

---

## 5. IMPACTO NO SCHEMA (Ação Imediata)

Para suportar isso, o `compliance_policy.schema.json` e o `employee_registry` precisam evoluir.

### Novo Objeto Sugerido: `PickingRules`

```json
"picking_rules": {
  "method": "weighted_score",
  "criteria": [
    { "field": "seniority_years", "weight": 10 },
    { "field": "tags", "match": "VIP", "weight": 50 },
    { "field": "last_request_granted", "weight": -5 }  // Rodízio: quem ganhou antes, perde agora
  ]
}
```

---

## CONCLUSÃO ANALYTICA

O "Micro gerenciamento" que a mãe faz é intuitivo, mas segue um algoritmo claro de **Ranking**.
Se o sistema tentar tratar todos como iguais (Democracia Pura), vai falhar na realidade da loja (onde a Cleonice manda).

**O sistema precisa de um campo `priority_score` calculado para cada funcionário.**
Quem tem score maior, tem seus pedidos processados primeiro pelo motor de alocação.
