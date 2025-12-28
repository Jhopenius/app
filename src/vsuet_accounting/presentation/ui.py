from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import subprocess

import pandas as pd
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from vsuet_accounting.application import services
from vsuet_accounting.domain import schemas
from vsuet_accounting.config import get_settings
from vsuet_accounting.infrastructure import backup as backup_ops
from vsuet_accounting.infrastructure.db.init_db import init_db
from vsuet_accounting.infrastructure.db.session import SessionLocal, get_engine


@st.cache_resource
def initialize_db() -> None:
    engine = get_engine()
    init_db(engine)


def run_app() -> None:
    st.set_page_config(page_title="Бухгалтерия ВГУИТ", layout="wide")
    initialize_db()

    st.sidebar.title("Бухгалтерия ВГУИТ")
    page = st.sidebar.radio(
        "Навигация",
        ["Обзор", "Справочники", "Операции", "Отчеты", "Сервис"],
    )

    if page == "Обзор":
        render_overview()
    elif page == "Справочники":
        render_reference_data()
    elif page == "Операции":
        render_operations()
    elif page == "Отчеты":
        render_reports()
    else:
        render_service()


def render_overview() -> None:
    st.title("Бухгалтерия ВГУИТ")
    st.write(
        "Учетная система университета: подразделения, сотрудники, расходы и выплаты."
    )

    with SessionLocal() as session:
        dept_count = len(services.list_departments(session))
        emp_count = len(services.list_employees(session))
        exp_count = len(services.list_expenses(session))
        payroll_count = len(services.list_payrolls(session))

    cols = st.columns(4)
    cols[0].metric("Подразделения", dept_count)
    cols[1].metric("Сотрудники", emp_count)
    cols[2].metric("Расходы", exp_count)
    cols[3].metric("Выплаты", payroll_count)


def render_reference_data() -> None:
    st.header("Справочники")
    tabs = st.tabs(["Подразделения", "Сотрудники", "Поставщики"])

    with tabs[0]:
        render_departments()
    with tabs[1]:
        render_employees()
    with tabs[2]:
        render_vendors()


def render_departments() -> None:
    st.subheader("Подразделения")
    with SessionLocal() as session:
        departments = services.list_departments(session)

    with st.form("add_department", clear_on_submit=True):
        name = st.text_input("Название подразделения")
        code = st.text_input("Код")
        submitted = st.form_submit_button("Добавить подразделение")
        if submitted:
            if not name or not code:
                st.warning("Заполните все поля.")
            else:
                with SessionLocal() as session:
                    services.create_department(
                        session,
                        payload=schemas.DepartmentCreate(name=name, code=code),
                    )
                st.success("Подразделение добавлено.")

    if departments:
        st.dataframe(
            pd.DataFrame(
                [
                    {"id": d.id, "name": d.name, "code": d.code}
                    for d in departments
                ]
            ),
            width="stretch",
        )

        selected = st.selectbox(
            "Выберите подразделение",
            departments,
            format_func=lambda d: f"{d.name} ({d.code})",
        )
        name = st.text_input(
            "Название", value=selected.name, key=f"dept_name_{selected.id}"
        )
        code = st.text_input("Код", value=selected.code, key=f"dept_code_{selected.id}")
        col1, col2 = st.columns(2)
        if col1.button("Обновить", key=f"update_dept_{selected.id}"):
            with SessionLocal() as session:
                services.update_department(
                    session,
                    selected.id,
                    schemas.DepartmentUpdate(name=name, code=code),
                )
            st.success("Подразделение обновлено.")
        if col2.button("Удалить", key=f"delete_dept_{selected.id}"):
            with SessionLocal() as session:
                services.delete_department(session, selected.id)
            st.success("Подразделение удалено.")
    else:
        st.info("Пока нет подразделений.")


def render_employees() -> None:
    st.subheader("Сотрудники")
    with SessionLocal() as session:
        employees = services.list_employees(session)
        departments = services.list_departments(session)

    if not departments:
        st.warning("Сначала добавьте подразделения.")
        return

    dept_options = {dept.name: dept.id for dept in departments}

    with st.form("add_employee", clear_on_submit=True):
        full_name = st.text_input("ФИО")
        hire_date = st.date_input("Дата приема", value=date.today())
        base_salary = st.number_input("Оклад", min_value=0.0, step=1000.0)
        is_active = st.checkbox("Активен", value=True)
        dept_name = st.selectbox("Подразделение", list(dept_options.keys()))
        submitted = st.form_submit_button("Добавить сотрудника")
        if submitted:
            payload = schemas.EmployeeCreate(
                department_id=dept_options[dept_name],
                full_name=full_name,
                hire_date=hire_date,
                base_salary=base_salary,
                is_active=is_active,
            )
            with SessionLocal() as session:
                services.create_employee(session, payload)
            st.success("Сотрудник добавлен.")

    if employees:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "id": e.id,
                        "full_name": e.full_name,
                        "department": e.department.name,
                        "hire_date": e.hire_date,
                        "base_salary": float(e.base_salary),
                        "is_active": e.is_active,
                    }
                    for e in employees
                ]
            ),
            width="stretch",
        )

        selected = st.selectbox(
            "Выберите сотрудника",
            employees,
            format_func=lambda e: f"{e.full_name} ({e.department.name})",
        )
        full_name = st.text_input(
            "ФИО", value=selected.full_name, key=f"emp_name_{selected.id}"
        )
        hire_date = st.date_input(
            "Дата приема", value=selected.hire_date, key=f"emp_hire_{selected.id}"
        )
        base_salary = st.number_input(
            "Оклад",
            min_value=0.0,
            step=1000.0,
            value=float(selected.base_salary),
            key=f"emp_salary_{selected.id}",
        )
        is_active = st.checkbox(
            "Активен", value=selected.is_active, key=f"emp_active_{selected.id}"
        )
        dept_name = st.selectbox(
            "Подразделение",
            list(dept_options.keys()),
            index=list(dept_options.values()).index(selected.department_id),
            key=f"emp_dept_{selected.id}",
        )
        col1, col2 = st.columns(2)
        if col1.button("Обновить", key=f"update_emp_{selected.id}"):
            payload = schemas.EmployeeUpdate(
                department_id=dept_options[dept_name],
                full_name=full_name,
                hire_date=hire_date,
                base_salary=base_salary,
                is_active=is_active,
            )
            with SessionLocal() as session:
                services.update_employee(session, selected.id, payload)
            st.success("Сотрудник обновлен.")
        if col2.button("Удалить", key=f"delete_emp_{selected.id}"):
            with SessionLocal() as session:
                services.delete_employee(session, selected.id)
            st.success("Сотрудник удален.")
    else:
        st.info("Пока нет сотрудников.")


def render_vendors() -> None:
    st.subheader("Поставщики")
    with SessionLocal() as session:
        vendors = services.list_vendors(session)

    with st.form("add_vendor", clear_on_submit=True):
        name = st.text_input("Название поставщика")
        inn = st.text_input("ИНН")
        submitted = st.form_submit_button("Добавить поставщика")
        if submitted:
            payload = schemas.VendorCreate(name=name, inn=inn)
            with SessionLocal() as session:
                services.create_vendor(session, payload)
            st.success("Поставщик добавлен.")

    if vendors:
        st.dataframe(
            pd.DataFrame(
                [{"id": v.id, "name": v.name, "inn": v.inn} for v in vendors]
            ),
            width="stretch",
        )

        selected = st.selectbox(
            "Выберите поставщика",
            vendors,
            format_func=lambda v: f"{v.name} ({v.inn})",
        )
        name = st.text_input(
            "Название", value=selected.name, key=f"vendor_name_{selected.id}"
        )
        inn = st.text_input("ИНН", value=selected.inn, key=f"vendor_inn_{selected.id}")
        col1, col2 = st.columns(2)
        if col1.button("Обновить", key=f"update_vendor_{selected.id}"):
            payload = schemas.VendorUpdate(name=name, inn=inn)
            with SessionLocal() as session:
                services.update_vendor(session, selected.id, payload)
            st.success("Поставщик обновлен.")
        if col2.button("Удалить", key=f"delete_vendor_{selected.id}"):
            with SessionLocal() as session:
                services.delete_vendor(session, selected.id)
            st.success("Поставщик удален.")
    else:
        st.info("Пока нет поставщиков.")


def render_operations() -> None:
    st.header("Операции")
    tabs = st.tabs(["Расходы", "Выплаты"])

    with tabs[0]:
        render_expenses()
    with tabs[1]:
        render_payrolls()


def render_expenses() -> None:
    st.subheader("Расходы")
    with SessionLocal() as session:
        expenses = services.list_expenses(session)
        departments = services.list_departments(session)
        vendors = services.list_vendors(session)

    if not departments or not vendors:
        st.warning("Сначала добавьте подразделения и поставщиков.")
        return

    dept_options = {dept.name: dept.id for dept in departments}
    vendor_options = {vendor.name: vendor.id for vendor in vendors}

    with st.form("add_expense", clear_on_submit=True):
        department_name = st.selectbox("Подразделение", list(dept_options.keys()))
        vendor_name = st.selectbox("Поставщик", list(vendor_options.keys()))
        amount = st.number_input("Сумма", min_value=0.0, step=500.0)
        expense_date = st.date_input("Дата расхода", value=date.today())
        is_approved = st.checkbox("Утверждено", value=False)
        submitted = st.form_submit_button("Добавить расход")
        if submitted:
            payload = schemas.ExpenseCreate(
                department_id=dept_options[department_name],
                vendor_id=vendor_options[vendor_name],
                amount=amount,
                expense_date=expense_date,
                is_approved=is_approved,
            )
            with SessionLocal() as session:
                services.create_expense(session, payload)
            st.success("Расход добавлен.")

    if expenses:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "id": e.id,
                        "department": e.department.name,
                        "vendor": e.vendor.name,
                        "amount": float(e.amount),
                        "expense_date": e.expense_date,
                        "is_approved": e.is_approved,
                    }
                    for e in expenses
                ]
            ),
            width="stretch",
        )

        selected = st.selectbox(
            "Выберите расход",
            expenses,
            format_func=lambda e: f"№{e.id} {e.department.name} {e.amount}",
        )
        department_name = st.selectbox(
            "Подразделение",
            list(dept_options.keys()),
            index=list(dept_options.values()).index(selected.department_id),
            key=f"expense_dept_{selected.id}",
        )
        vendor_name = st.selectbox(
            "Поставщик",
            list(vendor_options.keys()),
            index=list(vendor_options.values()).index(selected.vendor_id),
            key=f"expense_vendor_{selected.id}",
        )
        amount = st.number_input(
            "Сумма",
            min_value=0.0,
            step=500.0,
            value=float(selected.amount),
            key=f"expense_amount_{selected.id}",
        )
        expense_date = st.date_input(
            "Дата расхода",
            value=selected.expense_date,
            key=f"expense_date_{selected.id}",
        )
        is_approved = st.checkbox(
            "Утверждено",
            value=selected.is_approved,
            key=f"expense_approved_{selected.id}",
        )
        col1, col2 = st.columns(2)
        if col1.button("Обновить", key=f"update_expense_{selected.id}"):
            payload = schemas.ExpenseUpdate(
                department_id=dept_options[department_name],
                vendor_id=vendor_options[vendor_name],
                amount=amount,
                expense_date=expense_date,
                is_approved=is_approved,
            )
            with SessionLocal() as session:
                services.update_expense(session, selected.id, payload)
            st.success("Расход обновлен.")
        if col2.button("Удалить", key=f"delete_expense_{selected.id}"):
            with SessionLocal() as session:
                services.delete_expense(session, selected.id)
            st.success("Расход удален.")
    else:
        st.info("Пока нет расходов.")


def render_payrolls() -> None:
    st.subheader("Выплаты")
    with SessionLocal() as session:
        payrolls = services.list_payrolls(session)
        employees = services.list_employees(session)

    if not employees:
        st.warning("Сначала добавьте сотрудников.")
        return

    employee_options = {emp.full_name: emp.id for emp in employees}

    with st.form("add_payroll", clear_on_submit=True):
        employee_name = st.selectbox("Сотрудник", list(employee_options.keys()))
        period_start = st.date_input("Период с", value=date.today().replace(day=1))
        period_end = st.date_input("Период по", value=date.today())
        net_amount = st.number_input("Сумма к выплате", min_value=0.0, step=1000.0)
        is_paid = st.checkbox("Оплачено", value=False)
        paid_at = (
            st.date_input("Дата выплаты", value=date.today()) if is_paid else None
        )
        submitted = st.form_submit_button("Добавить выплату")
        if submitted:
            payload = schemas.PayrollCreate(
                employee_id=employee_options[employee_name],
                period_start=period_start,
                period_end=period_end,
                net_amount=net_amount,
                paid_at=datetime.combine(paid_at, datetime.min.time())
                if paid_at
                else None,
                is_paid=is_paid,
            )
            with SessionLocal() as session:
                services.create_payroll(session, payload)
            st.success("Выплата добавлена.")

    if payrolls:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "id": p.id,
                        "employee": p.employee.full_name,
                        "period_start": p.period_start,
                        "period_end": p.period_end,
                        "net_amount": float(p.net_amount),
                        "paid_at": p.paid_at,
                        "is_paid": p.is_paid,
                    }
                    for p in payrolls
                ]
            ),
            width="stretch",
        )

        selected = st.selectbox(
            "Выберите выплату",
            payrolls,
            format_func=lambda p: f"№{p.id} {p.employee.full_name}",
        )
        employee_name = st.selectbox(
            "Сотрудник",
            list(employee_options.keys()),
            index=list(employee_options.values()).index(selected.employee_id),
            key=f"payroll_emp_{selected.id}",
        )
        period_start = st.date_input(
            "Период с",
            value=selected.period_start,
            key=f"payroll_start_{selected.id}",
        )
        period_end = st.date_input(
            "Период по",
            value=selected.period_end,
            key=f"payroll_end_{selected.id}",
        )
        net_amount = st.number_input(
            "Сумма к выплате",
            min_value=0.0,
            step=1000.0,
            value=float(selected.net_amount),
            key=f"payroll_amount_{selected.id}",
        )
        is_paid = st.checkbox(
            "Оплачено", value=selected.is_paid, key=f"payroll_paid_{selected.id}"
        )
        paid_at = (
            st.date_input(
                "Дата выплаты",
                value=selected.paid_at.date() if selected.paid_at else date.today(),
                key=f"payroll_paid_at_{selected.id}",
            )
            if is_paid
            else None
        )
        col1, col2 = st.columns(2)
        if col1.button("Обновить", key=f"update_payroll_{selected.id}"):
            payload = schemas.PayrollUpdate(
                employee_id=employee_options[employee_name],
                period_start=period_start,
                period_end=period_end,
                net_amount=net_amount,
                paid_at=datetime.combine(paid_at, datetime.min.time())
                if paid_at
                else None,
                is_paid=is_paid,
            )
            with SessionLocal() as session:
                services.update_payroll(session, selected.id, payload)
            st.success("Выплата обновлена.")
        if col2.button("Удалить", key=f"delete_payroll_{selected.id}"):
            with SessionLocal() as session:
                services.delete_payroll(session, selected.id)
            st.success("Выплата удалена.")
    else:
        st.info("Пока нет выплат.")


def render_reports() -> None:
    st.header("Отчеты")

    with SessionLocal() as session:
        departments = services.list_departments(session)
        vendors = services.list_vendors(session)
        employees = services.list_employees(session)

    report_type = st.selectbox(
        "Тип отчета",
        ["Отчет по расходам", "Сводка расходов", "Отчет по выплатам", "Сводка выплат"],
    )

    if report_type in {"Отчет по расходам", "Сводка расходов"}:
        dept_map = {"Все": None}
        dept_map.update({dept.name: dept.id for dept in departments})
        vendor_map = {"Все": None}
        vendor_map.update({vendor.name: vendor.id for vendor in vendors})

        department_choice = st.selectbox("Подразделение", list(dept_map.keys()))
        vendor_choice = st.selectbox("Поставщик", list(vendor_map.keys()))
        date_from = st.date_input("Дата с", value=date(2024, 1, 1))
        date_to = st.date_input("Дата по", value=date.today())
        approved_only = st.checkbox("Только утвержденные", value=False)

        with SessionLocal() as session:
            if report_type == "Отчет по расходам":
                rows = services.expenses_report(
                    session,
                    department_id=dept_map[department_choice],
                    vendor_id=vendor_map[vendor_choice],
                    date_from=date_from,
                    date_to=date_to,
                    approved_only=approved_only,
                )
            else:
                rows = services.expenses_summary(
                    session,
                    date_from=date_from,
                    date_to=date_to,
                )

        df = pd.DataFrame(rows)

    else:
        emp_map = {"Все": None}
        emp_map.update({emp.full_name: emp.id for emp in employees})
        employee_choice = st.selectbox("Сотрудник", list(emp_map.keys()))
        date_from = st.date_input("Период с", value=date(2024, 1, 1))
        date_to = st.date_input("Период по", value=date.today())
        paid_filter = st.selectbox("Статус оплаты", ["Все", "Оплачено", "Не оплачено"])
        include_archived = st.checkbox("Включать архив", value=False)

        paid_only = None
        if paid_filter == "Оплачено":
            paid_only = True
        elif paid_filter == "Не оплачено":
            paid_only = False

        with SessionLocal() as session:
            if report_type == "Отчет по выплатам":
                rows = services.payrolls_report(
                    session,
                    employee_id=emp_map[employee_choice],
                    date_from=date_from,
                    date_to=date_to,
                    paid_only=paid_only,
                    include_archived=include_archived,
                )
            else:
                rows = services.payrolls_summary(
                    session,
                    date_from=date_from,
                    date_to=date_to,
                )

        df = pd.DataFrame(rows)

    if df.empty:
        st.info("Нет данных для выбранных фильтров.")
        return

    st.dataframe(df, width="stretch")

    csv = df.to_csv(index=False).encode("utf-8")
    file_name_map = {
        "Отчет по расходам": "otchet_rashody.csv",
        "Сводка расходов": "svodka_rashody.csv",
        "Отчет по выплатам": "otchet_vyplaty.csv",
        "Сводка выплат": "svodka_vyplaty.csv",
    }
    st.download_button(
        "Скачать CSV",
        csv,
        file_name=file_name_map[report_type],
        mime="text/csv",
    )


def render_service() -> None:
    st.header("Сервис")
    settings = get_settings()

    st.subheader("Резервное копирование")
    backup_name = f"backup_{datetime.now():%Y%m%d_%H%M%S}.sql"
    backup_path = str(Path(settings.backup_dir) / backup_name)
    if st.button("Создать бэкап"):
        try:
            backup_ops.backup_database(backup_path)
            st.success(f"Бэкап создан: {backup_path}")
        except (subprocess.CalledProcessError, FileNotFoundError, SQLAlchemyError) as exc:
            st.error(f"Ошибка бэкапа: {exc}")

    st.subheader("Восстановление")
    uploaded = st.file_uploader("Загрузите .sql бэкап", type=["sql"])
    if st.button("Восстановить из файла"):
        if not uploaded:
            st.warning("Сначала загрузите файл бэкапа.")
        else:
            restore_path = Path(settings.backup_dir) / f"restore_{uploaded.name}"
            restore_path.parent.mkdir(parents=True, exist_ok=True)
            restore_path.write_bytes(uploaded.getbuffer())
            try:
                backup_ops.restore_database(str(restore_path))
                st.success("База данных восстановлена.")
            except (subprocess.CalledProcessError, FileNotFoundError, SQLAlchemyError) as exc:
                st.error(f"Ошибка восстановления: {exc}")

    st.subheader("Архивация выплат")
    cutoff_date = st.date_input("Архивировать выплаты до", value=date(2024, 2, 1))
    if st.button("Запустить архивацию"):
        try:
            with SessionLocal() as session:
                moved = services.run_archive(session, cutoff_date)
            st.success(f"Архивировано выплат: {moved}")
        except SQLAlchemyError as exc:
            st.error(f"Ошибка архивации: {exc}")
