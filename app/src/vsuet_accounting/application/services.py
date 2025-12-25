from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from vsuet_accounting.domain import schemas
from vsuet_accounting.infrastructure.db import models


def list_departments(session: Session) -> list[models.Department]:
    return session.scalars(select(models.Department).order_by(models.Department.name)).all()


def create_department(
    session: Session, payload: schemas.DepartmentCreate
) -> models.Department:
    department = models.Department(**payload.model_dump())
    session.add(department)
    session.commit()
    session.refresh(department)
    return department


def update_department(
    session: Session, department_id: int, payload: schemas.DepartmentUpdate
) -> Optional[models.Department]:
    department = session.get(models.Department, department_id)
    if not department:
        return None
    for key, value in payload.model_dump().items():
        setattr(department, key, value)
    session.commit()
    session.refresh(department)
    return department


def delete_department(session: Session, department_id: int) -> bool:
    department = session.get(models.Department, department_id)
    if not department:
        return False
    session.delete(department)
    session.commit()
    return True


def list_employees(session: Session) -> list[models.Employee]:
    query = (
        select(models.Employee)
        .options(selectinload(models.Employee.department))
        .order_by(models.Employee.full_name)
    )
    return session.scalars(query).all()


def create_employee(
    session: Session, payload: schemas.EmployeeCreate
) -> models.Employee:
    employee = models.Employee(**payload.model_dump())
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


def update_employee(
    session: Session, employee_id: int, payload: schemas.EmployeeUpdate
) -> Optional[models.Employee]:
    employee = session.get(models.Employee, employee_id)
    if not employee:
        return None
    for key, value in payload.model_dump().items():
        setattr(employee, key, value)
    session.commit()
    session.refresh(employee)
    return employee


def delete_employee(session: Session, employee_id: int) -> bool:
    employee = session.get(models.Employee, employee_id)
    if not employee:
        return False
    session.delete(employee)
    session.commit()
    return True


def list_vendors(session: Session) -> list[models.Vendor]:
    return session.scalars(select(models.Vendor).order_by(models.Vendor.name)).all()


def create_vendor(session: Session, payload: schemas.VendorCreate) -> models.Vendor:
    vendor = models.Vendor(**payload.model_dump())
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor


def update_vendor(
    session: Session, vendor_id: int, payload: schemas.VendorUpdate
) -> Optional[models.Vendor]:
    vendor = session.get(models.Vendor, vendor_id)
    if not vendor:
        return None
    for key, value in payload.model_dump().items():
        setattr(vendor, key, value)
    session.commit()
    session.refresh(vendor)
    return vendor


def delete_vendor(session: Session, vendor_id: int) -> bool:
    vendor = session.get(models.Vendor, vendor_id)
    if not vendor:
        return False
    session.delete(vendor)
    session.commit()
    return True


def list_expenses(session: Session) -> list[models.Expense]:
    query = (
        select(models.Expense)
        .options(selectinload(models.Expense.department), selectinload(models.Expense.vendor))
        .order_by(models.Expense.expense_date)
    )
    return session.scalars(query).all()


def create_expense(
    session: Session, payload: schemas.ExpenseCreate
) -> models.Expense:
    expense = models.Expense(**payload.model_dump())
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


def update_expense(
    session: Session, expense_id: int, payload: schemas.ExpenseUpdate
) -> Optional[models.Expense]:
    expense = session.get(models.Expense, expense_id)
    if not expense:
        return None
    for key, value in payload.model_dump().items():
        setattr(expense, key, value)
    session.commit()
    session.refresh(expense)
    return expense


def delete_expense(session: Session, expense_id: int) -> bool:
    expense = session.get(models.Expense, expense_id)
    if not expense:
        return False
    session.delete(expense)
    session.commit()
    return True


def list_payrolls(session: Session) -> list[models.Payroll]:
    query = (
        select(models.Payroll)
        .options(selectinload(models.Payroll.employee))
        .order_by(models.Payroll.period_end)
    )
    return session.scalars(query).all()


def create_payroll(
    session: Session, payload: schemas.PayrollCreate
) -> models.Payroll:
    payroll = models.Payroll(**payload.model_dump())
    session.add(payroll)
    session.commit()
    session.refresh(payroll)
    return payroll


def update_payroll(
    session: Session, payroll_id: int, payload: schemas.PayrollUpdate
) -> Optional[models.Payroll]:
    payroll = session.get(models.Payroll, payroll_id)
    if not payroll:
        return None
    for key, value in payload.model_dump().items():
        setattr(payroll, key, value)
    session.commit()
    session.refresh(payroll)
    return payroll


def delete_payroll(session: Session, payroll_id: int) -> bool:
    payroll = session.get(models.Payroll, payroll_id)
    if not payroll:
        return False
    session.delete(payroll)
    session.commit()
    return True


def expenses_report(
    session: Session,
    department_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    approved_only: bool = False,
) -> list[dict[str, Any]]:
    query = (
        select(
            models.Expense.id.label("expense_id"),
            models.Department.name.label("department"),
            models.Vendor.name.label("vendor"),
            models.Expense.amount,
            models.Expense.expense_date,
            models.Expense.is_approved,
        )
        .join(models.Department, models.Expense.department_id == models.Department.id)
        .join(models.Vendor, models.Expense.vendor_id == models.Vendor.id)
    )

    if department_id:
        query = query.where(models.Department.id == department_id)
    if vendor_id:
        query = query.where(models.Vendor.id == vendor_id)
    if date_from:
        query = query.where(models.Expense.expense_date >= date_from)
    if date_to:
        query = query.where(models.Expense.expense_date <= date_to)
    if approved_only:
        query = query.where(models.Expense.is_approved.is_(True))

    return session.execute(query.order_by(models.Expense.expense_date)).mappings().all()


def expenses_summary(
    session: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict[str, Any]]:
    query = (
        select(
            models.Department.name.label("department"),
            func.sum(models.Expense.amount).label("total_amount"),
        )
        .join(models.Expense, models.Department.id == models.Expense.department_id)
        .group_by(models.Department.name)
    )

    if date_from:
        query = query.where(models.Expense.expense_date >= date_from)
    if date_to:
        query = query.where(models.Expense.expense_date <= date_to)

    return session.execute(query.order_by(models.Department.name)).mappings().all()


def payrolls_report(
    session: Session,
    employee_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    paid_only: Optional[bool] = None,
    include_archived: bool = False,
) -> list[dict[str, Any]]:
    if not include_archived:
        query = (
            select(
                models.Payroll.id.label("payroll_id"),
                models.Employee.full_name.label("employee"),
                models.Payroll.period_start,
                models.Payroll.period_end,
                models.Payroll.net_amount,
                models.Payroll.paid_at,
                models.Payroll.is_paid,
            )
            .join(models.Employee, models.Payroll.employee_id == models.Employee.id)
        )

        if employee_id:
            query = query.where(models.Employee.id == employee_id)
        if date_from:
            query = query.where(models.Payroll.period_end >= date_from)
        if date_to:
            query = query.where(models.Payroll.period_end <= date_to)
        if paid_only is not None:
            query = query.where(models.Payroll.is_paid.is_(paid_only))

        return session.execute(query.order_by(models.Payroll.period_end)).mappings().all()

    sql = """
        SELECT
            p.id AS payroll_id,
            e.full_name AS employee,
            p.period_start,
            p.period_end,
            p.net_amount,
            p.paid_at,
            p.is_paid,
            p.archived_at
        FROM payrolls_all p
        JOIN employees e ON p.employee_id = e.id
        WHERE 1=1
    """
    params: dict[str, Any] = {}

    if employee_id:
        sql += " AND p.employee_id = :employee_id"
        params["employee_id"] = employee_id
    if date_from:
        sql += " AND p.period_end >= :date_from"
        params["date_from"] = date_from
    if date_to:
        sql += " AND p.period_end <= :date_to"
        params["date_to"] = date_to
    if paid_only is not None:
        sql += " AND p.is_paid = :paid_only"
        params["paid_only"] = paid_only

    sql += " ORDER BY p.period_end"

    return session.execute(text(sql), params).mappings().all()


def payrolls_summary(
    session: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict[str, Any]]:
    query = (
        select(
            models.Department.name.label("department"),
            func.sum(models.Payroll.net_amount).label("total_net"),
        )
        .join(models.Employee, models.Payroll.employee_id == models.Employee.id)
        .join(models.Department, models.Employee.department_id == models.Department.id)
        .group_by(models.Department.name)
    )

    if date_from:
        query = query.where(models.Payroll.period_end >= date_from)
    if date_to:
        query = query.where(models.Payroll.period_end <= date_to)

    return session.execute(query.order_by(models.Department.name)).mappings().all()


def run_archive(session: Session, cutoff_date: date) -> int:
    result = session.execute(
        text("SELECT archive_payrolls(:cutoff_date) AS moved"),
        {"cutoff_date": cutoff_date},
    ).mappings()
    session.commit()
    row = result.first()
    return int(row["moved"]) if row else 0
