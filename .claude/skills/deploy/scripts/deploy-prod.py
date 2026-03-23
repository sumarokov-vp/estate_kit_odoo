# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///

import os
import subprocess
import sys
from pathlib import Path

import yaml


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"→ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


def ssh_cmd(ssh_alias: str, command: str) -> subprocess.CompletedProcess:
    return run(["ssh", ssh_alias, command])


def ssh_output(ssh_alias: str, command: str) -> str:
    result = subprocess.run(
        ["ssh", ssh_alias, command],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def load_config() -> tuple[dict, dict]:
    config_path = Path(".claude/devops.yaml")
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    deploy = config.get("deploy")
    if not deploy:
        print("Missing 'deploy' section in devops.yaml")
        sys.exit(1)

    server_name = deploy["server"]
    servers = config.get("servers", {})
    server = servers.get(server_name)
    if not server:
        print(f"Server '{server_name}' not found in servers")
        sys.exit(1)

    return deploy, server


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
        print(f"  1. docker compose down")
        print(f"  2. rsync addons to {ssh_alias}:{remote_dir}/addons/")
        print(f"  3. rsync docker configs to {ssh_alias}:{remote_dir}/")
        print(f"  4. Update module: odoo -u estate_kit -d {db_name}")
        print(f"  5. docker compose up -d")
        return

    # 1. Rsync addons
    print("Syncing addons to server...")
    run([
        "rsync", "-az", "--delete",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "-e", "ssh",
        "addons/", f"{ssh_alias}:{remote_dir}/addons/",
    ])

    # 2. Rsync docker configs (compose.yaml, Caddyfile)
    print("Syncing docker configs...")
    run([
        "rsync", "-az",
        "-e", "ssh",
        "docker/compose.yaml", "docker/Caddyfile",
        f"{ssh_alias}:{remote_dir}/",
    ])

    # 3. Fetch DB credentials from server
    print("Fetching DB credentials from server...")
    env_content = ssh_output(ssh_alias, f"sudo cat {remote_dir}/.env")
    env_vars = {}
    for line in env_content.splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()

    db_host = env_vars.get("DB_HOST", "")
    db_port = env_vars.get("DB_PORT", "5432")
    db_user = env_vars.get("DB_USER", "")
    db_password = env_vars.get("DB_PASSWORD", "")

    if not db_password:
        print("ERROR: Could not fetch DB_PASSWORD from server")
        sys.exit(1)

    print(f"DB connection: {db_user}@{db_host}:{db_port}/{db_name}")

    # 4. Stop containers
    print("Stopping containers...")
    ssh_cmd(ssh_alias,
            f"bash -c 'cd {remote_dir} && sudo docker compose down --remove-orphans'")

    # 5. Update module (run temporary container with new addons mounted)
    print("Updating estate_kit module...")
    ssh_cmd(ssh_alias,
            f"bash -c 'cd {remote_dir} && sudo docker compose run --rm odoo odoo "
            f"-u estate_kit -d {db_name} --stop-after-init'")

    # 6. Start containers
    print("Starting containers...")
    ssh_cmd(ssh_alias,
            f"bash -c 'cd {remote_dir} && sudo docker compose up -d'")

    # 7. Check logs
    print("Checking logs...")
    ssh_cmd(ssh_alias, f"sudo docker logs --tail 20 {container}")

    print("\nDeploy complete! Site: https://royalestate.smartist.dev/")


if __name__ == "__main__":
    main()
