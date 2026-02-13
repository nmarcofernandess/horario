# Prompt: Levantamento e Refatoração Completa do Frontend EscalaFlow

**Copie o conteúdo abaixo e use em um novo chat com uma IA (Agent mode).**

---

## Contexto

Projeto **EscalaFlow** — sistema de escalas de trabalho (Electron + React + Vite + shadcn/ui). Stack: `apps/frontend` com `src/renderer/` como raiz do React. Alias `@/` → `src/renderer/*`.

O frontend foi construído com componentes shadcn, mas muitos foram **alterados manualmente** em vez de instalados via CLI. Isso gerou inconsistências:

- Imports de `radix-ui` (meta-pacote) em vez de `@radix-ui/react-*` (pacotes específicos)
- Uso incorreto de `Slot.Root` onde deveria ser `Slot` (do `@radix-ui/react-slot`)
- CSS Tailwind inválido: `max-h-(--radix-...)` em vez de `max-h-[var(--radix-...)]`
- Componentes sem `forwardRef` onde necessário (ex.: Input para react-hook-form)
- Imports inconsistentes: `src/renderer/...` em vez de `@/...`

## O que preciso

### 1. Levantamento completo

Faça um **audit** de todo o frontend:

- **`apps/frontend/src/renderer/components/ui/`** — todos os componentes shadcn (47 arquivos)
- **`apps/frontend/src/renderer/pages/`** — EscalaPage, ColaboradoresPage, PedidosPage, ConfiguracaoPage, PerfilPage
- **`apps/frontend/src/renderer/components/`** — Layout, app-sidebar, nav-main, nav-user, configuracao/*, forms/*, feedback-state, tour, etc.

Para cada arquivo, identifique:

- Desvios do padrão shadcn oficial (imports, Slot vs Slot.Root, CSS `var()`)
- Uso incorreto de Table, Card, Tabs, Form, etc.
- Componentes que precisam de `forwardRef` e não têm
- Imports que devem usar `@/` e usam path absoluto

### 2. Refatoração

**Regra de ouro:** usar o CLI do shadcn para trazer o código oficial. Não inventar.

1. **Reinstalar componentes UI via CLI:**
   ```bash
   cd apps/frontend
   npx shadcn@latest add button input label select alert-dialog dialog dropdown-menu form badge breadcrumb card table tabs tooltip avatar separator sheet checkbox collapsible --overwrite
   ```
   (e os demais que existirem em `components/ui/`)

2. **Corrigir `components.json`** se necessário — aliases devem apontar para `src/renderer/components` e `src/renderer/lib/utils`.

3. **Padronizar uso nas páginas:**
   - **Table:** usar `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableCaption`, `TableHead` conforme shadcn; empty states e loading consistentes
   - **Card:** usar `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`, `CardAction` se existir
   - **Tabs:** usar `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` do Radix (não contexto customizado)
   - **Form:** usar `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` com react-hook-form + zod
   - **DateInput:** manter componente custom se existir, ou trocar por `Calendar`/`react-day-picker` do shadcn

4. **Corrigir imports:** tudo via `@/components/ui/...` e `@/lib/utils`, nunca `src/renderer/...`.

5. **Garantir:** Input, Select e outros usados por `FormControl` com `forwardRef` para react-hook-form.

### 3. Verificações finais

- `npm run build` sem erros
- `npm run lint` sem erros
- Páginas: Escala, Colaboradores, Pedidos, Configuração, Perfil funcionando
- Tabs (sidebar e internas) respondendo a cliques
- Tema dark/light funcionando

## Documentação de referência

- `docs/SISTEMA_ESCALAFLOW.md` — fluxo geral
- `.cursor/rules/agent.mdc` — regras do projeto
- `apps/frontend/components.json` — configuração atual do shadcn

## Estrutura do frontend

```
apps/frontend/src/renderer/
├── components/
│   ├── ui/           # 47 componentes shadcn
│   ├── configuracao/ # DemandSection, ExceptionSection, etc.
│   ├── forms/        # FormActions, FormSection
│   ├── Layout.tsx, app-sidebar.tsx, nav-main.tsx, nav-user.tsx
│   └── feedback-state.tsx, tour.tsx, tour-setup.tsx
├── pages/            # EscalaPage, ColaboradoresPage, PedidosPage, ConfiguracaoPage, PerfilPage
├── hooks/            # useShifts, useTemplate, useRotation, etc.
└── lib/              # api.ts, format.ts, utils.ts
```

## Entregáveis esperados

1. Lista de arquivos auditados e problemas encontrados
2. Código refatorado (componentes UI + páginas que os usam)
3. Confirmação de build e lint passando
4. Resumo das alterações para commit
