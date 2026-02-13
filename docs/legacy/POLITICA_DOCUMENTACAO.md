# Política de Documentação — EscalaFlow

> **Objetivo:** Manter docs sempre atualizados para trabalhar de forma fechada — fechar lacunas e resolver qualquer tipo de situação.

---

## 1. Princípio

**A documentação oficial deve refletir o estado real do sistema.** Ao implementar mudanças, atualizar imediatamente os docs relevantes. Não esperar "quando terminar tudo" — atualizar no mesmo ciclo de trabalho.

---

## 2. Doc Mestre (Operacional)

| Doc | Conteúdo | Quando atualizar |
|-----|----------|------------------|
| `docs/SISTEMA_ESCALAFLOW.md` | Fluxo do usuário, setup, dados, arquitetura resumida | Novos fluxos, novos endpoints, mudança de stack |
| `docs/BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md` | Arquitetura completa (PlantUML, ER, fluxos) | Mudanças no motor, novos domínios, alteração de schema |
| `docs/WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md` | Backlog mestre, dashboard de guerra | Ao concluir tasks, ao replanejar |

---

## 3. Regra de Atualização

**Ao implementar feature/correção:**

1. **Durante:** Verificar se `SISTEMA_ESCALAFLOW.md` ou `BUILD` precisam de ajuste.
2. **Ao concluir:** Atualizar `WARLOG` (status da task, log cronológico).
3. **Se novo fluxo:** Documentar em `SISTEMA_ESCALAFLOW.md` seção 3 (Fluxo do usuário).
4. **Se novo endpoint/schema:** Atualizar `BUILD` seção 3 (Estrutura de dados) e `README.md` se aplicável.

---

## 4. Checklist por Release / Merge

Antes de fechar PR ou marcar release:

- [ ] `README.md` — setup e comandos corretos
- [ ] `docs/SISTEMA_ESCALAFLOW.md` — fluxo e estrutura batem com o código
- [ ] `docs/SISTEMA_ESCALAFLOW.md` — governança runtime (preflight, NORMAL/ESTRITO, ACK, auditoria) documentada quando houver mudança
- [ ] `docs/BUILD_*` — ER e fluxos atualizados (se houver mudança)
- [ ] `docs/WARLOG_*` — status das tasks atualizado
- [ ] `.cursor/rules/agent.mdc` — stack e estrutura refletem o atual

---

## 5. Docs Legadas

| Doc | Local | Uso |
|-----|-------|-----|
| PRD 001 | `docs/legacy/PRD_001_escala_electron_backlog_legacy.md` | Referência histórica; não é fonte de verdade |
| Redpill Leis | `docs/legacy/REDPILL_LEIS_LOGICA_HUMANA_ESCALA.md` | Pirâmide de prioridade e algoritmo de alocação — referência para evolução do motor |
| Warlog antigo do Electron | `docs/WARLOG_ESCALA_CAIXA_ELECTRON.md` | Histórico de execução inicial; manter só para rastreabilidade |

---

## 6. Índice de Docs Ativos

```
docs/
├── SISTEMA_ESCALAFLOW.md           ← Doc mestre operacional
├── BUILD_ARQUITETURA_MOTOR_COMPLIANCE_ESCALA_CAIXA.md  ← Arquitetura do motor
├── WARLOG_SISTEMA_ESCALAFLOW_GLOBAL.md  ← Backlog mestre
├── POLITICA_DOCUMENTACAO.md        ← Este arquivo
├── WARLOG_ESCALA_CAIXA_ELECTRON.md ← Histórico legado (não ativo)
└── legacy/
    ├── PRD_001_escala_electron_backlog_legacy.md
    └── REDPILL_LEIS_LOGICA_HUMANA_ESCALA.md
```

---

## 7. O que "Fechar" Significa

O sistema está **fechado** quando:

- **Fluxo:** O RH consegue fazer tudo pela UI (configurar, gerar, exportar, aprovar pedidos) sem depender de seed manual ou scripts.
- **Cobertura:** Todos os CRUDs de configuração (turnos, mosaico, rodízio, exceções, demand) existem e funcionam.
- **Resiliência:** Indicador de API, retry, loading states implementados.
- **Documentação:** Docs refletem o estado real; não há divergência entre doc e código.
