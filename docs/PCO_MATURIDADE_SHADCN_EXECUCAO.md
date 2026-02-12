# PCO — Plano de Execucao para Maturidade Shadcn (EscalaFlow)

> Objetivo: sair de "funciona e parece bom" para "arquitetura de composicao madura, elegante, consistente e escalavel".
>  
> Escopo: `apps/frontend/src/renderer`  
> Estilo alvo: produto desktop com padrao de startup .io (alto nivel de acabamento visual + robustez tecnica)

---

## FASE 1 — OBJETIVO ESTRATEGICO

**O meu objetivo estrategico e** transformar o frontend em um sistema de UI maduro, com composicao idiomatica de shadcn, consistencia entre telas e qualidade de produto "premium", sem quebrar o fluxo operacional do EscalaFlow.

### Problema real (nao literal)
- O projeto ja usa shadcn, mas ainda existe gap entre "uso de componentes" e "arquitetura de composicao madura".
- Algumas telas ainda estao acopladas demais (principalmente `ConfiguracaoPage`).
- Existem inconsistencias de acessibilidade e estrutura de formularios.
- Parte da expressao visual ainda depende de classes locais/hardcoded em vez de variacoes padronizadas.

### Resultado de negocio esperado
- Menos retrabalho por tela.
- Onboarding mais rapido para novos devs.
- Menor risco de regressao visual/UX.
- Percepcao de produto premium para usuario final.

### O que voce quer vs o que foi pedido
- Pedido literal: "deixar lindo/vale do silicio e arrumar composicao".
- Intencao real: criar um frontend que pareca e se comporte como produto maduro, com padrao tecnico repetivel.

### Objetivos adjacentes
- Definir onde cada bloco deve viver (`ui/`, `components/`, `pages/`).
- Criar criterio de "Definition of Done de UI" para evitar voltar ao estado de remendo.
- Organizar uma trilha executavel para o time continuar sem dependencia de contexto de conversa.

---

## FASE 2 — PLANO DE EXECUCAO ARQUITETURAL

**O plano de execucao e**:

1. **Congelar baseline de maturidade UI**
   - O que fazer: inventariar estado atual por tela e componente.
   - Por que nessa ordem: evita refatorar no escuro.
   - Dependencias: nenhuma.

2. **Padronizar acessibilidade e anatomia de composicao**
   - O que fazer: fechar `Label` + `htmlFor` + `id`, `CardDescription`, `CardAction`, anatomia de `Table`.
   - Dependencias: baseline concluido.
   - Pontos de atencao: nao mudar regra de negocio.

3. **Padronizar formularios e validacao (camada de sistema)**
   - O que fazer: adotar stack de formulario unica para paginas de cadastro/edicao.
   - Dependencias: etapa 2 (semantica base).
   - Pontos de atencao: migracao incremental por tela.

4. **Desacoplar telas monoliticas em blocos compostos**
   - O que fazer: decompor `ConfiguracaoPage` em subcomponentes de dominio.
   - Dependencias: etapa 3.
   - Pontos de atencao: manter contrato atual com API.

5. **Elevar acabamento visual premium (tokens + variacoes + feedback)**
   - O que fazer: remover hardcoded visual, padronizar variantes, estados de loading/empty/error, micro-interacoes.
   - Dependencias: etapas 2-4.
   - Pontos de atencao: consistencia de tema light/dark.

6. **Auditar, testar e institucionalizar padrao**
   - O que fazer: checklist final por tela + doc de governanca.
   - Dependencias: todas anteriores.
   - Validacao: build/test + QA visual + checklist de composicao.

---

## FASE 3 — ANALISE DE RISCOS E MITIGACAO

**Os riscos sao**:

| # | Risco | Impacto | Probabilidade | Contramedida |
|---|-------|---------|---------------|--------------|
| 1 | Refatorar UI e quebrar fluxos de cadastro | Alto | Media | Migracao incremental por tela com smoke test manual apos cada bloco |
| 2 | Introduzir inconsistencia nova durante "embelezamento" | Medio | Alta | Definir checklist unico de composicao e aplicar em PR |
| 3 | Tela de configuracao continuar gigante mesmo apos ajustes pontuais | Alto | Alta | Refatoracao estrutural obrigatoria em subcomponentes |
| 4 | Over-engineering no formulario | Medio | Media | Padrao minimo (schema + mensagens + estados) sem abstrair demais no inicio |
| 5 | Regressao de acessibilidade | Alto | Media | Checklist de `htmlFor/id`, `aria-*`, foco, navegacao teclado |
| 6 | Divergencia entre design e implementacao | Medio | Media | Criar "tokens + variantes oficiais" e proibir hardcoded sem justificativa |
| 7 | Time voltar ao estilo antigo por falta de guardrails | Alto | Alta | Publicar "Definition of Done UI" e incluir em revisão obrigatoria |

---

## FASE 4 — GERACAO DO ARTEFATO (PASSO A PASSO EXECUTAVEL)

**Executando: maturidade completa de composicao shadcn e acabamento premium**

### Sprint 0 — Baseline e regras

1. Criar checklist de auditoria UI por tela:
   - Composicao (`Card`, `Table`, `Dialog`, `AlertDialog`, `Tabs`)
   - Acessibilidade (`Label/htmlFor/id`, foco, teclado)
   - Estados (`loading`, `empty`, `error`, `success`)
   - Visual (tokens vs hardcoded)

2. Congelar baseline visual com screenshots das paginas:
   - `EscalaPage`
   - `ColaboradoresPage`
   - `PedidosPage`
   - `ConfiguracaoPage`
   - `PerfilPage`

3. Definir "Definition of Done UI" (na pasta `docs/` ou `.cursor/rules/`):
   - Nenhum form novo sem label vinculado.
   - Nenhum bloco principal fora da anatomia shadcn esperada.
   - Nenhuma cor hardcoded fora de casos aprovados.

---

### Sprint 1 — Composicao canonica (sem mexer em negocio)

4. Fechar acessibilidade pendente em formularios:
   - `apps/frontend/src/renderer/pages/ConfiguracaoPage.tsx`
   - `apps/frontend/src/renderer/pages/PerfilPage.tsx`
   - Acao: adicionar `id` em `Input`/`SelectTrigger` e `htmlFor` em todo `Label`.

5. Revisar anatomia de cards:
   - Onde houver acao de topo, usar `CardAction`.
   - Onde houver texto de contexto, usar `CardDescription`.
   - Arquivos alvo: `ConfiguracaoPage.tsx`, `ColaboradoresPage.tsx`, `PedidosPage.tsx`, `PerfilPage.tsx`.

6. Revisar anatomia de tabelas:
   - Usar `TableCaption` quando agrega contexto de leitura.
   - Usar `TableFooter` para totalizadores quando aplicavel.
   - Arquivos alvo: `EscalaPage.tsx`, `ColaboradoresPage.tsx`, `ConfiguracaoPage.tsx`.

7. Padronizar empty states:
   - Mensagem curta, clara, orientada a acao.
   - Mesmo tom de linguagem em todas as paginas.

---

### Sprint 2 — Sistema de formularios maduro

8. Introduzir stack de form (incremental):
   - Biblioteca recomendada: `react-hook-form` + `zod`.
   - Criar schema por formulario (nao um schema gigante global).

9. Migrar forms por ordem de risco:
   1) `PedidosPage` (mais simples)  
   2) `ColaboradoresPage`  
   3) `PerfilPage`  
   4) `ConfiguracaoPage` (por secoes)

10. Padronizar validacao e erro:
   - Mensagens de erro consistentes.
   - Estados de submit (`isSubmitting`) visiveis.
   - Evitar submit silencioso.

11. Padronizar componentes de campo:
   - Criar componentes de apoio em `components/forms/` apenas para padroes repetidos reais.
   - Evitar abstracao prematura.

---

### Sprint 3 — Decomposicao de paginas e composicao de dominio

12. Refatorar `ConfiguracaoPage.tsx` em blocos:
   - `components/configuracao/ShiftSection.tsx`
   - `components/configuracao/TemplateSection.tsx`
   - `components/configuracao/RotationSection.tsx`
   - `components/configuracao/ExceptionSection.tsx`
   - `components/configuracao/DemandSection.tsx`

13. Extrair hooks por dominio:
   - `hooks/useShifts.ts`
   - `hooks/useTemplate.ts`
   - `hooks/useRotation.ts`
   - `hooks/useExceptions.ts`
   - `hooks/useDemand.ts`

14. Deixar a pagina como orquestradora:
   - Estado global minimo.
   - Regras de negocio locais encapsuladas por secao.

---

### Sprint 4 — Acabamento premium (startup-grade)

15. Trocar classes de status hardcoded por variantes:
   - Exemplo: `CellStatus` em `EscalaPage.tsx` virar variante de `Badge` com `cva`.

16. Introduzir feedback de acao de alto nivel:
   - Toast para sucesso/erro.
   - Confirmacao destrutiva padrao (ja iniciado com `AlertDialog`).

17. Refinar hierarquia visual:
   - Espacamentos, densidade, contraste, ritmo de tipografia.
   - Garantir consistencia entre cards e secoes de pagina.

18. Garantir robustez dark mode:
   - Revisao completa dos estados (`hover`, `focus`, `disabled`, `destructive`).

---

### Sprint 5 — QA, governanca e fechamento

19. Executar validações tecnicas:
   - `cd apps/frontend && npm run build`
   - Testes existentes (quando houver suite frontend expandida)
   - Smoke test manual de todos os CRUDs principais

20. Executar checklist de UX/a11y:
   - Navegacao por teclado.
   - Foco visivel.
   - Labels e controles associados.
   - Estados de erro claros.

21. Publicar doc de governanca visual:
   - Onde cada coisa deve morar:
     - `components/ui/`: primitives shadcn base
     - `components/`: composicoes reutilizaveis
     - `pages/`: orquestracao de tela
   - "Quando criar novo componente vs compor existente".

22. Registrar backlog de melhoria continua:
   - Itens nao criticos ficam explicitamente documentados (sem sumir no contexto).

---

## FASE 5 — AUTOCRITICA E JUSTIFICATIVA

**Auto-critica:**

### 1) Decisao mais critica
- **Decisao:** atacar primeiro composicao/a11y/sistema de form antes de "polimento visual pesado".
- **Por que:** sem base estrutural, visual premium vira maquiagem fragil.

### 2) Alternativa descartada
- **Alternativa:** redesign completo de UI imediato.
- **Por que descartada:** alto custo, baixa previsibilidade, risco de quebra funcional.
- **Quando seria melhor:** se produto estivesse em rebranding completo com equipe dedicada de design system.

### 3) Fragilidades conhecidas
- Migracao de forms em `ConfiguracaoPage` pode ser extensa.
- Alguns ajustes de visual premium exigem rodada de UX real com operador.
- Toast e micro-interacao podem exigir alinhamento de linguagem do produto.

### 4) Debito tecnico
- O debito atual e conhecido e mapeado.
- O plano evita criar debito novo ao institucionalizar checklist e governanca.

---

## FASE 6 — AUDITORIA FINAL

**Auditoria final...**

- **OBJETIVO:** o plano atende o objetivo estrategico?  
  Sim. Prioriza durabilidade da arquitetura de composicao antes de cosmética.

- **RUIDO:** existe residuo de versoes anteriores?  
  Sim, principalmente em telas grandes e padrao manual de formulario. O plano endereca.

- **LIMITES:** quais gaps remanescentes?  
  QA visual profundo e testes automatizados de UX ainda dependem da execucao dos sprints.

- **INTEGRACAO:** integra bem no TODO?  
  Sim. Respeita estrutura atual (`ui/`, `pages/`, API existente) e evolui sem ruptura.

- **MANUTENCAO:** outro dev entende sem explicacao?  
  Sim. Passo a passo por sprint, por arquivo, com criterios de fechamento.

- **FUTURO:** escala com roadmap?  
  Sim. Cria base para multiplas features sem perder consistencia visual/tecnica.

---

## Definition of Done (UI madura)

Para considerar concluido:

- [ ] Todos os formularios com `Label htmlFor` + controle com `id`.
- [ ] Sem `confirm()` nativo em ação destrutiva.
- [ ] Sem hardcoded visual de status que deveria estar em variante/token.
- [ ] Sem pagina monolitica de alta complexidade sem decomposicao.
- [ ] Estado `loading/empty/error/success` explicito nas telas principais.
- [ ] Build frontend passando (`npm run build`).
- [ ] Checklist de composicao e a11y anexado ao fechamento.

---

## Ordem recomendada de execucao real (resumo)

1. A11y e anatomia de composicao  
2. Sistema de formularios  
3. Refatoracao estrutural de `ConfiguracaoPage`  
4. Acabamento premium visual  
5. QA + governanca permanente

Esse e o caminho mais seguro para ficar bonito **e** maduro.

---

## Context Engineering Consolidado

### Composição oficial shadcn (referência prática)

- Card anatomy: `CardHeader` + `CardTitle` + `CardDescription` + `CardAction` + `CardContent` + `CardFooter`.
- Table anatomy: `Table` + `TableHeader`/`TableBody` + `TableCaption` (contexto) + `TableFooter` (resumo/total).
- Dialog anatomy: `DialogTrigger asChild` + `DialogContent` + `DialogHeader` + `DialogFooter`.
- AlertDialog anatomy: `AlertDialog` + `AlertDialogContent` + `AlertDialogAction`/`AlertDialogCancel`.
- asChild pattern: usar para preservar comportamento sem quebrar semântica do elemento final.

Referências-base:
- https://ui.shadcn.com/docs/components/card
- https://ui.shadcn.com/docs/components/table
- https://ui.shadcn.com/docs/components/dialog
- https://ui.shadcn.com/docs/components/alert-dialog
- https://ui.shadcn.com/docs/forms/react-hook-form

Snippet canônico de composição:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Create Project</CardTitle>
    <CardDescription>Deploy your project in one click.</CardDescription>
    <CardAction>
      <Button variant="ghost" size="icon">...</Button>
    </CardAction>
  </CardHeader>
  <CardContent>{/* form/table/content */}</CardContent>
  <CardFooter>{/* ações secundárias */}</CardFooter>
</Card>
```

### Padrão de formulário (produção)

Stack alvo:
- `react-hook-form`
- `zod`
- `@hookform/resolvers/zod`

Contrato mínimo por form:
1. Schema Zod tipado por contexto (não schema monolítico global).
2. `useForm` com `zodResolver(schema)`.
3. Mensagens de erro por campo com texto claro.
4. Estado de submit (`isSubmitting`) explícito.
5. Acessibilidade: `Label htmlFor`, `id`, `aria-invalid` quando aplicável.

Snippet-base:

```tsx
const schema = z.object({
  name: z.string().min(2, "Informe pelo menos 2 caracteres."),
})

type Values = z.infer<typeof schema>

const form = useForm<Values>({
  resolver: zodResolver(schema),
  defaultValues: { name: "" },
})
```

### Checklist visual premium (go/no-go)

- [ ] Hierarquia clara de título/subtítulo/ações.
- [ ] Densidade consistente entre cards e tabelas.
- [ ] Estados vazios orientados à ação.
- [ ] Estados de erro com linguagem consistente.
- [ ] Loading visível em ações assíncronas.
- [ ] Contraste e foco visível em light/dark.
- [ ] Sem hardcoded visual de status de negócio fora de variantes/tokens.
- [ ] Componentes de layout seguindo anatomia oficial shadcn.

---

## Baseline congelado (estado inicial antes da maturidade completa)

### EscalaPage
- Já usa composição sólida de `Card`, `Table`, `Tabs`, `Alertas`.
- Gap: status visual com classes hardcoded (`CellStatus`) em vez de variante/token.
- Gap: datas do período com `label` nativo (a11y inconsistente com padrão global).

### ColaboradoresPage
- Já possui `Label + htmlFor` e `Select` shadcn.
- Gap: formulário ainda manual (sem RHF + Zod).
- Gap: ausência de `CardDescription`/`CardAction` onde agregaria contexto/ação.

### PedidosPage
- Já possui `Label + htmlFor` e `Select` shadcn.
- Gap: formulário manual (sem RHF + Zod).
- Gap: card de criação sem descrição de contexto.

### ConfiguracaoPage
- Possui AlertDialog para ações destrutivas.
- Gap crítico: arquivo monolítico e formulários sem associação completa de labels.
- Gap: forms sem validação sistemática RHF + Zod.

### PerfilPage
- Gap: `Label` sem `htmlFor`.
- Gap: formulário manual e upload sem camada de validação centralizada.

---

## Definition of Done de UI (governança para PR)

Um PR de frontend só fecha quando:
- [ ] Todo campo de formulário tem `Label htmlFor` e controle com `id`.
- [ ] Ações destrutivas usam diálogo de confirmação (sem `confirm()` nativo).
- [ ] Formulários novos/alterados seguem padrão RHF + Zod.
- [ ] Estados `loading`, `empty`, `error` e `success` estão cobertos.
- [ ] Padrões de composição (`Card`, `Table`, `Dialog`, `Tabs`) seguem anatomia oficial.
- [ ] Build frontend passa: `cd apps/frontend && npm run build`.
- [ ] QA visual em light/dark executado na tela alterada.

---

## Auditoria UX/A11y final (checklist executado)

### Escala
- [x] Período com `Label htmlFor` e `Input id`.
- [x] Estado vazio em calendário e feedback de erro padronizado.
- [x] Tabelas com legenda contextual e resumo.
- [x] Navegação por tabs mantida.

### Colaboradores
- [x] Formulário de colaborador com validação Zod + RHF.
- [x] Formulário de setor com validação Zod + RHF.
- [x] Erro global de tela padronizado.
- [x] Tabelas com caption/footer.

### Pedidos
- [x] Form de criação com Zod + RHF.
- [x] Erros de campo explícitos.
- [x] Estado vazio de pendentes padronizado.
- [x] Feedback de ação (aprovar/rejeitar/criar) com toast.

### Configuração
- [x] Labels associados a inputs/selects nas seções principais.
- [x] Confirmações destrutivas com `AlertDialog`.
- [x] Validação de payload com Zod nos formulários de domínio.
- [x] Estrutura de seção extraída para componentes dedicados.

### Perfil
- [x] Formulário com RHF + Zod para nome/tema.
- [x] Feedback de persistência local com estado de erro e toast.
- [x] Composição semântica de card com descrição.

---

## Guia permanente de governança frontend

Onde cada coisa deve morar:
- `components/ui/`: primitives e wrappers base (Button, Table, Card, Form, Toaster).
- `components/forms/`: blocos reutilizáveis de formulário (ações, seção, auxiliares).
- `components/configuracao/`: composição por domínio da tela de configuração.
- `hooks/`: estado e operações de domínio reutilizáveis entre telas.
- `pages/`: orquestração de fluxo de cada tela, sem acoplamento pesado em detalhes internos.

Quando criar vs compor:
- Criar novo primitive em `components/ui` apenas se for padrão transversal.
- Criar em `components/forms` somente após repetição real em 2+ telas.
- Preferir compor `Card/Table/Dialog/Tabs` antes de criar layout custom.
- Toda ação crítica deve expor feedback (`toast`) e erro legível.
- Toda tela nova deve entrar com checklist de a11y e estados (`loading/empty/error/success`).
