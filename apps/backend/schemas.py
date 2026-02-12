"""Pydantic schemas para API REST."""
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
class RiskAckPayload(BaseModel):
    actor_role: str = "OPERADOR"
    actor_name: Optional[str] = None
    reason: str = Field(..., min_length=3)


class ScaleGenerateRequest(BaseModel):
    period_start: date
    period_end: date
    sector_id: str = "CAIXA"
    risk_ack: Optional[RiskAckPayload] = None


class PreflightIssue(BaseModel):
    code: str
    message: str
    recommended_action: str


class PreflightResponse(BaseModel):
    mode: str  # NORMAL | ESTRITO
    blockers: List[PreflightIssue]
    critical_warnings: List[PreflightIssue]
    can_proceed: bool
    ack_required: bool


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


class ScaleSimulateResponse(BaseModel):
    status: str
    assignments_count: int
    violations_count: int
    preferences_processed: int
    exceptions_applied: int
    assignments: List[AssignmentResponse]
    violations: List[ViolationResponse]


class WeeklyAnalysisRequest(BaseModel):
    period_start: date
    period_end: date
    sector_id: str = "CAIXA"
    mode: str = "OFFICIAL"  # OFFICIAL | SIMULATION


class WeeklySummaryRow(BaseModel):
    window: str  # MON_SUN | SUN_SAT
    week_start: str
    week_end: str
    employee_id: str
    employee_name: Optional[str] = None
    contract_code: str
    actual_minutes: int
    target_minutes: int
    delta_minutes: int
    status: str  # OK | OUT


class WeeklyAnalysisResponse(BaseModel):
    period_start: str
    period_end: str
    sector_id: str
    policy_week_definition: str
    tolerance_minutes: int
    summaries_mon_sun: List[WeeklySummaryRow]
    summaries_sun_sat: List[WeeklySummaryRow]
    external_dependencies_open: List[str]


# --- Shifts ---
class ShiftResponse(BaseModel):
    shift_code: str
    sector_id: str
    minutes: int
    day_scope: str


class ShiftCreate(BaseModel):
    shift_code: str
    sector_id: str = "CAIXA"
    minutes: int = Field(..., ge=0)
    day_scope: str = "WEEKDAY"


class ShiftUpdate(BaseModel):
    minutes: int = Field(..., ge=0)
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


class ExceptionUpdate(BaseModel):
    sector_id: str = "CAIXA"
    original_employee_id: str
    original_exception_date: date
    original_exception_type: str
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


class DemandSlotUpdate(BaseModel):
    sector_id: str = "CAIXA"
    original_work_date: date
    original_slot_start: str
    work_date: date
    slot_start: str
    min_required: int


# --- Weekday Template ---
class WeekdayTemplateSlot(BaseModel):
    employee_id: str
    day_key: str  # SEG/TER... ou MON/TUE...
    shift_code: str
    minutes: int = 0


# --- Sunday Rotation ---
class SundayRotationItem(BaseModel):
    scale_index: int = Field(..., ge=1)
    employee_id: str
    sunday_date: date
    folga_date: Optional[date] = None


# --- Governance / E4 ---
class GovernanceChecklistItem(BaseModel):
    item_id: str
    title: str
    done: bool
    detail: Optional[str] = None


class GovernanceConfigResponse(BaseModel):
    accepted_dom_folgas_markers: List[str]
    marker_semantics: dict[str, str]
    collective_agreement_id: str
    sunday_holiday_legal_validated: bool
    legal_validation_note: Optional[str] = None
    pending_items: List[str]
    release_checklist: List[GovernanceChecklistItem]


class GovernanceConfigUpdate(BaseModel):
    marker_semantics: dict[str, str]
    collective_agreement_id: str
    sunday_holiday_legal_validated: bool
    legal_validation_note: Optional[str] = None


class RuntimeModeConfig(BaseModel):
    mode: str  # NORMAL | ESTRITO
    updated_at: Optional[str] = None
    updated_by_role: Optional[str] = None
    source: str = "policy"


class RuntimeModeUpdate(BaseModel):
    mode: str
    actor_role: str = "ADMIN"


class GovernanceAuditEvent(BaseModel):
    event_id: int
    created_at: str
    operation: str
    mode: str
    actor_role: str
    actor_name: Optional[str] = None
    reason: Optional[str] = None
    warnings: List[str]
    sector_id: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
