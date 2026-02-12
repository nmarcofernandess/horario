import streamlit as st
import pandas as pd
from src.infrastructure.database.setup import SessionLocal
from src.infrastructure.repositories_db import SqlAlchemyRepository
from src.domain.models import Employee

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

st.set_page_config(page_title="Colaboradores", layout="wide")

if "db_session" not in st.session_state:
    st.session_state["db_session"] = SessionLocal()
repo = SqlAlchemyRepository(st.session_state["db_session"])

st.title("Colaboradores")
tab1, tab2 = st.tabs(["Colaboradores", "Setores"])

with tab1:
    st.subheader("Colaboradores cadastrados")
    sectors_for_select = repo.load_sectors()
    sector_options = [s[1] for s in sectors_for_select] or ["Caixa"]
    sector_ids = [s[0] for s in sectors_for_select] or ["CAIXA"]
    with st.expander("➕ Novo colaborador"):
        with st.form("add_employee_form"):
            c1, c2, c3 = st.columns(3)
            emp_id = c1.text_input("Código", placeholder="Ex: CLEONICE")
            name = c2.text_input("Nome completo")
            c4, c5 = st.columns(2)
            contract = c4.selectbox("Contrato", ["44h semanais", "36h semanais", "30h semanais"])
            contract_map = {"44h semanais": "H44_CAIXA", "36h semanais": "H36_CAIXA", "30h semanais": "H30_CAIXA"}
            sector_sel = c5.selectbox("Setor", range(len(sector_options)), format_func=lambda i: sector_options[i]) if sector_options else 0
            sector_id_val = sector_ids[sector_sel] if sector_sel is not None else (sector_ids[0] if sector_ids else "CAIXA")
            submitted = st.form_submit_button("Cadastrar")
            if submitted and emp_id and name:
                new_emp = Employee(
                    employee_id=emp_id.upper().strip(),
                    name=name.strip().title(),
                    contract_code=contract_map[contract],
                    sector_id=sector_id_val,
                    rank=99,
                    active=True
                )
                try:
                    repo.add_employee(new_emp)
                    st.success(f"Colaborador {name.strip().title()} cadastrado!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")

    employees = repo.load_employees()
    if employees:
        # Ordenar por rank (menor = mais prioritário)
        emp_list = sorted(employees.values(), key=lambda e: e.rank)
        contrato_labels = {"H44_CAIXA": "44h", "H36_CAIXA": "36h", "H30_CAIXA": "30h", "CLT_44H": "44h"}
        data = []
        for i, e in enumerate(emp_list, 1):
            contrato = contrato_labels.get(e.contract_code, e.contract_code)
            data.append({
                "Ordem": i,
                "Nome": e.name,
                "Contrato": contrato,
                "_emp_id": e.employee_id,
            })

        df = pd.DataFrame(data)

        if HAS_AGGRID:
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_grid_options(
                rowDragManaged=True,
                animateRows=True,
                suppressRowClickSelection=True,
            )
            gb.configure_column("Ordem", rowDrag=True)
            gb.configure_column("Ordem", editable=False)
            gb.configure_column("_emp_id", hide=True)  # Oculto: uso interno para DnD/Update
            grid_options = gb.build()

            grid_response = AgGrid(
                df,
                grid_options=grid_options,
                fit_columns_on_grid_load=True,
                height=350,
                update_mode=GridUpdateMode.MANUAL,
                data_return_mode=DataReturnMode.AS_INPUT,
            )

            if grid_response and grid_response.get("data"):
                new_df = pd.DataFrame(grid_response["data"])
                if len(new_df) == len(df) and "_emp_id" in new_df.columns:
                    for pos, (_, row) in enumerate(new_df.iterrows()):
                        repo.update_employee_rank(row["_emp_id"], pos + 1)
                    st.rerun()

            st.caption("Arraste a coluna Ordem para reordenar a lista. Clique em Update para salvar.")

        st.subheader("Editar colaborador")
        emp_options = [e.name for e in sorted(emp_list, key=lambda x: x.name)]
        emp_values = [e.employee_id for e in sorted(emp_list, key=lambda x: x.name)]
        sel_idx = st.selectbox("Selecione o colaborador", range(len(emp_options)), format_func=lambda i: emp_options[i], key="edit_emp_sel")
        if sel_idx is not None and emp_list:
            emp = employees[emp_values[sel_idx]]
            with st.form("edit_employee_form"):
                contract_map_rev = {"H44_CAIXA": "44h semanais", "H36_CAIXA": "36h semanais", "H30_CAIXA": "30h semanais", "CLT_44H": "44h semanais"}
                new_name = st.text_input("Nome", value=emp.name)
                new_contract = st.selectbox(
                    "Contrato",
                    ["44h semanais", "36h semanais", "30h semanais"],
                    index=["44h semanais", "36h semanais", "30h semanais"].index(contract_map_rev.get(emp.contract_code, "44h semanais"))
                )
                contract_map = {"44h semanais": "H44_CAIXA", "36h semanais": "H36_CAIXA", "30h semanais": "H30_CAIXA"}
                if st.form_submit_button("Salvar alterações"):
                    updated = Employee(
                        employee_id=emp.employee_id,
                        name=new_name.strip() or emp.name,
                        contract_code=contract_map[new_contract],
                        sector_id=emp.sector_id,
                        rank=emp.rank,
                        active=emp.active,
                    )
                    repo.add_employee(updated)
                    st.success(f"Colaborador {updated.name} atualizado!")
                    st.rerun()
        else:
            st.caption("Selecione um colaborador acima para editar nome e contrato.")
    else:
        st.info("Nenhum colaborador cadastrado. Use a aba Novo cadastro.")

with tab2:
    st.subheader("Setores cadastrados")
    with st.expander("➕ Novo setor"):
        with st.form("add_sector_form"):
            c1, c2 = st.columns(2)
            sec_id = c1.text_input("Código", placeholder="Ex: CAIXA")
            sec_name = c2.text_input("Nome do setor", placeholder="Ex: Caixa")
            if st.form_submit_button("Cadastrar"):
                if sec_id and sec_name:
                    repo.add_sector(sec_id.upper().strip(), sec_name.strip().title())
                    st.success(f"Setor {sec_name} cadastrado!")
                    st.rerun()

    sectors = repo.load_sectors()
    if sectors:
        df_sectors = pd.DataFrame(sectors, columns=["Identificador", "Nome"])
        st.dataframe(df_sectors, width="stretch", hide_index=True)
    else:
        st.info("Nenhum setor cadastrado. Use o formulário acima para adicionar.")
