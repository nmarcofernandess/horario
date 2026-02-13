# Padrão de espaçamento em Cards

**Referência visual:** Card "Novo colaborador" (ColaboradoresPage).

## Token de espaçamento

| Token | Valor | Uso |
|-------|-------|-----|
| `gap-2` / `space-y-2` | 8px | Label ↔ input (FormItem, FormSection) |
| `gap-4` / `space-y-4` | 16px | Campos relacionados (grid de inputs, botões na mesma linha) |
| `gap-6` / `space-y-6` | 24px | Seções principais (header↔content, entre blocos) |

## Card (shadcn)

- **Card:** `py-6` + `gap-6` entre filhos (Header, Content, Footer)
- **CardHeader:** `px-6`, `gap-2` (título ↔ descrição)
- **CardContent:** `px-6` — sem padding vertical
- **CardFooter:** `px-6`, `[.border-t]:pt-6`

O `gap-6` do Card cria 24px entre Header e Content, e entre Content e Footer.

## Cards customizados (ex.: Aderência colapsável)

Para manter consistência com o Card padrão:

- **Trigger/header:** `px-6 py-6` (igual ao padding do Card)
- **Conteúdo:** `pt-6 pb-6` após o separador, `gap-6` entre seções
- **Dentro de seções:** `gap-4` para elementos relacionados

## Formulários

- Form com `grid gap-4` — 16px entre campos
- FormItem / FormSection com `space-y-2` — 8px entre label e input
