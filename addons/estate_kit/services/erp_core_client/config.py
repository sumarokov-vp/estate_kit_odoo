import os


def get_database_url() -> str:
    host = os.environ["ERP_CORE_DB_HOST"]
    port = os.environ.get("ERP_CORE_DB_PORT", "5432")
    user = os.environ["ERP_CORE_DB_USER"]
    password = os.environ["ERP_CORE_DB_PASSWORD"]
    name = os.environ.get("ERP_CORE_DB_NAME", "estate_kit_erp")
    return f"postgres://{user}:{password}@{host}:{port}/{name}?sslmode=disable"
