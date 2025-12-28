-- Тестовые данные для БД "Бухгалтерия ВГУИТ"

INSERT INTO departments (id, name, code)
VALUES
    (1, 'Бухгалтерия', 'БУХ'),
    (2, 'Планово-финансовый отдел', 'ПФО'),
    (3, 'Отдел закупок и снабжения', 'ОЗС'),
    (4, 'ИТ-служба', 'ИТ'),
    (5, 'Кафедра пищевых технологий', 'КПТ');

INSERT INTO employees (id, department_id, full_name, hire_date, base_salary, is_active)
VALUES
    (1, 1, 'Петров Иван Сергеевич', '2021-03-15', 62000.00, TRUE),
    (2, 1, 'Сидорова Елена Викторовна', '2020-09-01', 58000.00, TRUE),
    (3, 2, 'Смирнова Ольга Павловна', '2018-06-10', 64000.00, TRUE),
    (4, 3, 'Лебедев Дмитрий Андреевич', '2019-11-05', 52000.00, TRUE),
    (5, 4, 'Волкова Марина Алексеевна', '2022-02-14', 70000.00, TRUE),
    (6, 5, 'Иванов Сергей Николаевич', '2019-05-20', 54000.00, TRUE),
    (7, 5, 'Кузнецов Павел Олегович', '2023-01-20', 48000.00, FALSE);

INSERT INTO vendors (id, name, inn)
VALUES
    (1, 'ООО "ВГУИТ-Снабжение"', '3661001111'),
    (2, 'ООО "ТехСервис"', '3661002222'),
    (3, 'ООО "ОфисЛайн"', '3661003333'),
    (4, 'АО "ЭнергоВоронеж"', '3661004444'),
    (5, 'ООО "ЛабХим Трейд"', '3661005555');

INSERT INTO expenses (id, department_id, vendor_id, amount, expense_date, is_approved)
VALUES
    (1, 1, 3, 4500.00, '2024-01-15', TRUE),
    (2, 1, 1, 12000.50, '2024-02-12', TRUE),
    (3, 2, 2, 9800.00, '2024-02-20', TRUE),
    (4, 3, 1, 15200.00, '2024-03-01', FALSE),
    (5, 4, 2, 56000.00, '2024-03-12', TRUE),
    (6, 5, 5, 22000.00, '2024-01-28', TRUE),
    (7, 5, 4, 13500.00, '2024-03-05', FALSE),
    (8, 2, 3, 3100.00, '2024-02-05', TRUE);

INSERT INTO payrolls (id, employee_id, period_start, period_end, net_amount, paid_at, is_paid)
VALUES
    (1, 1, '2023-12-01', '2023-12-31', 51000.00, '2024-01-10 10:00:00', TRUE),
    (2, 2, '2024-01-01', '2024-01-31', 49000.00, '2024-02-10 10:00:00', TRUE),
    (3, 3, '2024-01-01', '2024-01-31', 54500.00, '2024-02-12 10:00:00', TRUE),
    (4, 4, '2024-02-01', '2024-02-29', 47000.00, NULL, FALSE),
    (5, 5, '2024-02-01', '2024-02-29', 62000.00, '2024-03-10 10:00:00', TRUE),
    (6, 6, '2024-02-01', '2024-02-29', 46000.00, NULL, FALSE),
    (7, 7, '2024-01-01', '2024-01-31', 42000.00, '2024-02-05 10:00:00', TRUE);

INSERT INTO archive_log (id, source_table, payload)
VALUES
    (
        1,
        'payrolls',
        '{"id": 9001, "employee_id": 1, "period_start": "2023-09-01", "period_end": "2023-09-30", "net_amount": 50500.00, "paid_at": "2023-10-10T10:00:00", "is_paid": true}'
    ),
    (
        2,
        'payrolls',
        '{"id": 9002, "employee_id": 2, "period_start": "2023-10-01", "period_end": "2023-10-31", "net_amount": 48200.00, "paid_at": "2023-11-10T10:00:00", "is_paid": true}'
    );

SELECT setval('departments_id_seq', 5, true);
SELECT setval('employees_id_seq', 7, true);
SELECT setval('vendors_id_seq', 5, true);
SELECT setval('expenses_id_seq', 8, true);
SELECT setval('payrolls_id_seq', 7, true);
SELECT setval('archive_log_id_seq', 2, true);
