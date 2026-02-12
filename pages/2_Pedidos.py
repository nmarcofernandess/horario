import streamlit as st
import pandas as pd
from datetime import date
from src.infrastructure.database.setup import SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import PreferenceRequest, RequestType, RequestDecision

st.set_page_config(page_title="Pedidos", layout="wide")
st.title("Pedidos de folga e turno")
st.caption("Colaboradores solicitam folgas ou trocas; o RH aprova ou rejeita.")

if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()
repo = SqlAlchemyRepository(st.session_state["db_session"])

tab1, tab2 = st.tabs(["Pendentes (RH)", "Novo pedido"])

with tab1:
    st.subheader("Pedidos para aprovar")
    st.caption("Ordenados por Picking Rules (MANUAL_RANK): menor rank = maior prioridade.")
    requests = repo.load_preferences()
    employees = repo.load_employees()
    emp_names = {e.employee_id: e.name for e in employees.values()}
    emp_ranks = {e.employee_id: e.rank for e in employees.values()}
    pending = [r for r in requests if r.decision == RequestDecision.PENDING]
    pending = sorted(pending, key=lambda r: (emp_ranks.get(r.employee_id, 999), r.request_date))
    if not pending:
        st.success("Nenhum pedido pendente.")
    else:
        for req in pending:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.write(f"**{emp_names.get(req.employee_id, req.employee_id)}**")
                c2.write(f"{req.request_date} — {req.request_type.value.replace('_', ' ').title()}")
                c3.write(f"Prioridade: {req.priority}")
                
                with c4:
                    col_a, col_r = st.columns(2)
                    if col_a.button("Aprovar", key=f"app_{req.request_id}"):
                        repo.update_preference_decision(req.request_id, RequestDecision.APPROVED, "Manual Approval via UI")
                        st.rerun()
                    if col_r.button("Rejeitar", key=f"rej_{req.request_id}"):
                        repo.update_preference_decision(req.request_id, RequestDecision.REJECTED, "Manual Rejection via UI")
                        st.rerun()

    st.subheader("Histórico")
    history = [r for r in requests if r.decision != RequestDecision.PENDING]
    if history:
        tipo_map = {"FOLGA_ON_DATE": "Folga na data", "SHIFT_CHANGE_ON_DATE": "Troca de turno", "AVOID_SUNDAY_DATE": "Evitar domingo"}
        decisao_map = {"APPROVED": "Aprovado", "REJECTED": "Rejeitado", "PENDING": "Pendente"}
        data = [{"Colaborador": emp_names.get(h.employee_id, h.employee_id), "Data": h.request_date, "Tipo": tipo_map.get(h.request_type.value, h.request_type.value), "Decisão": decisao_map.get(h.decision.value, h.decision.value)} for h in history]
        st.dataframe(pd.DataFrame(data), width="stretch", hide_index=True)

with tab2:
    st.subheader("Solicitar folga ou troca de turno")
    employees = repo.load_employees()
    emp_list = list(employees.values())
    emp_options = [(e.employee_id, e.name) for e in sorted(emp_list, key=lambda x: x.name)]
    
    if not emp_options:
        st.info("Cadastre colaboradores na página Colaboradores para enviar pedidos.")
    else:
        with st.form("new_request"):
            emp_sel = st.selectbox("Colaborador", range(len(emp_options)), format_func=lambda i: emp_options[i][1])
            emp_id = emp_options[emp_sel][0]
            req_date = st.date_input("Data desejada", min_value=date.today())
            req_type = st.selectbox("Tipo de pedido", ["FOLGA_ON_DATE", "SHIFT_CHANGE_ON_DATE", "AVOID_SUNDAY_DATE"], format_func=lambda x: {"FOLGA_ON_DATE": "Folga na data", "SHIFT_CHANGE_ON_DATE": "Troca de turno", "AVOID_SUNDAY_DATE": "Evitar domingo"}[x])
            shift_codes = ["CAI1", "CAI2", "CAI3", "CAI4", "CAI5", "CAI6", "DOM_08_12_30"]
            target_shift = st.selectbox("Novo turno (para troca)", ["—"] + shift_codes, disabled=(req_type != "SHIFT_CHANGE_ON_DATE")) if req_type else "—"
            priority = st.select_slider("Prioridade", options=["LOW", "MEDIUM", "HIGH"], value="MEDIUM", format_func=lambda x: {"LOW": "Baixa", "MEDIUM": "Média", "HIGH": "Alta"}[x])
            note = st.text_area("Justificativa (opcional)")
            if st.form_submit_button("Enviar pedido"):
                import uuid
                target_code = None if target_shift == "—" or req_type != "SHIFT_CHANGE_ON_DATE" else target_shift
                if req_type == "SHIFT_CHANGE_ON_DATE" and not target_code:
                    st.error("Para troca de turno, selecione o novo turno desejado.")
                else:
                    new_req = PreferenceRequest(
                        request_id=str(uuid.uuid4()),
                        employee_id=emp_id,
                        request_date=req_date,
                        request_type=RequestType(req_type) if isinstance(req_type, str) else req_type,
                        priority=priority,
                        target_shift_code=target_code,
                        note=note,
                        decision=RequestDecision.PENDING
                    )
                    try:
                        repo.add_preference(new_req)
                        st.success("Pedido enviado! O RH analisará em breve.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
