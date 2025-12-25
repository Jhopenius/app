from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentRead(DepartmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    department_id: int
    full_name: str = Field(..., max_length=200)
    hire_date: date
    base_salary: float
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeRead(EmployeeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class VendorBase(BaseModel):
    name: str = Field(..., max_length=200)
    inn: str = Field(..., max_length=20)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(VendorBase):
    pass


class VendorRead(VendorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ExpenseBase(BaseModel):
    department_id: int
    vendor_id: int
    amount: float
    expense_date: date
    is_approved: bool = False


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PayrollBase(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    net_amount: float
    paid_at: Optional[datetime]
    is_paid: bool = False


class PayrollCreate(PayrollBase):
    pass


class PayrollUpdate(PayrollBase):
    pass


class PayrollRead(PayrollBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
