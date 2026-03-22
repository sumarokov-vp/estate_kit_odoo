"""Dev deploy: restart Odoo and update estate_kit module in estate-kit-dev compose."""

import subprocess
import sys
import time
from pathlib import Path

COMPOSE_FILE = Path(__file__).resolve().parents[5] / "dev" / "docker-compose.yml"
SERVICE = "odoo"
DB_NAME = "estate_kit_dev_odoo"
MODULE = "estate_kit"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def log(color: str, message: str) -> None:
    print(f"{color}{message}{NC}", flush=True)  # noqa: T201


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)  # noqa: S603


def wait_healthy(compose: list[str], timeout: int = 60) -> None:
    """Wait for Odoo to become healthy."""
    for _ in range(timeout):
        result = subprocess.run(  # noqa: S603
            [*compose, "exec", SERVICE, "curl", "-sf", "http://localhost:8069/web/health"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    log(RED, f"Odoo did not become healthy within {timeout}s")
    sys.exit(1)


def main() -> None:
    compose = ["docker", "compose", "-f", str(COMPOSE_FILE)]

    # 1. Restart to pick up new addon files from volume
    log(YELLOW, "Restarting Odoo (addons mounted via volume)...")
    run([*compose, "restart", SERVICE])

    # 2. Wait for healthy
    log(YELLOW, "Waiting for healthy status...")
    wait_healthy(compose)

    # 3. Stop Odoo before module update (port conflict with --stop-after-init)
    log(YELLOW, "Stopping Odoo for module update...")
    run([*compose, "stop", SERVICE])

    # 4. Update module via `run` (inherits env vars from compose)
    log(YELLOW, f"Updating module {MODULE}...")
    run([
        *compose, "run", "--rm", SERVICE,
        "odoo",
        f"--db-filter=^{DB_NAME}$",
        "-d", DB_NAME,
        "-u", MODULE,
        "--stop-after-init",
    ])

    # 5. Start Odoo back
    log(YELLOW, "Starting Odoo...")
    run([*compose, "start", SERVICE])

    # 5. Final health check
    log(YELLOW, "Final health check...")
    wait_healthy(compose)

    log(YELLOW, "Checking logs...")
    subprocess.run([*compose, "logs", "--tail", "20", SERVICE], check=False)  # noqa: S603

    log(GREEN, "Dev deploy complete! Module updated and Odoo restarted.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log(RED, f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
