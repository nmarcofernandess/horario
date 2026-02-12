"""Pydantic schemas para API REST - alinhados a AUDITORIA_PRE_NEXT.md"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


# --- Employees ---
class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    contract_code: str
    sector_id: str
    rank: int = 999
    active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    pass


class EmployeeRankUpdate(BaseModel):
    rank: int


# --- Sectors ---
class SectorBase(BaseModel):
    sector_id: str
    name: str


class SectorCreate(SectorBase):
    pass


class SectorResponse(SectorBase):
    active: bool = True


# --- Preferences ---
class PreferenceCreate(BaseModel):
    request_id: str
    employee_id: str
    request_date: date
    request_type: str  # FOLGA_ON_DATE | SHIFT_CHANGE_ON_DATE | AVOID_SUNDAY_DATE
    priority: str = "MEDIUM"
    target_shift_code: Optional[str] = None
    note: Optional[str] = None


class PreferenceDecision(BaseModel):
    decision: str  # APPROVED | REJECTED
    reason: Optional[str] = None


class PreferenceResponse(BaseModel):
    request_id: str
    employee_id: str
    request_date: date
    request_type: str
    priority: str
    target_shift_code: Optional[str] = None
    note: Optional[str] = None
    decision: str
    decision_reason: Optional[str] = None


# --- Scale ---
class ScaleGenerateRequest(BaseModel):
    period_start: date
    period_end: date
    sector_id: str = "CAIXA"


class AssignmentResponse(BaseModel):
    work_date: str
    employee_id: str
    employee_name: Optional[str] = None
    status: str
    shift_code: Optional[str] = None
    minutes: int
    source_rule: str


class ViolationResponse(BaseModel):
    employee_id: str
    employee_name: Optional[str] = None
    rule_code: str
    rule_label: Optional[str] = None
    severity: str
    date_start: str
    date_end: str
    detail: str


class ScaleGenerateResponse(BaseModel):
    status: str
    assignments_count: int
    violations_count: int
    preferences_processed: int
    exceptions_applied: int


# --- Shifts ---
class ShiftResponse(BaseModel):
    shift_code: str
    sector_id: str
    minutes: int
    day_scope: str


# --- Exceptions ---
class ExceptionCreate(BaseModel):
    sector_id: str = "CAIXA"
    employee_id: str
    exception_date: date
    exception_type: str  # VACATION | MEDICAL_LEAVE | SWAP | BLOCK
    note: Optional[str] = None


class ExceptionResponse(BaseModel):
    sector_id: str
    employee_id: str
    exception_date: date
    exception_type: str
    note: Optional[str] = None


# --- Demand Profile ---
class DemandSlotCreate(BaseModel):
    sector_id: str = "CAIXA"
    work_date: date
    slot_start: str  # "08:00", "08:30"
    min_required: int


class DemandSlotResponse(BaseModel):
    sector_id: str
    work_date: date
    slot_start: str
    min_required: int
