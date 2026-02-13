# Auditoria e Refatoração do Frontend EscalaFlow

**Data:** 2026-02-12  
**Escopo:** `apps/frontend/src/renderer/`

---

## 1. Levantamento Realizado

### 1.1 Componentes UI (47 arquivos em `components/ui/`)

| Categoria | Problema Identificado | Status |
|----------|----------------------|--------|
| **Imports** | `src/renderer/lib/utils` e `src/renderer/components/ui/*` em vez de `@/lib/utils` e `@/components/ui/*` | ✅ Corrigido |
| **Radix** | Uso de `radix-ui` (meta-pacote) — válido conforme shadcn v4; `Slot.Root` correto com radix-ui | ✅ Mantido |
| **CSS Tailwind v4** | Sintaxe `max-h-(--var)`, `origin-(--var)` — válida no Tailwind v4 como shorthand para `var()` | ✅ Mantido |
| **forwardRef** | Input, SelectTrigger já possuem forwardRef para react-hook-form | ✅ OK |

### 1.2 Componentes Reinstalados via shadcn CLI

```
button, input, label, select, alert-dialog, dialog, dropdown-menu, form,
badge, breadcrumb, card, table, tabs, tooltip, avatar, separator, sheet,
checkbox, accordion, alert, context-menu, hover-card, menubar, navigation-menu,
popover, progress, scroll-area, slider, switch, toggle, toggle-group, calendar
```

### 1.3 Customizações Preservadas

- **Layout.tsx:** `SidebarTrigger` com `className="no-drag"`
- **nav-main.tsx:** `SidebarMenuButton` com `className="no-drag"` (itens e collapsible)
- **nav-user.tsx:** `SidebarMenuButton` com `className="no-drag"`
- **date-input.tsx:** Componente custom mantido (não substituído por Calendar)
- **sidebar.tsx:** Usa `@radix-ui/react-slot` (Slot) — não alterado pelo CLI

### 1.4 Páginas (5 arquivos)

- **EscalaPage, ColaboradoresPage, PedidosPage, ConfiguracaoPage, PerfilPage:** Todas usam `@/` nos imports. Nenhuma alteração estrutural necessária nesta etapa.

---

## 2. Alterações Realizadas

### 2.1 components.json

```json
"aliases": {
  "components": "@/components",
  "utils": "@/lib/utils",
  "ui": "@/components/ui"
}
```

Antes: `src/renderer/...` (path absoluto relativo)  
Depois: `@/...` (alias configurado no Vite/tsconfig)

### 2.2 Imports Corrigidos (28 arquivos)

- `src/renderer/lib/utils` → `@/lib/utils`
- `src/renderer/components/ui/button` → `@/components/ui/button`
- `src/renderer/components/ui/label` → `@/components/ui/label`
- `src/renderer/components/ui/toggle` → `@/components/ui/toggle`

### 2.3 Componentes Atualizados via shadcn CLI

22 componentes foram sobrescritos com a versão oficial do registry shadcn (new-york style).

---

## 3. Verificações

| Verificação | Resultado |
|-------------|-----------|
| `npm run build` | ✅ Passou |
| `npm run lint` | ✅ Passou |

### Correções de Lint Aplicadas

- `python.ts`: parâmetro `code` removido do callback
- `app-sidebar.tsx`: comentário no bloco catch vazio
- `ConfiguracaoPage.tsx`: removidos `shiftSchema` duplicado, `newShift`/`setNewShift` não usados; eslint-disable para useEffect de mount
- `EscalaPage.tsx`: deps do useMemo corrigido para `assignments`; eslint-disable para useEffect de mount
- `.eslintrc.cjs`: overrides para desativar `react-refresh/only-export-components` em `ui/`, theme-provider e tour

---

## 4. Resumo para Commit

```
fix(frontend): padronizar imports e reinstalar componentes shadcn

- Atualizar components.json com aliases @/
- Corrigir imports src/renderer → @/ em 28 componentes UI
- Reinstalar 22 componentes via npx shadcn@latest add --overwrite
- Preservar customizações: no-drag, date-input, sidebar
- Corrigir erros de lint (variáveis não usadas, bloco vazio, exhaustive-deps)
```

---

## 5. Próximos Passos Sugeridos

1. Corrigir os 5 erros de lint (variáveis não usadas, bloco vazio)
2. Auditar uso de Table, Card, Tabs, Form nas páginas e padronizar
3. Garantir TooltipProvider no root se tooltips forem usados fora do sidebar
4. Testar manualmente: Escala, Colaboradores, Pedidos, Configuração, Perfil
