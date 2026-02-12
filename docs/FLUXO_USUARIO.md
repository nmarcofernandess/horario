# Fluxo do usuário — EscalaFlow

> Guia do fluxo completo para o usuário final (RH / gestor).

---

## 1. Primeira vez

1. **Rodar o seed** — popular o banco com dados iniciais:
   ```bash
   PYTHONPATH=. python3 scripts/seed.py
   ```

2. **Iniciar o app**:
   ```bash
   streamlit run app.py
   ```

---

## 2. Fluxo principal

### Página inicial (Escala de Trabalho)

1. **Definir período** — na barra lateral, escolher "De" e "Até".
2. **Clicar em "Atualizar escala"** — o sistema gera a escala e valida as regras.
3. **Ver resultado** — tabela com Data, Colaborador, Status, Turno, Carga (min).
4. **Ver alertas** — violações (dias consecutivos, meta semanal) em expander.
5. **Reordenar** (opcional) — arrastar a primeira coluna e clicar em Update.

### Colaboradores

1. **Cadastrar** — expandir "➕ Novo colaborador", preencher Código, Nome, Contrato, Setor.
2. **Reordenar prioridade** — arrastar a coluna Ordem na tabela e clicar em Update.
3. **Editar** — escolher colaborador no select e alterar Nome ou Contrato.

### Setores

1. **Cadastrar** — expandir "➕ Novo setor", preencher Código e Nome.
2. **Visualizar** — tabela com setores cadastrados.

### Pedidos

1. **Colaborador** — aba "Novo pedido": escolher colaborador, data, tipo (Folga na data, Troca de turno, Evitar domingo) e enviar.
2. **RH** — aba "Pendentes (RH)": aprovar ou rejeitar cada pedido.
3. **Histórico** — ver pedidos já decididos.

### Configuração

1. **Turnos** — ver/editar códigos e duração.
2. **Mosaico semanal** — quem trabalha em qual dia (seg–sáb).
3. **Rodízio de domingos** — quem trabalha em cada domingo e quando folga.
4. **Simular** — testar período sem atualizar a escala principal.

---

## 3. Termos para o usuário

| Técnico        | Usuário final      |
|----------------|--------------------|
| employee_id    | Colaborador (nome) |
| WORK / FOLGA   | Trabalho / Folga   |
| CAI1, CAI2...  | Manhã (9h30), etc. |
| R1_MAX_CONSECUTIVE | Dias consecutivos (máx. 6) |
| R4_WEEKLY_TARGET   | Meta semanal de horas |
| CRITICAL / HIGH    | Crítico / Alto     |

---

## 4. Integração de pedidos

Pedidos **aprovados** do tipo "Folga na data" são aplicados automaticamente na próxima geração da escala. O RH deve aprovar antes de clicar em "Atualizar escala".
