
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date
from src.infrastructure.database.setup import SessionLocal, init_db
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.infrastructure.parsers.legacy.csv_import import LegacyCSVImporter
from src.domain.engines import CycleGenerator, PolicyEngine
from src.domain.models import Shift, ProjectionContext, ShiftDayScope, ScheduleException, ExceptionType, DemandSlot

# DB Setup
init_db()
if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()

repo = SqlAlchemyRepository(st.session_state["db_session"])
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
importer = LegacyCSVImporter(DATA_DIR)

st.set_page_config(page_title="Configuração", layout="wide", page_icon="⚙️")

st.title("Configuração da escala")
st.markdown("Defina turnos, mosaico semanal (quem trabalha em qual dia) e rodízio de domingos.")

importer = LegacyCSVImporter(DATA_DIR)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Turnos",
    "Mosaico semanal",
    "Rodízio de domingos",
    "Exceções",
    "Demand (cobertura)",
    "Folgas",
    "Simular"
])

with tab1:
    st.subheader("Turnos disponíveis")
    st.markdown("Código e duração de cada turno.")
    
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
        mapa = {"shift_code": "Código", "minutes_median": "Minutos", "day_scope": "Tipo"}
        inv_map = {v: k for k, v in mapa.items()}
        df_display = df_shifts.rename(columns={k: v for k, v in mapa.items() if k in df_shifts.columns})
        edited_shifts = st.data_editor(df_display, num_rows="dynamic", key="editor_shifts", width="stretch")
        edited_shifts = edited_shifts.rename(columns={k: v for k, v in inv_map.items() if k in edited_shifts.columns})
        if st.button("Salvar turnos", key="btn_save_shifts"):
            repo.save_shifts(edited_shifts)
            st.success("Turnos salvos.")
            st.rerun()
    else:
        st.warning("Nenhum turno cadastrado.")

with tab2:
    st.subheader("Mosaico semanal")
    st.markdown("Quem trabalha em qual dia da semana (segunda a sábado).")
    
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
            
        day_filter = st.selectbox("Filtrar dia", ["Todos"] + sorted(df_slots['day_name'].unique().tolist()))
        df_display = df_slots if day_filter == "Todos" else df_slots[df_slots['day_name'] == day_filter]
            
        edited_slots = st.data_editor(
            df_display,
            key="editor_slots",
            width="stretch",
            num_rows="dynamic"
        )
        if st.button("Salvar mosaico", key="btn_save_slots"):
            repo.save_weekday_template(edited_slots)
            st.success("Mosaico salvo.")
            st.rerun()
    else:
        st.warning("Nenhum mosaico cadastrado.")

with tab3:
    st.subheader("Rodízio de domingos")
    st.markdown("Quem trabalha em cada domingo e quando tira a folga compensatória.")
    
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
            width="stretch",
            num_rows="dynamic",
            column_config={
                "sunday_date": st.column_config.DateColumn("Domingo trabalhado"),
                "folga_date": st.column_config.DateColumn("Folga compensatória"),
                "employee_id": st.column_config.TextColumn("Colaborador"),
                "scale_index": st.column_config.NumberColumn("Índice do ciclo"),
            }
        )
        if st.button("Salvar rodízio", key="btn_save_rotation"):
            repo.save_sunday_rotation(edited_rotation)
            st.success("Rodízio salvo.")
            st.rerun()
    else:
        st.warning("Nenhuma regra de domingo cadastrada.")

with tab4:
    st.subheader("Exceções (férias, atestado, bloqueios)")
    st.markdown("Datas em que o colaborador não pode trabalhar — a escala converte WORK em ABSENCE.")

    exc_type_map = {
        "VACATION": "Férias",
        "MEDICAL_LEAVE": "Atestado",
        "SWAP": "Troca",
        "BLOCK": "Bloqueio",
    }
    sector_id = "CAIXA"
    period_start = date(2026, 2, 1)
    period_end = date(2026, 12, 31)
    exceptions = repo.load_exceptions(sector_id, period_start, period_end)

    if exceptions:
        exc_data = [
            {
                "Colaborador": e.employee_id,
                "Data": e.exception_date,
                "Tipo": exc_type_map.get(e.exception_type.value, e.exception_type.value),
                "Observação": e.note or "",
            }
            for e in exceptions
        ]
        st.dataframe(pd.DataFrame(exc_data), width="stretch", hide_index=True)

    with st.form("nova_excecao"):
        st.subheader("Nova exceção")
        employees = repo.load_employees()
        emp_options = [(e.employee_id, e.name) for e in sorted(employees.values(), key=lambda x: x.name)]
        emp_sel = st.selectbox("Colaborador", range(len(emp_options)), format_func=lambda i: emp_options[i][1])
        emp_id = emp_options[emp_sel][0]
        exc_date = st.date_input("Data", min_value=period_start, max_value=period_end)
        exc_type = st.selectbox("Tipo", list(exc_type_map.keys()), format_func=lambda x: exc_type_map[x])
        exc_note = st.text_input("Observação (opcional)")
        if st.form_submit_button("Adicionar"):
            exc = ScheduleException(
                sector_id=sector_id,
                employee_id=emp_id,
                exception_date=exc_date,
                exception_type=ExceptionType(exc_type),
                note=exc_note,
            )
            repo.add_exception(exc)
            st.success("Exceção adicionada.")
            st.rerun()

with tab5:
    st.subheader("Demand profile (cobertura mínima por faixa)")
    st.markdown("Define cobertura mínima por data e horário — ex.: 08:00 = 08:00-08:30, mínimo 2 pessoas.")

    sector_id = "CAIXA"
    period_start = date(2026, 2, 1)
    period_end = date(2026, 12, 31)
    demand_slots = repo.load_demand_profile(sector_id, period_start, period_end)

    if demand_slots:
        d_data = [{"Data": s.work_date, "Slot": s.slot_start, "Mín. pessoas": s.min_required} for s in demand_slots]
        st.dataframe(pd.DataFrame(d_data), width="stretch", hide_index=True)

    with st.form("novo_demand"):
        st.subheader("Novo slot de demanda")
        d_date = st.date_input("Data", min_value=period_start, max_value=period_end)
        slot_options = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
        d_slot = st.selectbox("Slot (início 30min)", slot_options)
        d_min = st.number_input("Mínimo de pessoas", min_value=1, value=2)
        if st.form_submit_button("Adicionar"):
            slot = DemandSlot(sector_id=sector_id, work_date=d_date, slot_start=d_slot, min_required=d_min)
            repo.add_demand_slot(slot)
            st.success("Slot adicionado.")
            st.rerun()

with tab6:
    st.subheader("Matriz de folgas")
    df_folgas = importer.load_day_off_matrix()
    if not df_folgas.empty:
        st.dataframe(df_folgas, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma matriz carregada.")

with tab7:
    st.subheader("Simular escala")
    
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Início", date(2026, 3, 1))
    end_date = c2.date_input("Fim", date(2026, 3, 31))
    
    if st.button("Gerar escala"):
        # Load Directly from DB/Repo now!
        shifts = repo.load_shifts()
        if not shifts:
            st.error("Nenhum turno configurado no banco!")
            st.stop()
            
        # Add special Sunday Shift if missing
        if "DOM_08_12_30" not in shifts and "H_DOM" not in shifts:
            shifts["DOM_08_12_30"] = Shift(code="DOM_08_12_30", minutes=270, day_scope=ShiftDayScope.SUNDAY, sector_id="CAIXA")

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
                scale_cycle = generator.build_scale_cycle(df_rotation, template, "DOM_08_12_30", 270)
                
                anchor_date = None
                if not df_rotation.empty and "sunday_date" in df_rotation.columns:
                    min_sun = pd.to_datetime(df_rotation["sunday_date"]).min()
                    if pd.notna(min_sun):
                        anchor_date = min_sun.date() if hasattr(min_sun, "date") else min_sun
                context = ProjectionContext(
                    period_start=start_date,
                    period_end=end_date,
                    sector_id="CAIXA",
                    anchor_scale_id=1,
                    anchor_date=anchor_date,
                )
                
                projection = generator.project_cycle_to_period(scale_cycle, context)
                
                # 3. Validate
                contract_targets = repo.load_contract_targets("CAIXA")
                violations_cons = policy_engine.validate_consecutive_days(projection)
                violations_hours = policy_engine.validate_weekly_hours(projection, contract_targets)
                violations_intershift = policy_engine.validate_intershift_rest(
                    projection, shifts, {"min_intershift_rest_minutes": 660}
                )
                demand_slots = repo.load_demand_profile("CAIXA", start_date, end_date)
                violations_demand = policy_engine.validate_demand_coverage(projection, demand_slots, shifts)

                all_violations = violations_cons + violations_hours + violations_intershift + violations_demand
            
            # 4. Display Results
            st.success(f"Escala gerada com {len(projection)} alocações.")
            from src.application.ui.display import humanize_df_scale, humanize_df_violations
            emp_names = {e.employee_id: e.name for e in repo.load_employees().values()}
            proj_display = humanize_df_scale(projection, emp_names)
            st.dataframe(proj_display, width="stretch", hide_index=True)
            st.subheader(f"Alertas ({len(all_violations)})")
            if all_violations:
                v_df = pd.DataFrame([{"employee_id": v.employee_id, "rule_code": v.rule_code, "severity": v.severity.value, "detail": v.detail} for v in all_violations])
                v_display = humanize_df_violations(v_df, emp_names)
                st.dataframe(v_display, width="stretch", hide_index=True)
            else:
                st.success("Nenhuma violação encontrada! 🏆")
                
        except Exception as e:
            st.error(f"Erro na geração: {e}")
