"""Dev deploy: restart Odoo and update modules in estate-kit-dev compose."""

import subprocess
import sys
from pathlib import Path

COMPOSE_FILE = Path(__file__).resolve().parents[5] / "dev" / "docker-compose.yml"
SERVICE = "odoo"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def log(color: str, message: str) -> None:
    print(f"{color}{message}{NC}", flush=True)  # noqa: T201


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)  # noqa: S603


def main() -> None:
    compose = ["docker", "compose", "-f", str(COMPOSE_FILE)]

    log(YELLOW, "Restarting Odoo (addons mounted via volume)...")
    run([*compose, "restart", SERVICE])

    log(YELLOW, "Waiting for healthy status...")
    subprocess.run(  # noqa: S603
        [*compose, "exec", SERVICE, "curl", "-sf", "http://localhost:8069/web/health"],
        check=False,
    )

    log(YELLOW, "Checking logs...")
    subprocess.run([*compose, "logs", "--tail", "20", SERVICE], check=False)  # noqa: S603

    log(GREEN, "Dev deploy of Odoo completed! Addons are mounted read-only from ../odoo/addons")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log(RED, f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
