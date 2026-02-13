# Auditoria do Código Frontend EscalaFlow

**Data:** 2026-02-12  
**Escopo:** páginas, componentes, hooks, lib

---

## 1. Resumo Executivo

| Área | Status | Problemas |
|------|--------|-----------|
| Páginas | ⚠️ | Inconsistências, TabsContent duplicado |
| Componentes UI | ✅ Corrigido | Input sem forwardRef (corrigido) |
| Formulários | ⚠️ | Uso misto FormSection, Select defaultValue+value |
| Configuracao/* | ⚠️ | TabsContent redundante nas sections |

---

## 2. Páginas Auditadas

### 2.1 EscalaPage.tsx — ~770 linhas

**Uso correto:**
- Card, Table, Tabs, Badge, Button, Input, DateInput, AlertDialog
- EmptyState, ErrorState
- Form (não usa; usa estado local)
- `@/` em todos os imports

**Problemas:**
- Componente muito grande; poderia extrair hooks (useEscalaData, usePreflight) e subcomponentes
- useMemo com `[assignments]` — ok após correção

### 2.2 ColaboradoresPage.tsx — ~307 linhas

**Uso correto:**
- Tabs, Card, Table, Form, FormField, FormItem, FormSection, FormLabel, FormControl, FormMessage
- Select com FormControl
- Input em FormControl

**Problemas:**
- `FormSection` é wrapper extra; FormItem do shadcn já tem layout — redundante mas não quebra
- `useEffect` sem deps no load — intencional (mount)

### 2.3 PedidosPage.tsx — ~210 linhas

**Uso correto:**
- Tabs, Card, Form, DateInput, Select
- EmptyState para lista vazia

**Problemas:**
- Nenhum crítico

### 2.4 PerfilPage.tsx — ~195 linhas

**Uso correto:**
- Card, Form, Avatar, Input, Select
- useTheme, FormActions

**Problemas:**
- `useEffect` com `[perfil, theme, form]` — `form` pode causar loop; `form.reset` é estável

### 2.5 ConfiguracaoPage.tsx — ~1540 linhas

**Problemas críticos:**
1. **TabsContent duplicado:** A página usa `<TabsContent value="turnos"><ShiftSection>...</ShiftSection></TabsContent>` e `ShiftSection` retorna `<TabsContent value="turnos">{children}</TabsContent>`. Resultado: TabsContent aninhado com o mesmo value — redundante.
2. **Mesma situação** para TemplateSection, RotationSection, ExceptionSection, DemandSection: cada um envolve em TabsContent, e a página já envolve em TabsContent.
3. **Select:** `defaultValue={field.value}` e `value={field.value}` — em controlled, usar apenas `value`.
4. **FormStructure inconsistente:** turnos usa FormItem direto; Colaboradores usa FormItem + FormSection.

**Sugestão:** Remover o TabsContent da página e deixar as sections fornecerem, OU remover o TabsContent das sections e usar só o da página.

---

## 3. Componentes Auditados

### 3.1 Input (crítico)

**Problema:** O shadcn reinstalou removendo `forwardRef`. O react-hook-form passa `ref` via FormControl → componente filho. Sem forwardRef, o ref não chega ao `<input>` nativo.

**Correção aplicada:** Restaurado `React.forwardRef` no Input.

### 3.2 DateInput

**Status:** Usa Input com `ref={innerRef}`. Com Input corrigido, passa a funcionar.

### 3.3 FormSection

**Função:** Wrapper `<div className="space-y-2">` em volta de FormLabel + FormControl.

**Uso:** Colaboradores, Pedidos, Perfil usam. Configuracao (turnos) não usa — layout inline com `flex flex-wrap`.

**Conclusão:** Não é problema; é escolha de layout. FormSection dá layout vertical; Configuracao usa horizontal.

### 3.4 configuracao/* (ShiftSection, TemplateSection, etc.)

**Problema:** Cada section retorna `<TabsContent value="X">{children}</TabsContent>`. A página já envolve em `<TabsContent value="X">`. Duplicação.

**Opções:**
- A) Remover TabsContent das sections; sections viram só wrappers de layout.
- B) Remover TabsContent da página; deixar só as sections como filhos diretos do Tabs.

---

## 4. Padrões Identificados

| Padrão | Páginas | Observação |
|--------|---------|------------|
| Form + zod + zodResolver | Todas com form | ✅ Consistente |
| Table com TableCaption, empty state | Escala, Colaboradores, Configuracao | ✅ Consistente |
| Card com CardHeader, CardTitle, CardDescription, CardContent | Todas | ✅ Consistente |
| Tabs com TabsList, TabsTrigger, TabsContent | Todas com tabs | ✅ Consistente |
| FormSection | Colaboradores, Pedidos, Perfil | Configuracao não usa |
| Select em FormControl | Colaboradores, Pedidos, Perfil, Configuracao | ⚠️ Configuracao usa defaultValue+value |

---

## 5. Correções Aplicadas

1. **Input:** Restaurado `forwardRef` para react-hook-form.
2. **(Pendente)** ConfiguracaoPage: simplificar TabsContent e Select.

---

## 6. Próximos Passos Recomendados

1. Remover TabsContent duplicado em ConfiguracaoPage (page ou sections).
2. Padronizar Select: usar apenas `value` e `onValueChange` em formulários controlados.
3. Extrair lógica pesada de EscalaPage e ConfiguracaoPage para hooks customizados.
4. ColaboradoresPage: useEffect com eslint-disable ou incluir load nas deps (com useCallback).
