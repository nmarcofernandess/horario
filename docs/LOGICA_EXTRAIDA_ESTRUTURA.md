# Logica Extraida dos Arquivos (Base Streamlit)

## 1) O que cada arquivo representa
- `/Users/marcofernandes/horario/data/raw/Horario de trabalho padrao NOVO -2026 - REVISAO DE ESCALA.xlsx`: planilha mestra de escalas por setor; a aba `CAIXAS -2026- ESC` contem os turnos CAI e tambem o quadro de domingo/folga na faixa `AP:BE`.
- `/Users/marcofernandes/horario/data/raw/DOM E FOLGAS - CAIXA.xlsx`: matriz compacta de semanas com marcadores numericos (`5` e `6`) por colaborador.
- `/Users/marcofernandes/horario/data/raw/escala caixa - rita 1.pdf`: grade de turnos de segunda a sabado em janelas de 30 minutos (08:00 a 19:30) com totais diarios por colaborador.
- `/Users/marcofernandes/horario/data/raw/escala caixa - rita.pdf`: rodizio de domingos (8 escalas por bloco) + data de folga compensatoria de cada pessoa.
- `/Users/marcofernandes/horario/docs/PRD_SPEC_Escala_Caixa_Secullum.md`: regras de negocio do problema (R1/R2/R3) e alvo funcional para o app.

## 2) Logica inferida de quem montou a escala
- Segunda a sabado: horarios fixos por codigo (`CAI1`...`CAI6`) sem alteracao estrutural.
- Domingo: escalado em rodizio, com 3 pessoas por domingo na maior parte dos casos.
- Cada pessoa que trabalha no domingo recebe uma data de folga associada (compensacao), registrada no mesmo bloco.
- A planilha `DOM E FOLGAS` parece funcionar como resumo semanal dos marcadores de turno/compensacao por colaborador.
- A aba `CAIXAS -2026- ESC` replica os mesmos dados de rodizio de domingo que aparecem no PDF de domingo.

## 3) Evidencias extraidas
- Marcadores `DOM E FOLGAS`: 100 marcadores nao vazios em 726 celulas de matriz.
- Turnos detectados no PDF de grade: CAI1, CAI2, CAI3, CAI4, CAI5, CAI6.
- Linhas de slots (30 min) extraidas: 428.
- Rodizio de domingo (PDF): 72 linhas, 24 domingos.
- Rodizio de domingo (XLSX/CAIXAS): 72 linhas deduplicadas.
- Interseccao PDF x XLSX: 72 registros iguais (72 PDF vs 72 XLSX).

## 4) Artefatos prontos para o Streamlit
- `data/processed/dom_folgas_matrix.csv`: grade completa (inclui vazios).
- `data/processed/dom_folgas_markers.csv`: somente marcadores preenchidos.
- `data/processed/pdf_rita1_slots.csv`: slots de 30 min por colaborador.
- `data/processed/pdf_rita1_totals.csv`: total diario por colaborador.
- `data/processed/pdf_rita1_shift_catalog_by_day.csv`: duracao por codigo/dia.
- `data/processed/pdf_rita_sunday_rotation.csv`: domingo + folga (fonte PDF).
- `data/processed/xlsx_caixas_sunday_rotation.csv`: domingo + folga (fonte XLSX).
- `data/processed/sunday_rotation_source_compare.json`: divergencias entre fontes.
- `data/processed/excel_raw/*`: export bruto de todas as abas em CSV.

## 5) Pontos que ainda exigem decisao de produto
- O significado exato dos marcadores `5` e `6` deve ser confirmado (turno, dia de folga ou outro codigo operacional).
- Qual corte oficial de apuracao semanal sera usado no app (`MON_SUN` ou `SUN_SAT`).
- Se o app deve apenas validar/corrigir uma escala existente ou gerar escala nova automaticamente.
