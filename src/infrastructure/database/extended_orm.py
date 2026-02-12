
from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey
from src.infrastructure.database.orm_models import Base

class ShiftORM(Base):
    __tablename__ = "shifts"
    shift_code = Column(String, primary_key=True)
    sector_id = Column(String, nullable=False) # FK logical
    minutes = Column(Integer, nullable=False)
    day_scope = Column(String, default="WEEKDAY") # WEEKDAY, SUNDAY
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)

class CycleTemplateORM(Base):
    __tablename__ = "cycle_templates"
    # Composite PK logically
    id = Column(Integer, primary_key=True, autoincrement=True)
    scale_id = Column(Integer, nullable=False)
    cycle_day = Column(Integer, nullable=False)
    employee_id = Column(String, ForeignKey("employees.employee_id"), nullable=False)
    day_key = Column(String, nullable=False) # MON, TUE...
    shift_code = Column(String, nullable=True)
    minutes = Column(Integer, default=0)
    status = Column(String, default="WORK") # WORK, FOLGA
    source = Column(String, default="MANUAL")

class SundayRotationORM(Base):
    __tablename__ = "sunday_rotations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scale_index = Column(Integer, nullable=False)
    employee_id = Column(String, ForeignKey("employees.employee_id"), nullable=False)
    sunday_date = Column(Date, nullable=False)
    folga_date = Column(Date, nullable=True)
