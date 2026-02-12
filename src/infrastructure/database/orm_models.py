from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class SectorORM(Base):
    __tablename__ = "sectors"
    
    sector_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    
    employees = relationship("EmployeeORM", back_populates="sector")
    contracts = relationship("ContractORM", back_populates="sector")

class EmployeeORM(Base):
    __tablename__ = "employees"
    
    employee_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    contract_code = Column(String, ForeignKey("contracts.contract_code"), nullable=False)
    sector_id = Column(String, ForeignKey("sectors.sector_id"), nullable=False)
    rank = Column(Integer, default=999)
    active = Column(Boolean, default=True)
    
    sector = relationship("SectorORM", back_populates="employees")
    contract = relationship("ContractORM", back_populates="employees")
    preferences = relationship("PreferenceORM", back_populates="employee")

class ContractORM(Base):
    __tablename__ = "contracts"
    
    contract_code = Column(String, primary_key=True)
    sector_id = Column(String, ForeignKey("sectors.sector_id"), nullable=False)
    weekly_minutes = Column(Integer, nullable=False)
    sunday_mode = Column(String, default="WORK_WITH_COMPENSATION")
    allowed_shifts_json = Column(JSON, default=list) # List of shift codes
    
    sector = relationship("SectorORM", back_populates="contracts")
    employees = relationship("EmployeeORM", back_populates="contract")

class PreferenceORM(Base):
    __tablename__ = "preferences"
    
    request_id = Column(String, primary_key=True)
    employee_id = Column(String, ForeignKey("employees.employee_id"), nullable=False)
    request_date = Column(Date, nullable=False)
    request_type = Column(String, nullable=False) # Enum as string
    priority = Column(String, default="MEDIUM")
    target_shift_code = Column(String, nullable=True)
    note = Column(String, nullable=True)
    
    decision = Column(String, default="PENDING")
    decision_reason = Column(String, nullable=True)
    
    employee = relationship("EmployeeORM", back_populates="preferences")
