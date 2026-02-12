import streamlit as st
import pandas as pd
from pathlib import Path

from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.policy_loader import PolicyLoader
from src.domain.models import ProjectionContext
from src.application.use_cases import ValidationOrchestrator
from datetime import date

st.set_page_config(page_title="Escala Caixa - Compliance", layout="wide", page_icon="📅")

# Ensure DB Tables exist
init_db()

if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()

repo = SqlAlchemyRepository(st.session_state["db_session"])
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "processed" / "real_scale_cycle"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"

# Sidebar
st.sidebar.title("📅 Escala Caixa")
st.sidebar.markdown("**Validação de Compliance**")
st.sidebar.divider()

st.sidebar.header("Parâmetros")
sector_id = st.sidebar.selectbox("Setor", ["CAIXA"], help="Setor alvo da validação")
period_start = st.sidebar.date_input("Início", date(2026, 2, 8))
period_end = st.sidebar.date_input("Fim", date(2026, 3, 31))

st.sidebar.divider()
st.sidebar.caption("Use o menu **Pages** para Cadastros, Pedidos e Regras.")

# Main
st.title("Validação de Escala")
st.markdown("Execute a validação de compliance para o período selecionado.")

if st.button("Rodar Validação", type="primary"):
    with st.spinner("Processando..."):
        policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
        orchestrator = ValidationOrchestrator(
            repo=repo,
            policy_loader=policy_loader,
            output_path=OUTPUT,
            data_dir=ROOT / "data" / "processed"
        )
        context = ProjectionContext(
            period_start=period_start,
            period_end=period_end,
            sector_id=sector_id,
            anchor_scale_id=1
        )
        try:
            result = orchestrator.run(context, POLICY_PATH)
            st.success(f"Validação concluída: {result['assignments_count']} alocações, {result['violations_count']} violações.")

            tab1, tab2, tab3 = st.tabs(["Escala Final", "Decisões RH", "Violações"])
            with tab1:
                df_assign = pd.read_csv(OUTPUT / "final_assignments.csv")
                st.dataframe(df_assign, use_container_width=True, hide_index=True)
            with tab2:
                df_dec = pd.read_csv(OUTPUT / "preference_decisions.csv")
                if len(df_dec) > 0:
                    st.dataframe(df_dec, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma decisão de pedido registrada.")
            with tab3:
                df_vio = pd.read_csv(OUTPUT / "violations.csv")
                if len(df_vio) > 0:
                    st.dataframe(df_vio, use_container_width=True, hide_index=True)
                else:
                    st.success("Nenhuma violação encontrada.")

        except ValueError as e:
            st.warning(str(e))
            st.info("💡 Dica: Execute `python scripts/seed_db_from_csv.py` para popular o banco com dados de exemplo.")
        except Exception as e:
            st.error(f"Erro: {e}")
            with st.expander("Detalhes técnicos"):
                import traceback
                st.code(traceback.format_exc())

# Mostrar última execução se existir
if OUTPUT.exists() and (OUTPUT / "final_assignments.csv").exists():
    st.divider()
    st.subheader("Última execução")
    try:
        df_last = pd.read_csv(OUTPUT / "final_assignments.csv")
        st.dataframe(df_last.head(20), use_container_width=True, hide_index=True)
        if len(df_last) > 20:
            st.caption(f"Exibindo 20 de {len(df_last)} registros.")
    except Exception:
        pass

st.caption("Sistema de Compliance de Escalas — Escala Caixa")
