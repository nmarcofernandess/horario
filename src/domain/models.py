from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional, Dict, Any, Union

# Enums
class WeekDefinition(str, Enum):
    MON_SUN = "MON_SUN"
    SUN_SAT = "SUN_SAT"

class ShiftDayScope(str, Enum):
    WEEKDAY = "WEEKDAY"
    SUNDAY = "SUNDAY"

class RequestType(str, Enum):
    FOLGA_ON_DATE = "FOLGA_ON_DATE"
    SHIFT_CHANGE_ON_DATE = "SHIFT_CHANGE_ON_DATE"
    AVOID_SUNDAY_DATE = "AVOID_SUNDAY_DATE"

class RequestDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class PickingStrategy(str, Enum):
    WEIGHTED_SCORE = "WEIGHTED_SCORE"
    FIRST_COME_FIRST_SERVED = "FIRST_COME_FIRST_SERVED"
    MANUAL_ONLY = "MANUAL_ONLY"
    MANUAL_RANK = "MANUAL_RANK"

class ExceptionType(str, Enum):
    """Tipos de exceção que convertem WORK em ABSENCE."""
    VACATION = "VACATION"
    MEDICAL_LEAVE = "MEDICAL_LEAVE"
    SWAP = "SWAP"
    BLOCK = "BLOCK"

class ViolationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# Domain Entities

@dataclass(frozen=True)
class Employee:
    employee_id: str
    name: str
    contract_code: str
    sector_id: str
    rank: int = 999  # Lower number = Higher priority
    tags: List[str] = field(default_factory=list)
    active: bool = True

@dataclass(frozen=True)
class Shift:
    code: str
    minutes: int
    day_scope: ShiftDayScope
    sector_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class Contract:
    contract_code: str
    weekly_minutes: int
    sector_id: str
    allowed_shifts: List[str] = field(default_factory=list)
    sunday_mode: str = "WORK_WITH_COMPENSATION"

@dataclass(frozen=True)
class PickingRules:
    strategy: PickingStrategy
    criteria: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Policy:
    policy_id: str
    policy_version: str
    sector_id: str
    week_definition: WeekDefinition
    picking_rules: PickingRules
    contracts: Dict[str, Contract]
    shifts: Dict[str, Shift]
    constraints: Dict[str, Any]
    sunday_rules: Dict[str, Any]
    preference_rules: Dict[str, Any]

@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    employee_id: str
    work_date: date
    sector_id: str
    status: str  # WORK, FOLGA, ABSENCE
    shift_code: Optional[str] = None
    minutes: int = 0
    source: str = "ENGINE"
    scale_id: Optional[int] = None
    cycle_day: Optional[int] = None

@dataclass
class PreferenceRequest:
    request_id: str
    employee_id: str
    request_date: date
    request_type: RequestType
    priority: str  # HIGH, MEDIUM, LOW
    target_shift_code: Optional[str] = None
    note: str = ""
    decision: RequestDecision = RequestDecision.PENDING
    decision_reason: str = ""

@dataclass(frozen=True)
class ScheduleException:
    """Exceção que remove o colaborador da escala em determinada data (férias, atestado, etc)."""
    sector_id: str
    employee_id: str
    exception_date: date
    exception_type: ExceptionType
    note: str = ""


@dataclass(frozen=True)
class DemandSlot:
    """Cobertura mínima por faixa horária (ex.: 08:00 = 08:00-08:30, min 2 pessoas)."""
    sector_id: str
    work_date: date
    slot_start: str  # "08:00", "08:30", ...
    min_required: int

@dataclass(frozen=True)
class Violation:
    employee_id: str
    rule_code: str
    severity: ViolationSeverity
    date_start: date
    date_end: date
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ProjectionContext:
    period_start: date
    period_end: date
    sector_id: str
    anchor_scale_id: int = 1
    anchor_date: Optional[date] = None  # Domingo de referência do ciclo; se None, usa period_start
