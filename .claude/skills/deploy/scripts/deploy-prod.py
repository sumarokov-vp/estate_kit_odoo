# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import yaml

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
DIM = "\033[2m"
RED = "\033[0;31m"
NC = "\033[0m"


def log(color: str, message: str) -> None:
    print(f"{color}{message}{NC}", flush=True)


@contextmanager
def timed(label: str):
    log(YELLOW, f"{label}...")
    start = time.monotonic()
    yield
    elapsed = time.monotonic() - start
    log(DIM, f"  ✓ {elapsed:.1f}s")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"→ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def ssh_cmd(ssh_alias: str, command: str) -> subprocess.CompletedProcess:
    return run(["ssh", ssh_alias, command])


def load_config() -> tuple[dict, dict]:
    config_path = Path(".claude/devops.yaml")
    if not config_path.exists():
        log(RED, f"Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    deploy = config.get("deploy")
    if not deploy:
        log(RED, "Missing 'deploy' section in devops.yaml")
        sys.exit(1)

    server_name = deploy["server"]
    servers = config.get("servers", {})
    server = servers.get(server_name)
    if not server:
        log(RED, f"Server '{server_name}' not found in servers")
        sys.exit(1)

    return deploy, server


def rsync_addons(ssh_alias: str, remote_dir: str) -> None:
    run([
        "rsync", "-az", "--delete",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "-e", "ssh",
        "addons/", f"{ssh_alias}:{remote_dir}/addons/",
    ])


def rsync_configs(ssh_alias: str, remote_dir: str) -> None:
    run([
        "rsync", "-az",
        "-e", "ssh",
        "docker/compose.yaml", "docker/Caddyfile",
        f"{ssh_alias}:{remote_dir}/",
    ])


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    os.chdir(repo_root)

    deploy, server = load_config()

    container = deploy["container"]
    db_name = deploy["db_name"]

    ssh_alias = server.get("ssh", deploy["server"])
    remote_dir = server["path"]

    if dry_run:
        print("[DRY RUN] Would execute the following steps:")
        print(f"  1. rsync addons + configs (parallel, containers still running)")
        print(f"  2. docker compose stop odoo")
        print(f"  3. docker compose run --rm odoo -u estate_kit -d {db_name}")
        print(f"  4. docker compose start odoo")
        return

    total_start = time.monotonic()

    # 1. Rsync addons and configs in parallel (containers still running, no downtime)
    with timed("Syncing addons and configs (parallel)"):
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(rsync_addons, ssh_alias, remote_dir)
            f2 = pool.submit(rsync_configs, ssh_alias, remote_dir)
            f1.result()
            f2.result()

    # 2. Stop only Odoo (keep network and other containers)
    with timed("Stopping Odoo"):
        ssh_cmd(ssh_alias,
                f"bash -c 'cd {remote_dir} && sudo docker compose stop odoo'")

    # 3. Update module (temporary container, credentials from .env via compose)
    with timed("Updating estate_kit module"):
        ssh_cmd(ssh_alias,
                f"bash -c 'cd {remote_dir} && sudo docker compose run --rm odoo odoo "
                f"-u estate_kit -d {db_name} --stop-after-init'")

    # 4. Start Odoo back
    with timed("Starting Odoo"):
        ssh_cmd(ssh_alias,
                f"bash -c 'cd {remote_dir} && sudo docker compose start odoo'")

    # 5. Check logs
    log(YELLOW, "Checking logs...")
    ssh_cmd(ssh_alias, f"sudo docker logs --tail 20 {container}")

    total = time.monotonic() - total_start
    log(GREEN, f"\nDeploy complete in {total:.1f}s! Site: https://royalestate.smartist.dev/")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log(RED, f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
