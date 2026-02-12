"""Rotas de colaboradores"""
from fastapi import APIRouter, Depends, HTTPException
from src.domain.models import Employee
from src.infrastructure.repositories_db import SqlAlchemyRepository
from api.schemas import EmployeeCreate, EmployeeResponse, EmployeeRankUpdate
from api.deps import get_repo

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeResponse])
def list_employees(repo: SqlAlchemyRepository = Depends(get_repo)):
    employees = repo.load_employees()
    return [
        EmployeeResponse(
            employee_id=e.employee_id,
            name=e.name,
            contract_code=e.contract_code,
            sector_id=e.sector_id,
            rank=e.rank,
            active=e.active,
        )
        for e in employees.values()
    ]


@router.post("", response_model=EmployeeResponse)
def create_or_update_employee(
    data: EmployeeCreate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    emp = Employee(
        employee_id=data.employee_id,
        name=data.name,
        contract_code=data.contract_code,
        sector_id=data.sector_id,
        rank=data.rank,
        active=data.active,
    )
    repo.add_employee(emp)
    return EmployeeResponse(
        employee_id=emp.employee_id,
        name=emp.name,
        contract_code=emp.contract_code,
        sector_id=emp.sector_id,
        rank=emp.rank,
        active=emp.active,
    )


@router.patch("/{employee_id}/rank")
def update_employee_rank(
    employee_id: str,
    data: EmployeeRankUpdate,
    repo: SqlAlchemyRepository = Depends(get_repo),
):
    employees = repo.load_employees()
    if employee_id not in employees:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    repo.update_employee_rank(employee_id, data.rank)
    return {"ok": True, "employee_id": employee_id, "rank": data.rank}
