import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.policy_loader import PolicyLoader
from src.domain.models import ProjectionContext
from src.application.use_cases import ValidationOrchestrator
from src.application.ui.display import humanize_df_scale, humanize_df_violations

st.set_page_config(
    page_title="EscalaFlow",
    layout="wide",
    page_icon="📋",
    initial_sidebar_state="expanded",
)

# CSS para aparência de app de gestão
st.markdown("""
<style>
    /* Título principal */
    div[data-testid="stAppViewContainer"] h1 {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1e3a5f;
    }
    /* Cards/containers */
    .stDataFrame { border-radius: 8px; }
    div[data-testid="stVerticalBlock"] > div { padding: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

init_db()
if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()

repo = SqlAlchemyRepository(st.session_state["db_session"])
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "processed" / "real_scale_cycle"
POLICY_PATH = ROOT / "schemas" / "compliance_policy.example.json"

# Sidebar
with st.sidebar:
    st.title("📋 EscalaFlow")
    st.markdown("**Gestão de escala de trabalho**")
    st.divider()
    st.subheader("Período")
    period_start = st.date_input("De", date(2026, 2, 8))
    period_end = st.date_input("Até", date(2026, 3, 31))
    st.divider()
    st.caption("Colaboradores, Pedidos e Configuração no menu superior.")

# Main
st.title("Escala de Trabalho")
st.markdown("Visualize e valide a escala para o período selecionado.")

# Botão de ação principal
if st.button("Atualizar escala", type="primary"):
    with st.spinner("Gerando escala..."):
        policy_loader = PolicyLoader(schemas_path=ROOT / "schemas")
        orchestrator = ValidationOrchestrator(
            repo=repo,
            policy_loader=policy_loader,
            output_path=OUTPUT,
            data_dir=ROOT / "data" / "fixtures",
        )
        context = ProjectionContext(
            period_start=period_start,
            period_end=period_end,
            sector_id="CAIXA",
            anchor_scale_id=1,
        )
        try:
            if "escala_reordenada" in st.session_state:
                del st.session_state["escala_reordenada"]
            result = orchestrator.run(context, POLICY_PATH)
            msg = f"Escala gerada: **{result['assignments_count']}** alocações, **{result['violations_count']}** alertas."
            if result.get("exceptions_applied", 0) > 0:
                msg += f" **{result['exceptions_applied']}** exceções aplicadas."
            st.success(msg)
            st.rerun()
        except ValueError as e:
            st.warning(str(e))
            st.info("Execute `PYTHONPATH=. python scripts/seed.py` para popular o banco.")
        except Exception as e:
            st.error(f"Erro: {e}")
            with st.expander("Detalhes técnicos"):
                import traceback
                st.code(traceback.format_exc())

# Export HTML/Markdown
if OUTPUT.exists() and (OUTPUT / "escala_calendario.html").exists():
    with st.expander("📄 Exportar escala (calendário)", expanded=False):
        html_path = OUTPUT / "escala_calendario.html"
        md_path = OUTPUT / "escala_calendario.md"
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                st.download_button("⬇️ Baixar HTML (imprimir/colar parede)", f.read(), file_name="escala_calendario.html", mime="text/html", key="dl_html")
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as f:
                st.download_button("⬇️ Baixar Markdown", f.read(), file_name="escala_calendario.md", mime="text/markdown", key="dl_md")

# Exibir escala (com labels humanizados)
if OUTPUT.exists() and (OUTPUT / "final_assignments.csv").exists():
    try:
        df_raw = pd.read_csv(OUTPUT / "final_assignments.csv")
        emp_map = {e.employee_id: e.name for e in repo.load_employees().values()}
        df = humanize_df_scale(df_raw, emp_map)

        # Ordem preferida para o RH
        ordem = ["Data", "Colaborador", "Status", "Turno", "Carga (min)"]
        cols = [c for c in ordem if c in df.columns]
        if cols:
            df = df[cols]

        st.subheader("Escala gerada")
        if HAS_AGGRID:
            df_display = st.session_state.get("escala_reordenada")
            if df_display is None or len(df_display) != len(df):
                df_display = df.copy()
                st.session_state["escala_reordenada"] = df_display

            gb = GridOptionsBuilder.from_dataframe(df_display)
            gb.configure_grid_options(
                rowDragManaged=True,
                animateRows=True,
                suppressRowClickSelection=True,
            )
            gb.configure_column(df_display.columns[0], rowDrag=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                df_display,
                grid_options=grid_options,
                fit_columns_on_grid_load=True,
                height=400,
                update_mode=GridUpdateMode.MANUAL,
                data_return_mode=DataReturnMode.AS_INPUT,
            )

            if grid_response and grid_response.get("data"):
                new_df = pd.DataFrame(grid_response["data"])
                if len(new_df) == len(df_display):
                    st.session_state["escala_reordenada"] = new_df
                    st.rerun()

            st.caption("Arraste a primeira coluna para reordenar, depois clique em Update para aplicar.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

        # Violações
        vio_path = OUTPUT / "violations.csv"
        if vio_path.exists():
            df_vio = pd.read_csv(vio_path)
            if len(df_vio) > 0:
                df_vio = humanize_df_violations(df_vio, emp_map)
                with st.expander(f"⚠️ Alertas de regras ({len(df_vio)})", expanded=False):
                    st.dataframe(df_vio, width="stretch", hide_index=True)
            else:
                st.success("Nenhum alerta de regras.")

    except Exception as e:
        st.warning(f"Não foi possível carregar a escala: {e}")
