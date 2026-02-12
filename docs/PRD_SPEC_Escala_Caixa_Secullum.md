# PRD + SPEC — Escala de Caixa (Supermercado) com Domingo Curto (4h30) — Secullum Ponto Web

## 0) TL;DR (executivo)
Precisamos de um módulo/rotina para **gerar, validar e exportar** escalas de trabalho do setor **Caixa**, mantendo **horários fixos (CAI1…CAI6)** de **segunda a sábado** e um **turno de domingo fixo (08:00–12:30 / 4h30)**.  
O sistema deve garantir simultaneamente:
- **Conformidade de descanso (DSR prático)**: ninguém pode trabalhar **7 dias consecutivos** (limite: **máximo 6 dias seguidos**).
- **Carga horária semanal por contrato**, sem alterar horários:
  - 44h: Cleonice, Ana Júlia
  - 36h: Gabriel
  - 30h: Mayumi, Heloísa, Alice
- Compatibilidade com **Secullum Ponto Web** (fechamento semanal configurável).

O problema atual é que escalas “visualmente ok” acabam:
1) estourando **7 dias seguidos** em alguns trechos (passivo alto), e/ou  
2) “não fechando” horas quando o RH soma numa semana diferente da semana de apuração.

---

## 1) Contexto do negócio
### 1.1 Ambiente
- Empresa: supermercado (varejo)
- Setor: **Caixa**
- Controle de ponto: **Secullum Ponto Web**
- Escala operacional:
  - **Segunda a sábado**: turnos codificados (CAI1…CAI6) já definidos, **não podem mudar**.
  - **Domingo**: **08:00–12:30** (turno curto, 4h30).
- Existe um quadro/planilha/relatório onde:
  - **Branco = trabalho normal**
  - **“FOL” = folga**
  - Nos domingos existe uma escala de “quem trabalha” (normalmente 3 pessoas por domingo).

### 1.2 Objetivo
Criar uma escala correta (e/ou validações automáticas) que:
- mantenha os horários atuais;
- distribua domingos conforme regra (ou conforme uma lista de “quem trabalha”);
- garanta descanso semanal prático (sem 7 dias consecutivos);
- feche horas do contrato (44/36/30) dentro do período de apuração escolhido;
- permita exportação (PDF/Excel/CSV ou tabela) para uso interno.

---

## 2) Problema atual (dor)
### 2.1 Sintomas
- Em escalas atuais, quando “branco = trabalho” e só “FOL” é folga, alguns colaboradores fazem **7 dias seguidos** em certas sequências (ex.: após folga em um domingo, trabalham seg–sáb e só folgam no domingo seguinte).
- Quando o RH soma horas por semana, percebe “semanas que não fecham 44h”, principalmente quando:
  - o domingo (4h30) cai no fim de uma semana Seg–Dom,
  - e a folga compensatória cai na semana seguinte.
  Isso gera confusão, retrabalho e risco de interpretação incorreta.

### 2.2 Impactos
- **Risco trabalhista**: sequência de 7 dias consecutivos.
- **Risco operacional**: escalas inconsistentes, dificuldade em explicar para equipe.
- **Risco de folha/ponto**: divergência de apuração semanal vs escala.

---

## 3) Escopo
### 3.1 Dentro do escopo (MVP)
1) **Validador de escala**:
   - detectar automaticamente qualquer ocorrência de **7 dias consecutivos trabalhados**.
   - validar **1 folga por janela de 7 dias corridos** (janela móvel).
2) **Validação de carga horária** por contrato dentro de um período:
   - semanal (com semana configurável: Seg–Dom ou Dom–Sáb),
   - e/ou mensal/período informado.
3) **Geração de escala** (opcional no MVP, mas desejado):
   - dado um período (ex.: 08/02/2026 a 31/03/2026),
   - dados de funcionários e seus contratos,
   - regras de domingo (lista fixa ou rodízio),
   - regras de “folga fixa/compensatória”,
   - produzir escala final com “FOL” e “DOM 08:00–12:30”.
4) **Exportação**:
   - Markdown/CSV/Excel ou HTML simples (para colar/mandar).
   - Formato “calendário” dia a dia e formato “por semana”.

### 3.2 Fora do escopo (por enquanto)
- Alterar horários CAI1…CAI6.
- Otimização de dimensionamento (quantos caixas devem trabalhar por dia).
- Integração direta com API do Secullum (se existir/for viável) — apenas exportação/import manual.

---

## 4) Dados e entidades

### 4.1 Funcionários (caixa)
| Nome | Carga semanal | Identificador |
|---|---:|---|
| Cleonice | 44h | CLE |
| Ana Júlia | 44h | ANJ |
| Gabriel | 36h | GAB |
| Mayumi | 30h | MAY |
| Heloísa | 30h | HEL |
| Alice | 30h | ALI |

### 4.2 Turnos (fixos)
- **Domingo**: `DOM_08_12_30` = 08:00–12:30 = **4h30**.
- **Segunda a sábado**: turnos codificados `CAI1…CAI6` (horários exatos vêm do PDF interno).
  - Importante: para o algoritmo, cada CAI# deve ter uma **duração em minutos** para cálculo de horas.
  - Ex.: `CAI1 = X min`, `CAI2 = Y min`, etc.

> Nota: o sistema não deve “inventar” novos turnos. Só aplica CAI# já existentes e o domingo 08–12:30.

### 4.3 Representação da escala
Estrutura sugerida:
```json
{
  "period_start": "2026-02-08",
  "period_end": "2026-03-31",
  "week_definition": "SUN_SAT" | "MON_SUN",
  "employees": [...],
  "assignments": [
    {
      "date": "2026-02-08",
      "employee_id": "CLE",
      "shift_code": "DOM_08_12_30" | "CAI1" | "FOL"
    },
    ...
  ]
}
```

---

## 5) Regras de negócio (hard rules)

### 5.1 Descanso semanal / 6x1 (janela móvel)
**Regra R1 (obrigatória):** Para qualquer colaborador, é proibido ter **7 dias consecutivos trabalhados**.  
- Implementação: varrer o período dia-a-dia e contar streak de dias trabalhados; ao atingir 7, **invalidar**.
- Observação: esta validação **não depende** de semana Seg–Dom ou Dom–Sáb.

### 5.2 Domingo curto
**Regra R2:** Todo domingo tem turno fixo **08:00–12:30** para quem está escalado para trabalhar no domingo.  
- Duração fixa: 270 minutos.

### 5.3 Carga horária semanal por contrato
**Regra R3:** O sistema deve validar a carga horária com base no contrato:
- 44h (2640 min), 36h (2160 min), 30h (1800 min),
dentro do “corte” de apuração escolhido:
- `MON_SUN` (Seg–Dom) ou `SUN_SAT` (Dom–Sáb)

**Observação importante:** É permitido “balanço” semanal se a empresa apura por mês/período e estiver correto no período. Porém o requisito do cliente é conseguir validar por semana **conforme o corte escolhido** para evitar confusão.

### 5.4 Horários imutáveis
**Regra R4:** Não pode alterar o conteúdo dos turnos CAI#.  
O módulo só escolhe “qual CAI#” ou “FOL” (ou domingo).

### 5.5 Domingo x folga compensatória (modelo operacional)
Existe um modelo operacional recorrente:
- Em algumas semanas, o colaborador **trabalha no domingo** (4h30).
- Para manter a carga semanal do contrato **sem mexer em horários**, a folga deve ocorrer em um dia da semana que “equilibre” a soma.

O sistema deve suportar 2 modos de compensação (config):
- **Modo C1 — Folga fixa vinculada ao domingo trabalhado**:  
  Se trabalha no domingo, folga em um dia pré-definido da semana (por funcionário).  
- **Modo C2 — Folga no domingo quando não escalado**:  
  Se não trabalha no domingo, folga no domingo (DSR) e trabalha normalmente seg–sáb.

> O cliente informou que existe uma lógica do tipo “um dia na semana o funcionário trabalha só 4h30” relacionada ao domingo. Portanto, no cálculo, domingo deve ser tratado como turno curto e a folga/compensação deve ser posicionada para não violar R1.

---

## 6) Entradas do sistema

### 6.1 Configurações
- `period_start`, `period_end`
- `week_definition`: `SUN_SAT` ou `MON_SUN`
- `employees`: lista + contrato (44/36/30)
- `shift_catalog`: mapa CAI# -> duração (min) + domingo fixo 270 min
- `sunday_staffing_requirement`: quantos funcionários trabalham no domingo (ex.: 3)
- `sunday_assignment_mode`:
  - `LIST`: lista explícita por domingo com nomes
  - `ROTATION`: rodízio automático equilibrado com regras

### 6.2 Dados operacionais do cliente (existentes)
- PDF A: horários CAI1…CAI6 (seg–sáb)
- PDF B: listagem de “quem trabalha no domingo / folga” (regras internas)

O módulo deve permitir importar isso manualmente:
- tabela de CAI# -> duração
- lista de domingos -> empregados escalados

---

## 7) Saídas do sistema

### 7.1 Outputs principais
1) **Escala final** (dia a dia):
   - para cada data no período,
   - por funcionário: `CAI#` ou `FOL` ou `DOM 08:00–12:30`
2) **Resumo por semana** (conforme corte):
   - horas totais por funcionário vs contrato
   - flags de inconsistência
3) **Relatório de conformidade**:
   - lista de violações de R1 (7 dias seguidos) com datas
   - violações de R3 (carga semanal fora do contrato) por semana

### 7.2 Formatos de exportação
- Markdown (`.md`) — fácil de compartilhar
- CSV (opcional) — fácil para Excel
- HTML (opcional) — para impressão e colar na parede

---

## 8) Algoritmo (proposta)

### 8.1 Validação de 7 dias consecutivos (R1)
Para cada funcionário:
- ordenar datas do período
- `streak = 0`
- se dia é `FOL`: `streak = 0`
- se dia é trabalho (CAI# ou domingo): `streak += 1`
- se `streak >= 7`: registrar violação com intervalo `[date-6 .. date]`

### 8.2 Cálculo de horas por semana (R3)
- Converter cada turno em minutos
- Agrupar por semana conforme `week_definition`:
  - `MON_SUN`: semana começa segunda 00:00
  - `SUN_SAT`: semana começa domingo 00:00
- Somar por funcionário
- Comparar com contrato (minutos esperados)

### 8.3 Geração automática (se implementado)
**Inputs mínimos**:
- domingos do período
- quantidade exigida no domingo (ex.: 3)
- regra de rodízio/justiça (equilibrar domingos por funcionário, respeitando contratos)
- regra de folga associada ao domingo (C1/C2)

**Heurística recomendada**:
1) Garantir cobertura de domingo (selecionar N pessoas).
2) Para cada pessoa selecionada para domingo:
   - agendar `DOM_08_12_30`
   - agendar a folga compensatória no “dia curto” dela (se configurado C1)
3) Para quem não foi selecionado no domingo:
   - agendar `FOL` no domingo (C2) **ou** manter domingo livre conforme política
4) Passar validador R1; se violar, ajustar movendo folga compensatória para quebrar streak.
5) Passar validador R3; se violar, ajustar distribuindo domingos ou trocando seleção do domingo.

> Nota: o gerador pode ser guloso (greedy) com backtracking leve:
- “corrige primeiro 7 dias seguidos (R1), depois corrige horas (R3)”.

---

## 9) Casos e cenários (exemplos)
### 9.1 Cenário correto típico
- Funcionária 44h trabalha domingo (4h30) e folga um dia da semana para compensar, sem ultrapassar 6 dias seguidos.

### 9.2 Cenário de risco
- Folga marcada em um domingo, e a próxima folga só no domingo seguinte, com seg–sáb em branco (trabalho): isso cria 7 dias seguidos.

### 9.3 “Semanas que não fecham” (explicação de negócio)
Mesmo com escala correta, se a empresa soma horas em `MON_SUN`, pode haver semana que não “fecha” porque parte da compensação cai na semana seguinte.  
Por isso, a **definição de semana de apuração** precisa ser explícita e consistente no relatório.

---

## 10) Requisitos não-funcionais
- Fácil de auditar (relatórios claros).
- Exportação simples (Markdown/CSV/HTML).
- Configurável por loja/filial (semana, quantidade no domingo).
- Determinístico: mesma entrada gera mesma escala.

---

## 11) Critérios de aceitação (DoD)
Para o período informado (08/02/2026 a 31/03/2026), o sistema deve:
1) Produzir escala sem alterar CAI# e com domingo 08:00–12:30.
2) Garantir zero violações de 7 dias consecutivos (R1).
3) Gerar relatório semanal (MON_SUN e SUN_SAT) mostrando horas e divergências.
4) Para cada funcionário, as horas por contrato devem fechar no corte escolhido (quando a política de escala assim exigir).
5) Exportar em `.md` (no mínimo) com:
   - calendário dia a dia
   - tabela por semana
   - resumo de validações

---

## 12) Perguntas em aberto (para dev confirmar antes de codar)
1) **Quantas pessoas precisam trabalhar no domingo no caixa?** (foi citado 3; confirmar fixo.)
2) O módulo deve **gerar** escala ou apenas **validar/corrigir** uma escala existente?
3) Existe algum dia fixo de “folga preferencial” por funcionário (além da lógica interna)?
4) Precisamos considerar férias/atestados/afastamentos (exceções) no período?
5) A apuração oficial do Secullum (na empresa) está configurada como **MON_SUN** ou **SUN_SAT**?

---

## 13) Anexos (inputs do cliente)
- PDF com turnos do caixa (CAI1…CAI6) seg–sáb.
- PDF com rodízio de domingo/folgas.
- Evidência: domingo fixo 08:00–12:30 e “branco = trabalho normal”.

