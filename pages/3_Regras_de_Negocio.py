
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter
from src.domain.engines import CycleGenerator, PolicyEngine
from src.domain.models import Shift, ProjectionContext, ShiftDayScope

# DB Setup
init_db()
if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()

repo = SqlAlchemyRepository(st.session_state["db_session"])
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
importer = LegacyCSVImporter(DATA_DIR)

st.set_page_config(page_title="Regras de Negócio", layout="wide", page_icon="⚙️")

st.title("⚙️ Regras de Negócio e Configuração")
st.markdown("""
Para construir escalas **do zero** sem depender de seeds hardcoded, o sistema precisa destas 4 Definições Fundamentais.
Aqui você pode visualizar e editar as regras que antes estavam escondidas em arquivos CSV.
""")

importer = LegacyCSVImporter(DATA_DIR)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧩 Catálogo de Turnos", 
    "📅 Mosaico Base (Padrão)", 
    "🎡 Ciclos de Domingo",
    "🚫 Matriz de Folgas",
    "🚀 Simulador"
])

with tab1:
    st.header("Catálogo de Turnos (Shift Definitions)")
    st.markdown("Definição do que cada código de turno significa em termos de horário e validade.")
    
    # Load from DB
    shifts_dict = repo.load_shifts()
    if not shifts_dict:
        # Fallback to CSV if DB empty
        df_shifts = importer.load_shift_catalog()
        if not df_shifts.empty:
            df_shifts = df_shifts.drop_duplicates("shift_code").copy()
            if "day_scope" not in df_shifts.columns:
                df_shifts["day_scope"] = "WEEKDAY"
    else:
        # Convert dict to DF for display
        df_shifts = pd.DataFrame([
            {"shift_code": s.code, "minutes_median": s.minutes, "day_scope": s.day_scope.value} 
            for s in shifts_dict.values()
        ])

    if not df_shifts.empty:
        edited_shifts = st.data_editor(
            df_shifts, 
            num_rows="dynamic",
            key="editor_shifts",
            use_container_width=True
        )
        if st.button("💾 Salvar Definições de Turno", key="btn_save_shifts"):
            repo.save_shifts(edited_shifts)
            st.success("Definições de turno salvas no Banco de Dados! ✅")
            st.rerun()
    else:
        st.warning("Nenhum turno cadastrado.")

with tab2:
    st.header("Mosaico Base (Standard Slots)")
    st.markdown("A estrutura padrão da escala semanal. Quem assume qual posto em dias normais?")
    
    # Load from DB
    df_slots = repo.load_weekday_template_data()
    if df_slots.empty:
        df_slots = importer.load_base_slots()
        # Rename legacy to matching DB columns if needed
        if "day_name" not in df_slots.columns and "day_key" in df_slots.columns:
            df_slots = df_slots.rename(columns={"day_key": "day_name"})
        if "day_name" in df_slots.columns:
            # Standardize column naming for the editor
            pass

    if not df_slots.empty:
        # Ensure we have common columns
        if "day_name" not in df_slots.columns and "day_key" in df_slots.columns:
            df_slots = df_slots.rename(columns={"day_key": "day_name"})
            
        day_filter = st.selectbox("Filtrar por Dia da Semana", ["TODOS"] + sorted(df_slots['day_name'].unique().tolist()))
        df_display = df_slots if day_filter == "TODOS" else df_slots[df_slots['day_name'] == day_filter]
            
        edited_slots = st.data_editor(
            df_display,
            key="editor_slots",
            use_container_width=True,
            num_rows="dynamic"
        )
        if st.button("💾 Salvar Mosaico Base", key="btn_save_slots"):
            repo.save_weekday_template(edited_slots)
            st.success("Mosaico base salvo no Banco de Dados! ✅")
            st.rerun()
    else:
        st.warning("Nenhum mosaico cadastrado.")

with tab3:
    st.header("Ciclos de Domingo (Rotation Rules)")
    st.markdown("Regras de quem trabalha no domingo e quando tira a folga compensatória.")
    
    df_rotation = repo.load_sunday_rotation()
    if df_rotation.empty:
        df_rotation = importer.load_sunday_rotation()
        
    if not df_rotation.empty:
        # Sort by date for better view
        if 'sunday_date' in df_rotation.columns:
            df_rotation['sunday_date'] = pd.to_datetime(df_rotation['sunday_date'], errors='coerce')
        if 'folga_date' in df_rotation.columns:
            df_rotation['folga_date'] = pd.to_datetime(df_rotation['folga_date'], errors='coerce')
            
        df_rotation = df_rotation.sort_values('sunday_date')
            
        edited_rotation = st.data_editor(
            df_rotation,
            key="editor_rotation",
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "sunday_date": st.column_config.DateColumn("Domingo Trabalhado"),
                "folga_date": st.column_config.DateColumn("Folga Compensatória")
            }
        )
        if st.button("💾 Salvar Ciclo de Domingos", key="btn_save_rotation"):
            repo.save_sunday_rotation(edited_rotation)
            st.success("Ciclo de domingos salvo no Banco de Dados! ✅")
            st.rerun()
    else:
        st.warning("Nenhuma regra de domingo cadastrada.")

with tab4:
    st.header("Matriz de Folgas (Constraints)")
    st.markdown("A matriz resultante de folgas e restrições geradas.")
    
    df_folgas = importer.load_day_off_matrix()
    if not df_folgas.empty:
        st.dataframe(df_folgas, use_container_width=True)
        st.caption("Esta matriz geralmente é gerada pelo motor, mas pode servir de input para regras fixas.")
    else:
        st.info("Nenhuma matriz de folgas carregada.")

with tab5:
    st.header("Simulador de Geração")
    st.markdown("Teste as regras configuradas acima gerando uma escala real.")
    
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Início", date(2026, 3, 1))
    end_date = c2.date_input("Fim", date(2026, 3, 31))
    
    if st.button("🚀 Gerar Escala Simulada"):
        # Load Directly from DB/Repo now!
        shifts = repo.load_shifts()
        if not shifts:
            st.error("Nenhum turno configurado no banco!")
            st.stop()
            
        # Add special Sunday Shift if missing
        if "H_DOM" not in shifts:
             shifts["H_DOM"] = Shift(code="H_DOM", minutes=300, day_scope=ShiftDayScope.SUNDAY, sector_id="CAIXA")

        # Load Rules from DB
        df_slots = repo.load_weekday_template_data()
        df_rotation = repo.load_sunday_rotation()
        
        if df_slots.empty:
            st.error("Mosaico Base está vazio no banco!")
            st.stop()
        
        # Instantiate Engines
        generator = CycleGenerator()
        policy_engine = PolicyEngine()
        
        try:
            with st.spinner("Processando Regras..."):
                # 2. Build Pipeline
                template = generator.build_weekday_template(df_slots, shifts)
                scale_cycle = generator.build_scale_cycle(df_rotation, template, "H_DOM", 300)
                
                context = ProjectionContext(
                    period_start=start_date,
                    period_end=end_date,
                    sector_id="CAIXA",
                    anchor_scale_id=1
                )
                
                projection = generator.project_cycle_to_period(scale_cycle, context)
                
                # 3. Validate
                violations_cons = policy_engine.validate_consecutive_days(projection)
                violations_hours = policy_engine.validate_weekly_hours(
                    projection, 
                    contract_targets={} # Empty means default 44h
                )
                
                all_violations = violations_cons + violations_hours
            
            # 4. Display Results
            st.success(f"Escala gerada com {len(projection)} alocações!")
            
            st.subheader("Visualização Diária")
            st.dataframe(projection, use_container_width=True)
            
            st.subheader(f"Violações Encontradas ({len(all_violations)})")
            if all_violations:
                v_data = [{
                    "Func": v.employee_id,
                    "Regra": v.rule_code,
                    "Gravidade": v.severity.value,
                    "Detalhe": v.detail,
                    "Data": v.date_start
                } for v in all_violations]
                st.dataframe(pd.DataFrame(v_data), use_container_width=True)
            else:
                st.success("Nenhuma violação encontrada! 🏆")
                
        except Exception as e:
            st.error(f"Erro na geração: {e}")
