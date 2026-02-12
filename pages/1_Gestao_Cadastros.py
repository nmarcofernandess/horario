import streamlit as st
import pandas as pd
from src.infrastructure.database.setup import SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import Employee

st.set_page_config(page_title="Gestão de Cadastros", layout="wide")

st.title("Gestão de Cadastros")

# Dependency Injection (Manual for Streamlit)
if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()
repo = SqlAlchemyRepository(st.session_state["db_session"])

tab1, tab2 = st.tabs(["Funcionários", "Setores"])

with tab1:
    st.header("Funcionários")
    
    # Form to Add Employee
    with st.expander("Novo Funcionário"):
        with st.form("add_employee_form"):
            c1, c2, c3 = st.columns(3)
            emp_id = c1.text_input("ID (Sigla)", placeholder="EX: JOAO")
            name = c2.text_input("Nome Completo")
            rank = c3.number_input("Rank (Prioridade)", min_value=1, value=999)
            
            c4, c5 = st.columns(2)
            # Fetch contracts (mocked list for now or fetch from DB if implemented)
            # Ideally fetch from repo.contracts
            # We implemented repo.add_contract but not get_all_contracts in Repo yet.
            # Using hardcoded list for MVP velocity as requested.
            contract = c4.selectbox("Contrato", ["H44_CAIXA", "H36_CAIXA", "H30_CAIXA"])
            sector = c5.selectbox("Setor", ["CAIXA"]) 
            
            submitted = st.form_submit_button("Cadastrar")
            if submitted and emp_id and name:
                new_emp = Employee(
                    employee_id=emp_id.upper(),
                    name=name.upper(),
                    contract_code=contract,
                    sector_id=sector,
                    rank=rank,
                    active=True
                )
                try:
                    repo.add_employee(new_emp)
                    st.success(f"Funcionário {name} cadastrado!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    # List Employees
    employees = repo.load_employees()
    if employees:
        data = []
        for e in employees.values():
            data.append({
                "ID": e.employee_id,
                "Nome": e.name,
                "Rank": e.rank,
                "Contrato": e.contract_code,
                "Ativo": e.active
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("Nenhum funcionário cadastrado.")

with tab2:
    st.header("Setores")
    with st.form("add_sector"):
        sec_id = st.text_input("ID Setor", placeholder="EX: AOUGUE")
        sec_name = st.text_input("Nome", placeholder="Açougue")
        if st.form_submit_button("Criar Setor"):
            if sec_id and sec_name:
                repo.add_sector(sec_id.upper(), sec_name)
                st.success("Setor Criado!")
