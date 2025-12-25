    from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from vsuet_accounting.infrastructure.db.models import (
    ArchiveLog,
    Base,
    Department,
    Employee,
    Expense,
    Payroll,
    Vendor,
)
from vsuet_accounting.infrastructure.db.session import SessionLocal

ARCHIVE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION archive_payrolls(cutoff_date date)
RETURNS integer AS $$
DECLARE
    moved_count integer;
BEGIN
    INSERT INTO archive_log (source_table, payload)
    SELECT 'payrolls', to_jsonb(p) FROM payrolls p
    WHERE p.period_end < cutoff_date;

    GET DIAGNOSTICS moved_count = ROW_COUNT;

    DELETE FROM payrolls WHERE period_end < cutoff_date;

    RETURN moved_count;
END;
$$ LANGUAGE plpgsql;
"""

ARCHIVE_VIEW_SQL = """
CREATE OR REPLACE VIEW payrolls_archive_view AS
SELECT
    (payload->>'id')::int AS id,
    (payload->>'employee_id')::int AS employee_id,
    (payload->>'period_start')::date AS period_start,
    (payload->>'period_end')::date AS period_end,
    (payload->>'net_amount')::numeric AS net_amount,
    (payload->>'paid_at')::timestamp AS paid_at,
    (payload->>'is_paid')::boolean AS is_paid,
    archived_at AS archived_at
FROM archive_log
WHERE source_table = 'payrolls';
"""

PAYROLLS_ALL_VIEW_SQL = """
CREATE OR REPLACE VIEW payrolls_all AS
SELECT
    id,
    employee_id,
    period_start,
    period_end,
    net_amount,
    paid_at,
    is_paid,
    NULL::timestamp AS archived_at
FROM payrolls
UNION ALL
SELECT
    id,
    employee_id,
    period_start,
    period_end,
    net_amount,
    paid_at,
    is_paid,
    archived_at
FROM payrolls_archive_view;
"""


def init_db(engine, seed: bool = True) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(ARCHIVE_FUNCTION_SQL))
        conn.execute(text(ARCHIVE_VIEW_SQL))
        conn.execute(text(PAYROLLS_ALL_VIEW_SQL))

    if seed:
        seed_data()


def database_is_empty(session: Session) -> bool:
    tables: Iterable[type[Base]] = (
        Department,
        Employee,
        Vendor,
        Expense,
        Payroll,
        ArchiveLog,
    )
    return all(
        session.scalar(select(func.count()).select_from(table)) == 0 for table in tables
    )


def seed_data(session: Optional[Session] = None) -> None:
    owns_session = session is None
    if session is None:
        session = SessionLocal()

    try:
        if not database_is_empty(session):
            return

        dept_accounting = Department(name="Бухгалтерия", code="БУХ")
        dept_finance = Department(name="Планово-финансовый отдел", code="ПФО")
        dept_procurement = Department(name="Отдел закупок и снабжения", code="ОЗС")
        dept_it = Department(name="ИТ-служба", code="ИТ")
        dept_food = Department(name="Кафедра пищевых технологий", code="КПТ")

        session.add_all(
            [dept_accounting, dept_finance, dept_procurement, dept_it, dept_food]
        )
        session.flush()

        employee_1 = Employee(
            department_id=dept_accounting.id,
            full_name="Петров Иван Сергеевич",
            hire_date=date(2021, 3, 15),
            base_salary=62000.00,
            is_active=True,
        )
        employee_2 = Employee(
            department_id=dept_accounting.id,
            full_name="Сидорова Елена Викторовна",
            hire_date=date(2020, 9, 1),
            base_salary=58000.00,
            is_active=True,
        )
        employee_3 = Employee(
            department_id=dept_finance.id,
            full_name="Смирнова Ольга Павловна",
            hire_date=date(2018, 6, 10),
            base_salary=64000.00,
            is_active=True,
        )
        employee_4 = Employee(
            department_id=dept_procurement.id,
            full_name="Лебедев Дмитрий Андреевич",
            hire_date=date(2019, 11, 5),
            base_salary=52000.00,
            is_active=True,
        )
        employee_5 = Employee(
            department_id=dept_it.id,
            full_name="Волкова Марина Алексеевна",
            hire_date=date(2022, 2, 14),
            base_salary=70000.00,
            is_active=True,
        )
        employee_6 = Employee(
            department_id=dept_food.id,
            full_name="Иванов Сергей Николаевич",
            hire_date=date(2019, 5, 20),
            base_salary=54000.00,
            is_active=True,
        )
        employee_7 = Employee(
            department_id=dept_food.id,
            full_name="Кузнецов Павел Олегович",
            hire_date=date(2023, 1, 20),
            base_salary=48000.00,
            is_active=False,
        )

        session.add_all(
            [
                employee_1,
                employee_2,
                employee_3,
                employee_4,
                employee_5,
                employee_6,
                employee_7,
            ]
        )
        session.flush()

        vendor_1 = Vendor(name="ООО \"ВГУИТ-Снабжение\"", inn="3661001111")
        vendor_2 = Vendor(name="ООО \"ТехСервис\"", inn="3661002222")
        vendor_3 = Vendor(name="ООО \"ОфисЛайн\"", inn="3661003333")
        vendor_4 = Vendor(name="АО \"ЭнергоВоронеж\"", inn="3661004444")
        vendor_5 = Vendor(name="ООО \"ЛабХим Трейд\"", inn="3661005555")

        session.add_all([vendor_1, vendor_2, vendor_3, vendor_4, vendor_5])
        session.flush()

        expenses = [
            Expense(
                department_id=dept_accounting.id,
                vendor_id=vendor_3.id,
                amount=4500.00,
                expense_date=date(2024, 1, 15),
                is_approved=True,
            ),
            Expense(
                department_id=dept_accounting.id,
                vendor_id=vendor_1.id,
                amount=12000.50,
                expense_date=date(2024, 2, 12),
                is_approved=True,
            ),
            Expense(
                department_id=dept_finance.id,
                vendor_id=vendor_2.id,
                amount=9800.00,
                expense_date=date(2024, 2, 20),
                is_approved=True,
            ),
            Expense(
                department_id=dept_procurement.id,
                vendor_id=vendor_1.id,
                amount=15200.00,
                expense_date=date(2024, 3, 1),
                is_approved=False,
            ),
            Expense(
                department_id=dept_it.id,
                vendor_id=vendor_2.id,
                amount=56000.00,
                expense_date=date(2024, 3, 12),
                is_approved=True,
            ),
            Expense(
                department_id=dept_food.id,
                vendor_id=vendor_5.id,
                amount=22000.00,
                expense_date=date(2024, 1, 28),
                is_approved=True,
            ),
            Expense(
                department_id=dept_food.id,
                vendor_id=vendor_4.id,
                amount=13500.00,
                expense_date=date(2024, 3, 5),
                is_approved=False,
            ),
            Expense(
                department_id=dept_finance.id,
                vendor_id=vendor_3.id,
                amount=3100.00,
                expense_date=date(2024, 2, 5),
                is_approved=True,
            ),
        ]

        session.add_all(expenses)

        payrolls = [
            Payroll(
                employee_id=employee_1.id,
                period_start=date(2023, 12, 1),
                period_end=date(2023, 12, 31),
                net_amount=51000.00,
                paid_at=datetime(2024, 1, 10, 10, 0, 0),
                is_paid=True,
            ),
            Payroll(
                employee_id=employee_2.id,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                net_amount=49000.00,
                paid_at=datetime(2024, 2, 10, 10, 0, 0),
                is_paid=True,
            ),
            Payroll(
                employee_id=employee_3.id,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                net_amount=54500.00,
                paid_at=datetime(2024, 2, 12, 10, 0, 0),
                is_paid=True,
            ),
            Payroll(
                employee_id=employee_4.id,
                period_start=date(2024, 2, 1),
                period_end=date(2024, 2, 29),
                net_amount=47000.00,
                paid_at=None,
                is_paid=False,
            ),
            Payroll(
                employee_id=employee_5.id,
                period_start=date(2024, 2, 1),
                period_end=date(2024, 2, 29),
                net_amount=62000.00,
                paid_at=datetime(2024, 3, 10, 10, 0, 0),
                is_paid=True,
            ),
            Payroll(
                employee_id=employee_6.id,
                period_start=date(2024, 2, 1),
                period_end=date(2024, 2, 29),
                net_amount=46000.00,
                paid_at=None,
                is_paid=False,
            ),
            Payroll(
                employee_id=employee_7.id,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 1, 31),
                net_amount=42000.00,
                paid_at=datetime(2024, 2, 5, 10, 0, 0),
                is_paid=True,
            ),
        ]

        session.add_all(payrolls)

        archive_1 = ArchiveLog(
            source_table="payrolls",
            payload={
                "id": 9001,
                "employee_id": employee_1.id,
                "period_start": "2023-09-01",
                "period_end": "2023-09-30",
                "net_amount": 50500.00,
                "paid_at": "2023-10-10T10:00:00",
                "is_paid": True,
            },
        )
        archive_2 = ArchiveLog(
            source_table="payrolls",
            payload={
                "id": 9002,
                "employee_id": employee_2.id,
                "period_start": "2023-10-01",
                "period_end": "2023-10-31",
                "net_amount": 48200.00,
                "paid_at": "2023-11-10T10:00:00",
                "is_paid": True,
            },
        )

        session.add_all([archive_1, archive_2])

        session.commit()
    finally:
        if owns_session:
            session.close()
