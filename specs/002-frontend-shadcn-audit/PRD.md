# PRD: Ajustar e Otimizar Layout Frontend (shadcn)

> **Workflow:** refactor
> **Criado em:** 2026-02-12
> **Fonte:** discovery 002-frontend-shadcn-audit

---

## Visão Geral

Implementar os ajustes e melhorias identificados no discovery para alinhar o frontend EscalaFlow aos padrões shadcn/ui, otimizando layout, acessibilidade e congruência de componentes.

---

## Requisitos Funcionais

- [ ] Unificar Slot: button, badge, breadcrumb, sidebar usam @radix-ui/react-slot + Slot (não Slot.Root)
- [ ] Corrigir BreadcrumbLink: Layout usa href="#" + onClick — usar asChild + Button ou role="button"
- [ ] Substituir select nativo por shadcn Select em ColaboradoresPage (contrato, setor)
- [ ] Substituir select nativo por shadcn Select em PedidosPage (tipo pedido)
- [ ] Usar Label + htmlFor em forms de ColaboradoresPage e PedidosPage
- [ ] Usar CardDescription onde descrição é <p> solto em CardHeader
- [ ] CellStatus (EscalaPage) usar cn() em vez de array.join()
- [ ] Tab Calendário (EscalaPage) usar componentes Table shadcn
- [ ] Substituir confirm() por AlertDialog em ConfiguracaoPage (4+ lugares)
- [ ] Remover CSS boilerplate não usado em App.css
- [ ] Remover @layer base duplicado em index.css

---

## Critérios de Aceitação

- [ ] Nenhum import de radix-ui para Slot; todos usam @radix-ui/react-slot
- [ ] BreadcrumbLink não usa href="#" com preventDefault
- [ ] Colaboradores e Pedidos usam Select, Label com htmlFor
- [ ] ConfiguracaoPage usa AlertDialog para confirmações destrutivas
- [ ] App.css sem .logo, .card; index.css sem @layer base duplicado
- [ ] npm run build passa; app abre e navega sem erros

---

## Constraints

- Seguir princípio de congruência: app nunca importa Radix; só @/components/ui/*
- Mudanças sem impacto de lógica preferidas
- Manter comportamento funcional idêntico

---

## Fora do Escopo

- react-hook-form + zod (forms com validação)
- Redesign visual completo
- Novas features

---

## Serviços Envolvidos

- [x] Frontend (apps/frontend)

---

## Notas Adicionais

- AlertDialog já existe em ui/alert-dialog.tsx
- ConfiguracaoPage usa confirm() em: clearTemplateAll, handleDeleteShift, handleDeleteException, handleDeleteDemand, handleDeleteRotation
