import streamlit as st
import pandas as pd
from datetime import date
from src.infrastructure.database.setup import SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import PreferenceRequest, RequestType, RequestDecision

st.set_page_config(page_title="Gestão de Pedidos", layout="wide")
st.title("Gestão de Pedidos e Prioridades")

if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()
repo = SqlAlchemyRepository(st.session_state["db_session"])

tab1, tab2 = st.tabs(["Fila de Aprovação (RH)", "Novo Pedido (Colaborador)"])

with tab1:
    st.header("Fila de Aprovação")
    requests = repo.load_preferences()
    
    # Filter pending
    pending = [r for r in requests if r.decision == RequestDecision.PENDING]
    
    if not pending:
        st.success("Não há pedidos pendentes!")
    else:
        for req in pending:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.write(f"**{req.employee_id}**")
                c2.write(f"{req.request_date} ({req.request_type.value})")
                c3.write(f"Prioridade: {req.priority}")
                
                with c4:
                    col_a, col_r = st.columns(2)
                    if col_a.button("Aprovar", key=f"app_{req.request_id}"):
                        repo.update_preference_decision(req.request_id, RequestDecision.APPROVED, "Manual Approval via UI")
                        st.rerun()
                    if col_r.button("Rejeitar", key=f"rej_{req.request_id}"):
                        repo.update_preference_decision(req.request_id, RequestDecision.REJECTED, "Manual Rejection via UI")
                        st.rerun()

    st.subheader("Histórico de Decisões")
    history = [r for r in requests if r.decision != RequestDecision.PENDING]
    if history:
         data = []
         for h in history:
             data.append({
                 "ID": h.request_id,
                 "Func": h.employee_id,
                 "Data": h.request_date,
                 "Tipo": h.request_type,
                 "Decisão": h.decision.value,
                 "Motivo": h.decision_reason
             })
         st.dataframe(pd.DataFrame(data), use_container_width=True)

with tab2:
    st.header("Novo Pedido")
    employees = repo.load_employees()
    emp_ids = list(employees.keys()) or ["(Nenhum cadastrado)"]
    
    with st.form("new_request"):
        emp_id = st.selectbox("Colaborador", emp_ids, disabled=(len(emp_ids) == 1 and "(Nenhum cadastrado)" in emp_ids))
        req_date = st.date_input("Data do Pedido", min_value=date.today())
        req_type = st.selectbox("Tipo", [t.value for t in RequestType])
        priority = st.select_slider("Prioridade (Declarada)", options=["LOW", "MEDIUM", "HIGH"], value="MEDIUM")
        note = st.text_area("Justificativa")
        
        if st.form_submit_button("Enviar Pedido"):
            if emp_id == "(Nenhum cadastrado)" or not emp_ids:
                st.error("Cadastre funcionários primeiro em Gestão de Cadastros.")
            else:
                import uuid
                new_req = PreferenceRequest(
                    request_id=str(uuid.uuid4())[:8],
                    employee_id=emp_id,
                    request_date=req_date,
                    request_type=RequestType(req_type),
                    priority=priority,
                    note=note,
                    decision=RequestDecision.PENDING
                )
                try:
                    repo.add_preference(new_req)
                    st.success("Pedido enviado para análise do RH!")
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")
