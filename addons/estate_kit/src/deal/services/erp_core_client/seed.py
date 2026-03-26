import psycopg


def seed_initial_data(database_url: str) -> None:
    with psycopg.connect(database_url) as conn:
        _seed_currency(conn)
        _seed_invoice_statuses(conn)
        _seed_money_statuses(conn)
        _seed_expense_statuses(conn)
        _seed_assets(conn)
        _seed_items(conn)
        _seed_mls_party(conn)
        conn.commit()


def _seed_currency(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        INSERT INTO currency (code, name, symbol)
        VALUES ('KZT', 'Казахстанский тенге', '₸')
        ON CONFLICT (code) DO NOTHING
        """
    )


def _seed_invoice_statuses(conn: psycopg.Connection) -> None:
    statuses = [
        ("draft", False),
        ("sent", False),
        ("paid", True),
        ("cancelled", False),
    ]
    for name, submit in statuses:
        conn.execute(
            """
            INSERT INTO invoice_status (name, submit)
            VALUES (%(name)s, %(submit)s)
            ON CONFLICT (name) DO NOTHING
            """,
            {"name": name, "submit": submit},
        )


def _seed_money_statuses(conn: psycopg.Connection) -> None:
    statuses = [
        ("draft", False),
        ("submitted", True),
        ("cancelled", False),
    ]
    for name, submit in statuses:
        conn.execute(
            """
            INSERT INTO money_status (name, submit)
            VALUES (%(name)s, %(submit)s)
            ON CONFLICT (name) DO NOTHING
            """,
            {"name": name, "submit": submit},
        )
    _seed_money_transitions(conn)


def _seed_money_transitions(conn: psycopg.Connection) -> None:
    transitions = [
        ("draft", "submitted"),
        ("draft", "cancelled"),
        ("submitted", "draft"),
        ("cancelled", "draft"),
    ]
    for from_name, to_name in transitions:
        conn.execute(
            """
            INSERT INTO allowed_money_status_transitions (from_money_status_id, to_money_status_id)
            SELECT f.id, t.id
            FROM money_status f, money_status t
            WHERE f.name = %(from_name)s AND t.name = %(to_name)s
            ON CONFLICT DO NOTHING
            """,
            {"from_name": from_name, "to_name": to_name},
        )


def _seed_expense_statuses(conn: psycopg.Connection) -> None:
    statuses = [
        ("draft", False),
        ("submitted", True),
        ("cancelled", False),
    ]
    for name, submit in statuses:
        conn.execute(
            """
            INSERT INTO expense_status (name, submit)
            VALUES (%(name)s, %(submit)s)
            ON CONFLICT (name) DO NOTHING
            """,
            {"name": name, "submit": submit},
        )
    _seed_expense_transitions(conn)


def _seed_expense_transitions(conn: psycopg.Connection) -> None:
    transitions = [
        ("draft", "submitted"),
        ("draft", "cancelled"),
        ("submitted", "draft"),
        ("cancelled", "draft"),
    ]
    for from_name, to_name in transitions:
        conn.execute(
            """
            INSERT INTO allowed_expense_status_transitions (from_expense_status_name, to_expense_status_name)
            VALUES (%(from_name)s, %(to_name)s)
            ON CONFLICT DO NOTHING
            """,
            {"from_name": from_name, "to_name": to_name},
        )


def _seed_assets(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        INSERT INTO assets (name, symbol, description)
        VALUES ('Расчётный счёт', 'BANK_ACCOUNT', 'Основной банковский счёт агентства')
        ON CONFLICT (symbol) DO NOTHING
        """
    )


def _seed_items(conn: psycopg.Connection) -> None:
    items = [
        ("listing_agent", "Агент продавца", True),
        ("buyer_agent", "Агент покупателя", True),
        ("isa", "ISA", True),
        ("team_lead", "Тим-лид", True),
        ("coordinator", "Координатор", True),
        ("legal", "Юрист", True),
        ("referral", "Реферал", True),
        ("mls_fee", "Комиссия MLS", False),
    ]
    for name, description, salary_plan_applicable in items:
        conn.execute(
            """
            INSERT INTO item (name, description, salary_plan_applicable)
            VALUES (%(name)s, %(description)s, %(salary_plan_applicable)s)
            ON CONFLICT DO NOTHING
            """,
            {
                "name": name,
                "description": description,
                "salary_plan_applicable": salary_plan_applicable,
            },
        )


def _seed_mls_party(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        INSERT INTO party (name, party_type)
        SELECT 'MLS EstateKit', 'company'
        WHERE NOT EXISTS (
            SELECT 1 FROM party WHERE name = 'MLS EstateKit' AND party_type = 'company'
        )
        """
    )
