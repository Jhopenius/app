-- Schema for VSUET Accounting (PostgreSQL)

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    department_id INT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    full_name VARCHAR(200) NOT NULL,
    hire_date DATE NOT NULL,
    base_salary NUMERIC(12, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    inn VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    department_id INT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    vendor_id INT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    expense_date DATE NOT NULL,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS payrolls (
    id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    net_amount NUMERIC(12, 2) NOT NULL,
    paid_at TIMESTAMP,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS archive_log (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(50) NOT NULL,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

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
