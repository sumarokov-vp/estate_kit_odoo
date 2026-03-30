-- depends: 0004.mutual-money-fk-restrict

-- Currency
INSERT INTO currency (code, name, symbol)
VALUES ('KZT', 'Казахстанский тенге', '₸')
ON CONFLICT (code) DO NOTHING;

-- Invoice statuses
INSERT INTO invoice_status (name, submit) VALUES ('draft', false) ON CONFLICT (name) DO NOTHING;
INSERT INTO invoice_status (name, submit) VALUES ('sent', false) ON CONFLICT (name) DO NOTHING;
INSERT INTO invoice_status (name, submit) VALUES ('paid', true) ON CONFLICT (name) DO NOTHING;
INSERT INTO invoice_status (name, submit) VALUES ('cancelled', false) ON CONFLICT (name) DO NOTHING;

-- Money statuses
INSERT INTO money_status (name, submit) VALUES ('draft', false) ON CONFLICT (name) DO NOTHING;
INSERT INTO money_status (name, submit) VALUES ('submitted', true) ON CONFLICT (name) DO NOTHING;
INSERT INTO money_status (name, submit) VALUES ('cancelled', false) ON CONFLICT (name) DO NOTHING;

-- Money status transitions
INSERT INTO allowed_money_status_transitions (from_money_status_id, to_money_status_id)
SELECT f.id, t.id FROM money_status f, money_status t
WHERE f.name = 'draft' AND t.name = 'submitted'
ON CONFLICT DO NOTHING;

INSERT INTO allowed_money_status_transitions (from_money_status_id, to_money_status_id)
SELECT f.id, t.id FROM money_status f, money_status t
WHERE f.name = 'draft' AND t.name = 'cancelled'
ON CONFLICT DO NOTHING;

INSERT INTO allowed_money_status_transitions (from_money_status_id, to_money_status_id)
SELECT f.id, t.id FROM money_status f, money_status t
WHERE f.name = 'submitted' AND t.name = 'draft'
ON CONFLICT DO NOTHING;

INSERT INTO allowed_money_status_transitions (from_money_status_id, to_money_status_id)
SELECT f.id, t.id FROM money_status f, money_status t
WHERE f.name = 'cancelled' AND t.name = 'draft'
ON CONFLICT DO NOTHING;

-- Expense statuses
INSERT INTO expense_status (name, submit) VALUES ('draft', false) ON CONFLICT (name) DO NOTHING;
INSERT INTO expense_status (name, submit) VALUES ('submitted', true) ON CONFLICT (name) DO NOTHING;
INSERT INTO expense_status (name, submit) VALUES ('cancelled', false) ON CONFLICT (name) DO NOTHING;

-- Expense status transitions
INSERT INTO allowed_expense_status_transitions (from_expense_status_name, to_expense_status_name)
VALUES ('draft', 'submitted') ON CONFLICT DO NOTHING;
INSERT INTO allowed_expense_status_transitions (from_expense_status_name, to_expense_status_name)
VALUES ('draft', 'cancelled') ON CONFLICT DO NOTHING;
INSERT INTO allowed_expense_status_transitions (from_expense_status_name, to_expense_status_name)
VALUES ('submitted', 'draft') ON CONFLICT DO NOTHING;
INSERT INTO allowed_expense_status_transitions (from_expense_status_name, to_expense_status_name)
VALUES ('cancelled', 'draft') ON CONFLICT DO NOTHING;

-- Assets
INSERT INTO assets (name, symbol, description)
VALUES ('Расчётный счёт', 'BANK_ACCOUNT', 'Основной банковский счёт агентства')
ON CONFLICT (symbol) DO NOTHING;

-- Items
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('listing_agent', 'Агент продавца', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('buyer_agent', 'Агент покупателя', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('isa', 'ISA', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('team_lead', 'Тим-лид', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('coordinator', 'Координатор', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('legal', 'Юрист', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('referral', 'Реферал', true) ON CONFLICT DO NOTHING;
INSERT INTO item (name, description, salary_plan_applicable) VALUES ('mls_fee', 'Комиссия MLS', false) ON CONFLICT DO NOTHING;

-- MLS Party
INSERT INTO party (name, party_type)
SELECT 'MLS EstateKit', 'company'
WHERE NOT EXISTS (
    SELECT 1 FROM party WHERE name = 'MLS EstateKit' AND party_type = 'company'
);
